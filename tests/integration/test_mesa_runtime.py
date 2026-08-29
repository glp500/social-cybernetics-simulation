from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from social_cybernetics.config import (
    AgentConfig,
    CorrelatedShockConfig,
    IndependentShockConfig,
    ResourceConfig,
    SimulationConfig,
    SystemShockConfig,
    WorldConfig,
    load_config,
)
from social_cybernetics.domain import ShockEventStatus, ShockScope
from social_cybernetics.runtime.mesa.model import STAGE_ORDER, SugarscapeModel


class RecordingSpatialSink:
    def __init__(self) -> None:
        self.snapshots: list[dict[str, int | NDArray[Any]]] = []

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
    ) -> None:
        self.snapshots.append(
            {
                "tick": tick,
                "resource_stock": np.array(resource_stock, copy=True),
                "effective_capacity": np.array(effective_capacity, copy=True),
                "effective_regeneration": np.array(effective_regeneration, copy=True),
                "recovery_remaining": np.array(recovery_remaining, copy=True),
                "baseline_capacity": np.array(baseline_capacity, copy=True),
                "baseline_regeneration": np.array(baseline_regeneration, copy=True),
            }
        )


def test_initial_and_completed_tick_snapshots_are_recorded() -> None:
    model = SugarscapeModel(SimulationConfig(duration=1))

    assert [record.tick for record in model.model_records] == [0]
    assert [record.tick for record in model.cohort_records] == [0]

    model.step()

    assert model.completed_ticks == 1
    assert model.stage_traces == ((1, STAGE_ORDER),)
    assert [record.tick for record in model.model_records] == [0, 1]
    assert [record.tick for record in model.cohort_records] == [0, 1]
    assert model.model_records[-1].total_resources == pytest.approx(248.0)
    assert model.cohort_records[-1].snapshot.energy == pytest.approx(11.0)


def test_spatial_sink_receives_tick_zero_and_every_completed_tick() -> None:
    sink = RecordingSpatialSink()
    model = SugarscapeModel(SimulationConfig(duration=2), spatial_sink=sink)

    assert sink.snapshots == []

    model.run()

    assert [snapshot["tick"] for snapshot in sink.snapshots] == [0, 1, 2]
    np.testing.assert_array_equal(sink.snapshots[0]["resource_stock"], 10.0)
    np.testing.assert_array_equal(sink.snapshots[-1]["resource_stock"], model.resource_stock)
    np.testing.assert_array_equal(
        sink.snapshots[-1]["effective_capacity"], model.effective_capacity
    )
    np.testing.assert_array_equal(
        sink.snapshots[-1]["recovery_remaining"], model.recovery_remaining
    )


def test_tick_zero_spatial_snapshot_reflects_a_pre_run_resource_fixture() -> None:
    sink = RecordingSpatialSink()
    model = SugarscapeModel(SimulationConfig(duration=0), spatial_sink=sink)
    fixture = np.full((5, 5), 4.0)
    model.set_resource_fixture(capacity=fixture, stock=fixture / 2)

    model.run()

    assert [snapshot["tick"] for snapshot in sink.snapshots] == [0]
    np.testing.assert_array_equal(sink.snapshots[0]["resource_stock"], fixture / 2)
    np.testing.assert_array_equal(sink.snapshots[0]["baseline_capacity"], fixture)


def test_resource_fixture_is_rejected_after_tick_zero_has_been_streamed() -> None:
    sink = RecordingSpatialSink()
    model = SugarscapeModel(SimulationConfig(duration=0), spatial_sink=sink)
    model.run()
    fixture = np.full((5, 5), 4.0)

    with pytest.raises(ValueError, match="spatial recording"):
        model.set_resource_fixture(capacity=fixture, stock=fixture / 2)


def test_rng_registry_uses_stable_recorded_mechanism_namespaces() -> None:
    first = SugarscapeModel(SimulationConfig(duration=0))
    second = SugarscapeModel(SimulationConfig(duration=0))

    assert first.rng_provenance == {
        "bit_generator": "PCG64",
        "policy": (1,),
        "shock_initiation": (2, 1),
        "shock_location": (2, 2),
        "shock_transmission": (2, 3),
    }
    assert first.policy_rng.random() == second.policy_rng.random()
    assert first.shock_initiation_rng.random() == second.shock_initiation_rng.random()


