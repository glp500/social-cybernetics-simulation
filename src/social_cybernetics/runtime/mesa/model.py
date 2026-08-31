"""Thin Mesa orchestration whose step method mirrors the ODD+D schedule."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, Protocol

import numpy as np
from mesa import Model
from mesa.discrete_space import OrthogonalVonNeumannGrid
from numpy.typing import NDArray

from social_cybernetics.config import (
    CorrelatedShockConfig,
    IndependentShockConfig,
    NoShockConfig,
    SimulationConfig,
    SystemShockConfig,
)
from social_cybernetics.domain import (
    AgentSnapshot,
    AgentState,
    AgentTransitionRecord,
    CellDamageApplication,
    CohortRecord,
    DamageParameters,
    EventCellExposure,
    EventRecord,
    InvariantViolationError,
    ModelRecord,
    RecoveryState,
    ShockEventSnapshot,
    ShockEventState,
    ShockEventStatus,
    ShockScope,
    ShockTerminationReason,
    advance_correlated_event,
    allow_all,
    apply_metabolism,
    apply_recovery,
    apply_simultaneous_damage,
    copy_observation,
    direct_observation,
    draw_event,
    draw_independent_hits,
    draw_uniform_position,
    initialize_recovery_state,
    initialize_resources,
    literal_local_policy,
    relax_resources,
    resolve_actions,
    start_correlated_event,
)
from social_cybernetics.domain.ecology import validate_resource_arrays
from social_cybernetics.metrics import gini

from .agent import ForagerAgent

type FloatArray = NDArray[np.float64]

STAGE_ORDER = (
    "recovery",
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


class SpatialSnapshotSink(Protocol):
    """Runtime callback for persistence-owned, synchronous spatial streaming."""

    def record_spatial_snapshot(
        self,
        *,
        tick: int,
        resource_stock: NDArray[Any],
        effective_capacity: NDArray[Any],
        effective_regeneration: NDArray[Any],
        recovery_remaining: NDArray[Any],
        baseline_capacity: NDArray[Any],
        baseline_regeneration: NDArray[Any],
    ) -> None: ...


class SugarscapeModel(Model):
    """Deterministic material baseline hosted by Mesa discrete space."""

    def __init__(
        self,
        config: SimulationConfig,
        *,
        spatial_sink: SpatialSnapshotSink | None = None,
    ) -> None:
        super().__init__(rng=config.seed)
        self.config = config
        self._spatial_sink = spatial_sink
        self._last_spatial_tick = -1
        self.policy_rng = self._make_rng((1,))
        self.shock_initiation_rng = self._make_rng((2, 1))
        self.shock_location_rng = self._make_rng((2, 2))
        self.shock_transmission_rng = self._make_rng((2, 3))
        self.rng_provenance: dict[str, str | tuple[int, ...]] = {
            "bit_generator": self.policy_rng.bit_generator.__class__.__name__,
            "policy": (1,),
            "shock_initiation": (2, 1),
            "shock_location": (2, 2),
            "shock_transmission": (2, 3),
        }
        self.completed_ticks = 0
        self.stage_traces: tuple[tuple[int, tuple[str, ...]], ...] = ()
        self.grid = OrthogonalVonNeumannGrid(
            (config.world.width, config.world.height),
            torus=config.world.torus,
            capacity=None,
            random=self.random,
        )
        resource_stock, resource_capacity = initialize_resources(
            (config.world.width, config.world.height),
            initial_stock=config.resources.initial_stock,
            capacity=config.resources.capacity,
        )
        self.resource_layer = self.grid.create_property_layer("resource_stock", 0.0, dtype=float)
        self.capacity_layer = self.grid.create_property_layer("resource_capacity", 0.0, dtype=float)
        self.resource_layer.data = resource_stock
        self.capacity_layer.data = resource_capacity
        baseline_regeneration = np.full(
            resource_capacity.shape,
            config.resources.regeneration_rate,
            dtype=np.float64,
        )
        recovery = initialize_recovery_state(resource_capacity, baseline_regeneration)
        self.baseline_regeneration_layer = self.grid.create_property_layer(
            "baseline_regeneration", 0.0, dtype=float
        )
        self.effective_capacity_layer = self.grid.create_property_layer(
            "effective_capacity", 0.0, dtype=float
        )
        self.effective_regeneration_layer = self.grid.create_property_layer(
            "effective_regeneration", 0.0, dtype=float
        )
        self.recovery_remaining_layer = self.grid.create_property_layer(
            # Mesa's annotation currently narrows every property layer to float even
            # though its implementation accepts NumPy integer dtypes.
            "recovery_remaining",
            0,
            dtype=np.int64,  # pyright: ignore[reportArgumentType]
        )
        self.capacity_increment_layer = self.grid.create_property_layer(
            "capacity_recovery_increment", 0.0, dtype=float
        )
        self.regeneration_increment_layer = self.grid.create_property_layer(
            "regeneration_recovery_increment", 0.0, dtype=float
        )
        self.baseline_regeneration_layer.data = baseline_regeneration
        self._set_recovery_state(recovery)

        self.active_agents: dict[int, ForagerAgent] = {}
        self.cohort_states: dict[int, AgentState] = {}
        self.cohort_positions: dict[int, tuple[int, int]] = {}
        self.lifetime_harvest: dict[int, float] = {}
        self.cumulative_unmet_need: dict[int, float] = {}
        self._model_records: list[ModelRecord] = []
        self._cohort_records: list[CohortRecord] = []
        self._agent_transitions: list[AgentTransitionRecord] = []
        self._event_records: list[EventRecord] = []
        self._shock_event_snapshots: list[ShockEventSnapshot] = []
        self._shock_exposures: list[EventCellExposure] = []
        self._cell_damage_applications: list[CellDamageApplication] = []
        self._active_shock_events: dict[int, ShockEventState] = {}
        self._next_shock_event_id = 1

        for agent_id, position in enumerate(config.agents.initial_positions):
            state = AgentState(agent_id=agent_id, energy=config.agents.initial_energy)
            agent = ForagerAgent(self, state, self.grid[position])
            self.active_agents[agent_id] = agent
            self.cohort_states[agent_id] = state
            self.cohort_positions[agent_id] = position
            self.lifetime_harvest[agent_id] = 0.0
            self.cumulative_unmet_need[agent_id] = 0.0

        self._measure(accumulate_need=True)
        self.running = config.duration > 0

    def _make_rng(self, spawn_key: tuple[int, ...]) -> np.random.Generator:
        sequence = np.random.SeedSequence(self.config.seed, spawn_key=spawn_key)
        return np.random.default_rng(sequence)

    @property
    def resource_stock(self) -> FloatArray:
        return self.resource_layer.data

    @property
    def resource_capacity(self) -> FloatArray:
        return self.capacity_layer.data

    @property
    def baseline_regeneration(self) -> FloatArray:
        return self.baseline_regeneration_layer.data

    @property
    def effective_capacity(self) -> FloatArray:
        return self.effective_capacity_layer.data

    @property
    def effective_regeneration(self) -> FloatArray:
        return self.effective_regeneration_layer.data

    @property
    def recovery_remaining(self) -> NDArray[np.int64]:
        return self.recovery_remaining_layer.data

    @property
    def model_records(self) -> tuple[ModelRecord, ...]:
        return tuple(self._model_records)

    @property
    def cohort_records(self) -> tuple[CohortRecord, ...]:
        return tuple(self._cohort_records)

    @property
    def event_records(self) -> tuple[EventRecord, ...]:
        return tuple(self._event_records)

    @property
    def agent_transitions(self) -> tuple[AgentTransitionRecord, ...]:
        return tuple(self._agent_transitions)

    @property
    def shock_event_snapshots(self) -> tuple[ShockEventSnapshot, ...]:
        return tuple(self._shock_event_snapshots)

    @property
    def shock_exposures(self) -> tuple[EventCellExposure, ...]:
        return tuple(self._shock_exposures)

    @property
    def cell_damage_applications(self) -> tuple[CellDamageApplication, ...]:
        return tuple(self._cell_damage_applications)

    def _recovery_state(self) -> RecoveryState:
        return RecoveryState.create(
            self.effective_capacity,
            self.effective_regeneration,
            self.recovery_remaining,
            self.capacity_increment_layer.data,
            self.regeneration_increment_layer.data,
        )

    def _set_recovery_state(self, recovery: RecoveryState) -> None:
        self.effective_capacity_layer.data = np.array(recovery.effective_capacity, copy=True)
        self.effective_regeneration_layer.data = np.array(
            recovery.effective_regeneration, copy=True
        )
        self.recovery_remaining_layer.data = np.array(recovery.remaining_ticks, copy=True)
        self.capacity_increment_layer.data = np.array(recovery.capacity_increment, copy=True)
        self.regeneration_increment_layer.data = np.array(
            recovery.regeneration_increment, copy=True
        )

    def set_resource_fixture(self, *, capacity: FloatArray, stock: FloatArray) -> None:
        """Set a validated array fixture before execution for verification experiments."""

        if self.completed_ticks != 0:
            raise ValueError("resource fixtures can only be set before the first step")
        if self._last_spatial_tick >= 0:
            raise ValueError("resource fixtures cannot change after spatial recording begins")
        capacity_array = np.asarray(capacity, dtype=np.float64)
        stock_array = np.asarray(stock, dtype=np.float64)
        if capacity_array.shape != self.resource_capacity.shape:
            raise ValueError("resource fixture shape does not match the configured world")
        validate_resource_arrays(stock_array, capacity_array)
        self.capacity_layer.data = capacity_array
        self.resource_layer.data = stock_array
        self._set_recovery_state(
            initialize_recovery_state(capacity_array, self.baseline_regeneration)
        )
        self._model_records[-1] = replace(
            self._model_records[-1], total_resources=float(math.fsum(stock_array.flat))
        )

    def _living_snapshots(self, tick: int) -> dict[int, AgentSnapshot]:
        snapshots: dict[int, AgentSnapshot] = {}
        for agent_id in sorted(self.active_agents):
            agent = self.active_agents[agent_id]
            position = self._agent_position(agent)
            state = agent.state
            snapshots[agent_id] = AgentSnapshot(
                tick=tick,
                agent_id=agent_id,
                position=position,
                energy=state.energy,
                alive=state.alive,
            )
        return snapshots

    def _record_spatial_snapshot(self) -> None:
        sink = self._spatial_sink
        if sink is None:
            return
        expected_tick = self._last_spatial_tick + 1
        if self.completed_ticks != expected_tick:
            raise InvariantViolationError(
                f"expected spatial snapshot tick {expected_tick}, got {self.completed_ticks}"
            )
        sink.record_spatial_snapshot(
            tick=self.completed_ticks,
            resource_stock=self.resource_stock,
            effective_capacity=self.effective_capacity,
            effective_regeneration=self.effective_regeneration,
            recovery_remaining=self.recovery_remaining,
            baseline_capacity=self.resource_capacity,
            baseline_regeneration=self.baseline_regeneration,
        )
        self._last_spatial_tick = self.completed_ticks

    @staticmethod
    def _agent_position(agent: ForagerAgent) -> tuple[int, int]:
        cell = agent.cell
        if cell is None or len(cell.coordinate) != 2:
            raise InvariantViolationError("active agent must occupy one two-dimensional cell")
        return int(cell.coordinate[0]), int(cell.coordinate[1])

    def step(self) -> None:
        if self._spatial_sink is not None and self._last_spatial_tick < 0:
            self._record_spatial_snapshot()
        next_tick = self.completed_ticks + 1

        # 1. Recovery: advance existing cell-local damage clocks.
        self._set_recovery_state(
            apply_recovery(
                self._recovery_state(),
                self.resource_capacity,
                self.baseline_regeneration,
            )
        )

        # 2. Regeneration: signed relaxation toward current effective capacity.
        self.resource_layer.data = relax_resources(
            self.resource_stock,
            effective_capacity=self.effective_capacity,
            effective_regeneration=self.effective_regeneration,
            baseline_capacity=self.resource_capacity,
        )

        # 3. Shock: advance active wavefronts, initiate events, and resolve hits once per cell.
        self._advance_shocks(next_tick)

        # 4. Observation: immutable views of current cell resource stock.
        snapshots = self._living_snapshots(next_tick)
        observations = {
            agent_id: direct_observation(snapshot, float(self.resource_stock[snapshot.position]))
            for agent_id, snapshot in snapshots.items()
        }

        # 5. Belief update: copy observations without aliasing them.
        beliefs = {
            agent_id: copy_observation(observation)
            for agent_id, observation in observations.items()
        }

        # 6. Action intent: literal policy, with its stable model-owned substream.
        agent_config = self.config.agents
        intents = {}
        for agent_id, snapshot in snapshots.items():
            neighbors = tuple(
                (int(cell.coordinate[0]), int(cell.coordinate[1]))
                for cell in self.grid[snapshot.position].neighborhood
            )
            intents[agent_id] = literal_local_policy(
                snapshot,
                beliefs[agent_id],
                neighbors,
                harvest_threshold=agent_config.harvest_threshold,
                harvest_capacity=agent_config.harvest_capacity,
                rng=self.policy_rng,
            )

        # 7. Institutional gate: allow every intent in v0.1.
        decisions = tuple(allow_all(intents[agent_id]) for agent_id in sorted(intents))
        decisions_by_agent = {decision.agent_id: decision for decision in decisions}

        # 8. Physical resolution: simultaneous harvest allocation and movement results.
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

        # 9. Metabolism: conversion, basal cost, movement cost, and death flagging.
        dying: list[int] = []
        for agent_id in sorted(self.active_agents):
            result = resolution.by_agent[agent_id]
            agent = self.active_agents[agent_id]
            energy_before = agent.state.energy
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
            intent = intents[agent_id]
            self._agent_transitions.append(
                AgentTransitionRecord(
                    tick=next_tick,
                    agent_id=agent_id,
                    origin=snapshots[agent_id].position,
                    observed_stock=observations[agent_id].local_stock,
                    believed_stock=beliefs[agent_id].believed_local_stock,
                    intent_kind=intent.kind,
                    requested_amount=intent.amount,
                    intended_destination=intent.destination,
                    gate_allowed=decisions_by_agent[agent_id].allowed,
                    harvested=result.harvested,
                    moved=result.moved,
                    final_position=self._agent_position(agent),
                    energy_before=energy_before,
                    energy_after=state.energy,
                    shortfall=max(0.0, agent_config.viability_target - state.energy),
                    died=died,
                )
            )
            if died:
                dying.append(agent_id)

        # 10. Mortality: remove dead wrappers from Mesa but retain domain archives.
        for agent_id in dying:
            agent = self.active_agents.pop(agent_id)
            self.cohort_positions[agent_id] = self._agent_position(agent)
            agent.remove()
            self._event_records.append(
                EventRecord(next_tick, "death", agent_id, position=self.cohort_positions[agent_id])
            )

        # 11. Measurement: record the original cohort after a complete transition.
        self.completed_ticks = next_tick
        self._measure(accumulate_need=True)
        self._record_spatial_snapshot()
        self.stage_traces += ((next_tick, STAGE_ORDER),)
        if self.completed_ticks >= self.config.duration:
            self.running = False

    def _damage_parameters(self) -> DamageParameters | None:
        shock = self.config.shock
        if isinstance(shock, NoShockConfig):
            return None
        return DamageParameters(
            stock_loss_fraction=shock.stock_loss_fraction,
            capacity_loss_fraction=shock.capacity_loss_fraction,
            regeneration_suppression_fraction=shock.regeneration_suppression_fraction,
            recovery_ticks=shock.recovery_ticks,
        )

    def _allocate_event_id(self) -> int:
        event_id = self._next_shock_event_id
        self._next_shock_event_id += 1
        return event_id

    def _correlated_snapshot(
        self,
        tick: int,
        event: ShockEventState,
        shock: CorrelatedShockConfig,
        damage: DamageParameters,
    ) -> ShockEventSnapshot:
        return ShockEventSnapshot(
            tick=tick,
            event_id=event.event_id,
            scope=ShockScope.CORRELATED,
            initiation_tick=event.initiation_tick,
            epicenter=event.epicenter,
            age=event.spread_rounds_completed,
            status=event.status,
            frontier=tuple(sorted(event.frontier)),
            affected_count=len(event.affected),
            event_probability=shock.event_probability,
            damage=damage,
            spread_probability=shock.spread_probability,
            max_spread_ticks=shock.max_spread_ticks,
            termination_reason=event.termination_reason,
        )

    def _nonspreading_snapshot(
        self,
        *,
        tick: int,
        event_id: int,
        scope: ShockScope,
        positions: tuple[tuple[int, int], ...],
        event_probability: float,
        damage: DamageParameters,
        epicenter: tuple[int, int] | None,
    ) -> ShockEventSnapshot:
        return ShockEventSnapshot(
            tick=tick,
            event_id=event_id,
            scope=scope,
            initiation_tick=tick,
            epicenter=epicenter,
            age=0,
            status=ShockEventStatus.TERMINATED,
            frontier=positions,
            affected_count=len(positions),
            event_probability=event_probability,
            damage=damage,
            termination_reason=ShockTerminationReason.NONSPREADING,
        )

    def _advance_correlated_shocks(
        self,
        tick: int,
        shock: CorrelatedShockConfig,
        damage: DamageParameters,
        hits: dict[tuple[int, int], list[int]],
        snapshots: list[ShockEventSnapshot],
    ) -> None:
        shape = (self.config.world.width, self.config.world.height)
        for event_id in sorted(tuple(self._active_shock_events)):
            result = advance_correlated_event(
                self._active_shock_events[event_id],
                tick=tick,
                shape=shape,
                torus=self.config.world.torus,
                rng=self.shock_transmission_rng,
            )
            self._shock_exposures.extend(result.exposures)
            for position in result.newly_affected:
                hits.setdefault(position, []).append(event_id)
            if result.event.status is ShockEventStatus.ACTIVE:
                self._active_shock_events[event_id] = result.event
            else:
                del self._active_shock_events[event_id]
            snapshots.append(self._correlated_snapshot(tick, result.event, shock, damage))

        if not draw_event(shock.event_probability, self.shock_initiation_rng):
            return
        event_id = self._allocate_event_id()
        epicenter = draw_uniform_position(shape, self.shock_location_rng)
        event = start_correlated_event(
            event_id,
            tick,
            epicenter,
            shock.spread_probability,
            shock.max_spread_ticks,
        )
        hits.setdefault(epicenter, []).append(event_id)
        if event.status is ShockEventStatus.ACTIVE:
            self._active_shock_events[event_id] = event
        snapshots.append(self._correlated_snapshot(tick, event, shock, damage))

    def _advance_independent_shocks(
        self,
        tick: int,
        shock: IndependentShockConfig,
        damage: DamageParameters,
        hits: dict[tuple[int, int], list[int]],
        snapshots: list[ShockEventSnapshot],
    ) -> None:
        shape = (self.config.world.width, self.config.world.height)
        for position in draw_independent_hits(
            shape, shock.event_probability, self.shock_initiation_rng
        ):
            event_id = self._allocate_event_id()
            hits.setdefault(position, []).append(event_id)
            snapshots.append(
                self._nonspreading_snapshot(
                    tick=tick,
                    event_id=event_id,
                    scope=ShockScope.INDEPENDENT,
                    positions=(position,),
                    event_probability=shock.event_probability,
                    damage=damage,
                    epicenter=position,
                )
            )

    def _advance_system_shock(
        self,
        tick: int,
        shock: SystemShockConfig,
        damage: DamageParameters,
        hits: dict[tuple[int, int], list[int]],
        snapshots: list[ShockEventSnapshot],
    ) -> None:
        if not draw_event(shock.event_probability, self.shock_initiation_rng):
            return
        event_id = self._allocate_event_id()
        shape = (self.config.world.width, self.config.world.height)
        positions = tuple((x, y) for x in range(shape[0]) for y in range(shape[1]))
        for position in positions:
            hits.setdefault(position, []).append(event_id)
        snapshots.append(
            self._nonspreading_snapshot(
                tick=tick,
                event_id=event_id,
                scope=ShockScope.SYSTEM,
                positions=positions,
                event_probability=shock.event_probability,
                damage=damage,
                epicenter=None,
            )
        )

    def _apply_shock_hits(
        self,
        *,
        tick: int,
        damage: DamageParameters,
        hits: dict[tuple[int, int], list[int]],
    ) -> None:
        if not hits:
            return
        batch = apply_simultaneous_damage(
            self.resource_stock,
            self._recovery_state(),
            self.resource_capacity,
            self.baseline_regeneration,
            hits={position: tuple(event_ids) for position, event_ids in hits.items()},
            parameters=damage,
            tick=tick,
        )
        self.resource_layer.data = np.array(batch.resource_stock, copy=True)
        self._set_recovery_state(batch.recovery)
        self._cell_damage_applications.extend(batch.applications)

    def _advance_shocks(self, tick: int) -> None:
        shock = self.config.shock
        damage = self._damage_parameters()
        if damage is None:
            return

        hits: dict[tuple[int, int], list[int]] = {}
        snapshots: list[ShockEventSnapshot] = []
        if isinstance(shock, CorrelatedShockConfig):
            self._advance_correlated_shocks(tick, shock, damage, hits, snapshots)
        elif isinstance(shock, IndependentShockConfig):
            self._advance_independent_shocks(tick, shock, damage, hits, snapshots)
        elif isinstance(shock, SystemShockConfig):
            self._advance_system_shock(tick, shock, damage, hits, snapshots)
        self._apply_shock_hits(tick=tick, damage=damage, hits=hits)
        self._shock_event_snapshots.extend(snapshots)

    def run(self) -> None:
        if self._spatial_sink is not None and self._last_spatial_tick < 0:
            self._record_spatial_snapshot()
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
