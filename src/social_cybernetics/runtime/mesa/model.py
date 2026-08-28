"""Thin Mesa orchestration whose step method mirrors the ODD+D schedule."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

import numpy as np
from mesa import Model
from mesa.discrete_space import OrthogonalVonNeumannGrid
from numpy.typing import NDArray

from social_cybernetics.config import SimulationConfig
from social_cybernetics.domain import (
    AgentSnapshot,
    AgentState,
    CohortRecord,
    EventRecord,
    ModelRecord,
    allow_all,
    apply_metabolism,
    copy_observation,
    direct_observation,
    literal_local_policy,
    regenerate,
    resolve_actions,
)
from social_cybernetics.domain.ecology import validate_resource_arrays
from social_cybernetics.metrics import gini

from .agent import ForagerAgent

type FloatArray = NDArray[np.float64]

STAGE_ORDER = (
    "regeneration",
    "shock",
    "observation",
    "belief_update",
    "intent_selection",
    "institutional_gate",
    "physical_resolution",
    "metabolism",
    "mortality",
    "measurement",
)


class SugarscapeModel(Model):
    """Deterministic material baseline hosted by Mesa discrete space."""

    def __init__(self, config: SimulationConfig) -> None:
        super().__init__(seed=config.seed)
        self.config = config
        self.completed_ticks = 0
        self.stage_traces: tuple[tuple[int, tuple[str, ...]], ...] = ()
        self.grid = OrthogonalVonNeumannGrid(
            (config.world.width, config.world.height),
            torus=config.world.torus,
            capacity=None,
            random=self.random,
        )
        self.resource_layer = self.grid.create_property_layer(
            "resource_stock", config.resources.initial_stock, dtype=float
        )
        self.capacity_layer = self.grid.create_property_layer(
            "resource_capacity", config.resources.capacity, dtype=float
        )

        self.active_agents: dict[int, ForagerAgent] = {}
        self.cohort_states: dict[int, AgentState] = {}
        self.cohort_positions: dict[int, tuple[int, int]] = {}
        self.lifetime_harvest: dict[int, float] = {}
        self.cumulative_unmet_need: dict[int, float] = {}
        self._model_records: list[ModelRecord] = []
        self._cohort_records: list[CohortRecord] = []
        self._event_records: list[EventRecord] = []

        for agent_id, position in enumerate(config.agents.initial_positions):
            state = AgentState(agent_id=agent_id, energy=config.agents.initial_energy)
            agent = ForagerAgent(self, state, self.grid[position])
            self.active_agents[agent_id] = agent
            self.cohort_states[agent_id] = state
            self.cohort_positions[agent_id] = position
            self.lifetime_harvest[agent_id] = 0.0
            self.cumulative_unmet_need[agent_id] = 0.0

        self._measure(accumulate_need=True)

    @property
    def resource_stock(self) -> FloatArray:
        return self.resource_layer.data

    @property
    def resource_capacity(self) -> FloatArray:
        return self.capacity_layer.data

    @property
    def model_records(self) -> tuple[ModelRecord, ...]:
        return tuple(self._model_records)

    @property
    def cohort_records(self) -> tuple[CohortRecord, ...]:
        return tuple(self._cohort_records)

    @property
    def event_records(self) -> tuple[EventRecord, ...]:
        return tuple(self._event_records)

    def set_resource_fixture(self, *, capacity: FloatArray, stock: FloatArray) -> None:
        """Set a validated array fixture before execution for verification experiments."""

        if self.completed_ticks != 0:
            raise ValueError("resource fixtures can only be set before the first step")
        capacity_array = np.asarray(capacity, dtype=np.float64)
        stock_array = np.asarray(stock, dtype=np.float64)
        if capacity_array.shape != self.resource_capacity.shape:
            raise ValueError("resource fixture shape does not match the configured world")
        validate_resource_arrays(stock_array, capacity_array)
        self.capacity_layer.data = capacity_array
        self.resource_layer.data = stock_array
        self._model_records[-1] = replace(
            self._model_records[-1], total_resources=float(math.fsum(stock_array.flat))
        )

    def _living_snapshots(self, tick: int) -> dict[int, AgentSnapshot]:
        snapshots: dict[int, AgentSnapshot] = {}
        for agent_id in sorted(self.active_agents):
            agent = self.active_agents[agent_id]
            position = tuple(agent.cell.coordinate)
            state = agent.state
            snapshots[agent_id] = AgentSnapshot(
                tick=tick,
                agent_id=agent_id,
                position=position,
                energy=state.energy,
                alive=state.alive,
                resource_holdings=state.resource_holdings,
                debt=state.debt,
                information_capabilities=state.information_capabilities,
            )
        return snapshots

    def step(self) -> None:
        next_tick = self.completed_ticks + 1

        # 1. Environment: relaxation regeneration.
        self.resource_layer.data = regenerate(
            self.resource_stock,
            self.resource_capacity,
            self.config.resources.regeneration_rate,
        )

        # 2. Shock: the only v0.1 variant is an explicit no-op.

        # 3. Observation: immutable views of current cell resource stock.
        snapshots = self._living_snapshots(next_tick)
        observations = {
            agent_id: direct_observation(snapshot, float(self.resource_stock[snapshot.position]))
            for agent_id, snapshot in snapshots.items()
        }

        # 4. Belief update: copy observations without aliasing them.
        beliefs = {
            agent_id: copy_observation(observation)
            for agent_id, observation in observations.items()
        }

        # 5. Action intent: literal policy, with model-owned random generator.
        agent_config = self.config.agents
        intents = {}
        for agent_id, snapshot in snapshots.items():
            neighbors = tuple(cell.coordinate for cell in self.grid[snapshot.position].neighborhood)
            intents[agent_id] = literal_local_policy(
                snapshot,
                beliefs[agent_id],
                neighbors,
                harvest_threshold=agent_config.harvest_threshold,
                harvest_capacity=agent_config.harvest_capacity,
                rng=self.rng,
            )

        # 6. Institutional gate: allow every intent in v0.1.
        decisions = tuple(allow_all(intents[agent_id]) for agent_id in sorted(intents))

        # 7. Physical resolution: simultaneous harvest allocation and movement results.
        resolution = resolve_actions(self.resource_stock, decisions)
        self.resource_layer.data = resolution.resource_stock
        for agent_id, result in resolution.by_agent.items():
            agent = self.active_agents[agent_id]
            if result.moved and result.destination is not None:
                agent.move_to(self.grid[result.destination])
                self.cohort_positions[agent_id] = result.destination
                self._event_records.append(
                    EventRecord(next_tick, "move", agent_id, position=result.destination)
                )
            if result.harvested > 0:
                self.lifetime_harvest[agent_id] += result.harvested
                self._event_records.append(
                    EventRecord(
                        next_tick,
                        "harvest",
                        agent_id,
                        amount=result.harvested,
                        position=snapshots[agent_id].position,
                    )
                )

        # 8. Metabolism: conversion, basal cost, movement cost, and death flagging.
        dying: list[int] = []
        for agent_id in sorted(self.active_agents):
            result = resolution.by_agent[agent_id]
            agent = self.active_agents[agent_id]
            state, died = apply_metabolism(
                agent.state,
                harvested=result.harvested,
                moved=result.moved,
                conversion_efficiency=agent_config.conversion_efficiency,
                basal_cost=agent_config.basal_cost,
                movement_cost=agent_config.movement_cost,
            )
            agent.state = state
            self.cohort_states[agent_id] = state
            if died:
                dying.append(agent_id)

        # 9. Mortality: remove dead wrappers from Mesa but retain domain archives.
        for agent_id in dying:
            agent = self.active_agents.pop(agent_id)
            self.cohort_positions[agent_id] = tuple(agent.cell.coordinate)
            agent.remove()
            self._event_records.append(
                EventRecord(next_tick, "death", agent_id, position=self.cohort_positions[agent_id])
            )

        # 10. Measurement: record the original cohort after a complete transition.
        self.completed_ticks = next_tick
        self._measure(accumulate_need=True)
        self.stage_traces += ((next_tick, STAGE_ORDER),)

    def run(self) -> None:
        while self.completed_ticks < self.config.duration:
            self.step()

    def _measure(self, *, accumulate_need: bool) -> None:
        tick = self.completed_ticks
        energies = [self.cohort_states[index].energy for index in sorted(self.cohort_states)]
        current_unmet = {
            index: max(0.0, self.config.agents.viability_target - state.energy)
            for index, state in self.cohort_states.items()
        }
        if accumulate_need:
            for index, amount in current_unmet.items():
                self.cumulative_unmet_need[index] += amount

        for agent_id in sorted(self.cohort_states):
            state = self.cohort_states[agent_id]
            self._cohort_records.append(
                CohortRecord(
                    tick,
                    AgentSnapshot(
                        tick=tick,
                        agent_id=agent_id,
                        position=self.cohort_positions[agent_id],
                        energy=state.energy,
                        alive=state.alive,
                        resource_holdings=state.resource_holdings,
                        debt=state.debt,
                        information_capabilities=state.information_capabilities,
                    ),
                )
            )

        alive_count = sum(state.alive for state in self.cohort_states.values())
        self._model_records.append(
            ModelRecord(
                tick=tick,
                total_resources=float(math.fsum(self.resource_stock.flat)),
                alive_count=alive_count,
                cohort_mean_energy=float(math.fsum(energies) / len(energies)) if energies else 0.0,
                total_harvest=float(math.fsum(self.lifetime_harvest.values())),
                unmet_need=float(math.fsum(self.cumulative_unmet_need.values())),
                energy_gini=gini(energies),
            )
        )

    def summary(self) -> dict[str, Any]:
        latest = self._model_records[-1]
        energies = [state.energy for state in self.cohort_states.values()]
        harvest = list(self.lifetime_harvest.values())
        unmet = list(self.cumulative_unmet_need.values())
        cohort_size = len(self.cohort_states)
        return {
            "schema_version": "scs-run-summary/v0.1.0",
            "seed": self.config.seed,
            "completed_ticks": self.completed_ticks,
            "alive_count": latest.alive_count,
            "dead_count": cohort_size - latest.alive_count,
            "total_resources": latest.total_resources,
            "cohort_mean_energy": latest.cohort_mean_energy,
            "total_harvest": latest.total_harvest,
            "unmet_need": latest.unmet_need,
            "inequality": {
                "energy_gini": gini(energies),
                "harvest_gini": gini(harvest),
                "unmet_need_gini": gini(unmet),
            },
        }