def test_v01_stochastic_policy_trajectory_is_rebaselined_to_stream_one() -> None:
    config = SimulationConfig(
        seed=42,
        duration=3,
        resources=ResourceConfig(initial_stock=0, capacity=0, regeneration_rate=0),
        agents=AgentConfig(initial_energy=100),
    )
    model = SugarscapeModel(config)

    model.run()

    assert [record.position for record in model.event_records] == [(1, 2), (1, 1), (0, 1)]
    assert [record.snapshot.position for record in model.cohort_records] == [
        (2, 2),
        (1, 2),
        (1, 1),
        (0, 1),
    ]


def test_no_agent_world_converges_to_capacity() -> None:
    config = SimulationConfig(
        duration=1_000,
        resources=ResourceConfig(initial_stock=0, capacity=10, regeneration_rate=0.1),
        agents=AgentConfig(count=0, initial_positions=()),
    )
    model = SugarscapeModel(config)

    model.run()

    assert model.model_records[-1].total_resources == pytest.approx(250.0)
    assert model.completed_ticks == 1_000


def test_explicit_landscape_initializes_and_steps_without_transposition() -> None:
    config = load_config(Path("configs/ecology-v0.2.yml"))
    model = SugarscapeModel(config)

    np.testing.assert_array_equal(
        model.resource_capacity,
        [[4.0, 8.0], [6.0, 10.0], [2.0, 12.0]],
    )
    np.testing.assert_array_equal(
        model.resource_stock,
        [[2.0, 8.0], [3.0, 5.0], [1.0, 6.0]],
    )
    assert model.model_records[0].total_resources == pytest.approx(25.0)

    model.step()

    assert model.model_records[-1].total_resources == pytest.approx(24.7)
    assert model.cohort_records[-1].snapshot.position == (1, 1)
    assert model.cohort_records[-1].snapshot.energy == pytest.approx(11.0)


def test_system_shock_damages_all_cells_and_records_normalized_evidence() -> None:
    config = SimulationConfig(
        schema_version="0.2.0",
        duration=1,
        world=WorldConfig(width=2, height=1),
        resources=ResourceConfig(initial_stock=10, capacity=10, regeneration_rate=0.2),
        agents=AgentConfig(count=0, initial_positions=()),
        shock=SystemShockConfig(
            event_probability=1,
            stock_loss_fraction=0.5,
            capacity_loss_fraction=0.2,
            regeneration_suppression_fraction=0.5,
            recovery_ticks=2,
        ),
    )
    model = SugarscapeModel(config)

    model.step()

    np.testing.assert_allclose(model.resource_stock, [[5.0], [5.0]])
    np.testing.assert_allclose(model.effective_capacity, [[8.0], [8.0]])
    np.testing.assert_allclose(model.effective_regeneration, [[0.1], [0.1]])
    np.testing.assert_array_equal(model.recovery_remaining, [[2], [2]])
    assert len(model.shock_event_snapshots) == 1
    snapshot = model.shock_event_snapshots[0]
    assert snapshot.scope is ShockScope.SYSTEM
    assert snapshot.status is ShockEventStatus.TERMINATED
    assert snapshot.epicenter is None
    assert snapshot.affected_count == 2
    assert len(model.cell_damage_applications) == 2
    assert all(record.event_ids == (1,) for record in model.cell_damage_applications)


