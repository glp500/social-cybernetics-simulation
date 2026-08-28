from dataclasses import replace

import pytest

from social_cybernetics.config import AgentConfig, ResourceConfig, SimulationConfig
from social_cybernetics.runtime.mesa.model import STAGE_ORDER, SugarscapeModel


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
        agents=replace(AgentConfig(), count=10, initial_positions=positions),
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