def test_correlated_events_propagate_concurrently_with_immutable_records() -> None:
    config = SimulationConfig(
        schema_version="0.2.0",
        seed=9,
        duration=2,
        world=WorldConfig(width=3, height=3),
        resources=ResourceConfig(initial_stock=10, capacity=10, regeneration_rate=0),
        agents=AgentConfig(count=0, initial_positions=()),
        shock=CorrelatedShockConfig(
            event_probability=1,
            stock_loss_fraction=0.5,
            capacity_loss_fraction=0,
            regeneration_suppression_fraction=0,
            recovery_ticks=2,
            spread_probability=1,
            max_spread_ticks=1,
        ),
    )
    first = SugarscapeModel(config)
    second = SugarscapeModel(config)

    first.run()
    second.run()

    assert first.shock_event_snapshots == second.shock_event_snapshots
    assert first.shock_exposures == second.shock_exposures
    assert first.cell_damage_applications == second.cell_damage_applications
    assert [item.event_id for item in first.shock_event_snapshots] == [1, 1, 2]
    assert first.shock_event_snapshots[1].status is ShockEventStatus.TERMINATED
    assert first.shock_event_snapshots[2].status is ShockEventStatus.ACTIVE
    assert all(item.transmitted for item in first.shock_exposures)
    assert all(
        tuple(sorted(item.event_ids)) == item.event_ids for item in first.cell_damage_applications
    )


def test_sham_shocks_do_not_shift_policy_or_physical_trajectories() -> None:
    common = {
        "schema_version": "0.2.0",
        "seed": 17,
        "duration": 20,
        "resources": ResourceConfig(initial_stock=0, capacity=0, regeneration_rate=0),
        "agents": AgentConfig(initial_energy=100),
    }
    control = SugarscapeModel(SimulationConfig(**common))
    sham = SugarscapeModel(
        SimulationConfig(
            **common,
            shock=IndependentShockConfig(
                event_probability=1,
                stock_loss_fraction=0,
                capacity_loss_fraction=0,
                regeneration_suppression_fraction=0,
                recovery_ticks=1,
            ),
        )
    )

    control.run()
    sham.run()

    assert control.model_records == sham.model_records
    assert control.cohort_records == sham.cohort_records
    assert control.event_records == sham.event_records
    assert sham.shock_event_snapshots


def test_scarcity_causes_death_but_keeps_the_original_cohort() -> None:
    config = SimulationConfig(
        duration=1,
        resources=ResourceConfig(initial_stock=0, capacity=0, regeneration_rate=0),
        agents=AgentConfig(initial_energy=0.1),
    )
    model = SugarscapeModel(config)

    model.run()

    assert len(model.agents) == 0
    assert model.cohort_states[0].alive is False
    assert model.cohort_states[0].energy == 0
    assert [record.snapshot.alive for record in model.cohort_records] == [True, False]
    assert any(event.event == "death" for event in model.event_records)


def test_two_agents_contest_one_cell_proportionally() -> None:
    config = SimulationConfig(
        duration=1,
        resources=ResourceConfig(initial_stock=3, capacity=3, regeneration_rate=0),
        agents=AgentConfig(count=2, initial_positions=((2, 2), (2, 2))),
    )
    model = SugarscapeModel(config)

    model.run()

    assert [model.cohort_states[index].energy for index in (0, 1)] == [10.5, 10.5]
    assert model.lifetime_harvest == {0: 1.5, 1: 1.5}
    assert model.resource_stock[2, 2] == 0


def test_same_seed_reproduces_complete_records_even_if_agent_mapping_is_reordered() -> None:
    config = SimulationConfig(
        duration=20,
        resources=ResourceConfig(initial_stock=0.5, capacity=10, regeneration_rate=0.1),
        agents=AgentConfig(count=2, initial_positions=((2, 2), (2, 2))),
    )
    first = SugarscapeModel(config)
    second = SugarscapeModel(config)
    second.active_agents = dict(reversed(tuple(second.active_agents.items())))

    first.run()
    second.run()

    assert first.model_records == second.model_records
    assert first.cohort_records == second.cohort_records
    assert first.event_records == second.event_records
    assert first.summary() == second.summary()


def test_ten_agents_run_on_a_deterministic_heterogeneous_fixture() -> None:
    positions = tuple((index % 5, index // 5) for index in range(10))
    config = SimulationConfig(
        duration=5,
        agents=AgentConfig(count=10, initial_positions=positions),
    )
    first = SugarscapeModel(config)
    second = SugarscapeModel(config)
    fixture = first.resource_capacity.copy()
    fixture[0, :] = 2.0
    fixture[4, :] = 6.0
    for model in (first, second):
        model.set_resource_fixture(capacity=fixture, stock=fixture / 2)
        model.run()

    assert first.model_records == second.model_records
    assert first.cohort_records == second.cohort_records
