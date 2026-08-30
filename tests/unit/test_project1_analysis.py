from dataclasses import replace

import numpy as np
import pytest

from social_cybernetics.analysis import (
    calculate_distribution,
    calculate_ecology,
    calculate_persistence,
    calculate_subsistence_security,
)
from social_cybernetics.domain import (
    ActionKind,
    AgentSnapshot,
    AgentTransitionRecord,
    CohortRecord,
)


def transition(
    agent_id: int,
    tick: int,
    *,
    shortfall: float,
    harvested: float = 0.0,
    died: bool = False,
) -> AgentTransitionRecord:
    energy = 0.0 if died else 10.0 - shortfall
    return AgentTransitionRecord(
        tick=tick,
        agent_id=agent_id,
        origin=(0, 0),
        observed_stock=0.0,
        believed_stock=0.0,
        intent_kind=ActionKind.MOVE,
        requested_amount=0.0,
        intended_destination=(0, 1),
        gate_allowed=True,
        harvested=harvested,
        moved=True,
        final_position=(0, 1),
        energy_before=max(0.0, energy + 1.25),
        energy_after=energy,
        shortfall=shortfall,
        died=died,
    )


def test_subsistence_metrics_reconstruct_spells_depth_and_catastrophe() -> None:
    records = (
        transition(0, 1, shortfall=2.0),
        transition(1, 1, shortfall=0.0),
        transition(0, 2, shortfall=3.0),
        transition(1, 2, shortfall=1.0),
        transition(0, 3, shortfall=0.0),
        transition(1, 3, shortfall=1.0),
        transition(0, 4, shortfall=1.0),
        transition(1, 4, shortfall=1.0),
        transition(0, 5, shortfall=10.0, died=True),
        transition(1, 5, shortfall=1.0),
    )

    metrics = calculate_subsistence_security(tuple(reversed(records)), completed_ticks=5)

    assert metrics.shortfall_frequency == pytest.approx(0.8)
    assert [spell.length for spell in metrics.spells] == [2, 2, 4]
    assert [spell.right_censored for spell in metrics.spells] == [False, False, True]
    assert metrics.mean_spell_length == pytest.approx(8 / 3)
    assert metrics.mean_shortfall_depth == pytest.approx(2.5)
    assert metrics.maximum_shortfall_depth == 10.0
    assert metrics.catastrophic_shortfall_probability == pytest.approx(0.1)


def test_subsistence_metrics_define_empty_history() -> None:
    metrics = calculate_subsistence_security((), completed_ticks=0)

    assert metrics.shortfall_frequency == 0.0
    assert metrics.spells == ()
    assert metrics.mean_spell_length == 0.0
    assert metrics.mean_shortfall_depth == 0.0
    assert metrics.maximum_shortfall_depth == 0.0
    assert metrics.catastrophic_shortfall_probability == 0.0


def test_subsistence_metrics_reject_duplicate_or_incomplete_active_histories() -> None:
    record = transition(0, 1, shortfall=1.0)
    with pytest.raises(ValueError, match="duplicated"):
        calculate_subsistence_security((record, record), completed_ticks=1)
    with pytest.raises(ValueError, match="final tick"):
        calculate_subsistence_security((record,), completed_ticks=2)


def test_subsistence_metrics_reject_inconsistent_death_and_shortfall_values() -> None:
    record = transition(0, 1, shortfall=1.0)
    with pytest.raises(ValueError, match="nonnegative"):
        calculate_subsistence_security((replace(record, shortfall=-1.0),), completed_ticks=1)
    with pytest.raises(ValueError, match="zero energy"):
        calculate_subsistence_security((replace(record, died=True),), completed_ticks=1)


def cohort_history(
    final_energies: tuple[float, ...], completed_ticks: int
) -> tuple[CohortRecord, ...]:
    records = []
    for tick in range(completed_ticks + 1):
        for agent_id, final_energy in enumerate(final_energies):
            energy = 10.0 if tick < completed_ticks else final_energy
            records.append(
                CohortRecord(
                    tick,
                    AgentSnapshot(tick, agent_id, (agent_id, 0), energy, True),
                )
            )
    return tuple(records)


def test_distribution_metrics_keep_material_outcomes_distinct() -> None:
    records = tuple(
        transition(agent_id, tick, shortfall=shortfall, harvested=harvested)
        for tick, values in enumerate(
            (
                ((2.0, 1.0), (0.0, 0.0)),
                ((2.0, 1.0), (1.0, 0.0)),
                ((0.0, 1.0), (2.0, 0.0)),
                ((0.0, 1.0), (2.0, 0.0)),
            ),
            start=1,
        )
        for agent_id, (harvested, shortfall) in enumerate(values)
    )

    metrics = calculate_distribution(records, cohort_history((5.0, 10.0), 4), completed_ticks=4)

    assert metrics.cumulative_harvest == ((0, 4.0), (1, 5.0))
    assert metrics.cumulative_unmet_need == ((0, 4.0), (1, 0.0))
    assert metrics.harvest_gini == pytest.approx(1 / 18)
    assert metrics.energy_gini == pytest.approx(1 / 6)
    assert metrics.unmet_need_gini == pytest.approx(0.5)
    assert metrics.top_10_percent_harvest_share.value == pytest.approx(5 / 9)
    assert metrics.bottom_25_percent_shortfall_share.value == 1.0


def test_persistence_metrics_reconstruct_rank_reversal_advantage_and_half_life() -> None:
    records = tuple(
        transition(agent_id, tick, shortfall=shortfall, harvested=harvested)
        for tick, values in enumerate(
            (
                ((2.0, 1.0), (0.0, 0.0)),
                ((2.0, 1.0), (1.0, 0.0)),
                ((0.0, 1.0), (2.0, 0.0)),
                ((0.0, 1.0), (2.0, 0.0)),
            ),
            start=1,
        )
        for agent_id, (harvested, shortfall) in enumerate(values)
    )

    metrics = calculate_persistence(
        tuple(reversed(records)), cohort_history((5.0, 10.0), 4), completed_ticks=4
    )

    assert metrics.material_rank_autocorrelation.value == pytest.approx(-1.0)
    assert metrics.rank_transition.counts[3][1] == 1
    assert metrics.rank_transition.counts[1][3] == 1
    assert metrics.advantage_duration.spell_lengths == (3, 1)
    assert metrics.advantage_duration.mean == 2.0
    assert metrics.advantage_duration.maximum == 3
    assert metrics.inequality_half_life.value == 2
    assert metrics.inequality_half_life.peak_tick == 1
    assert metrics.inequality_half_life.right_censored is False


def test_persistence_reports_tied_rank_undefinedness_and_zero_inequality() -> None:
    records = tuple(
        transition(agent_id, tick, shortfall=0.0, harvested=1.0)
        for tick in (1, 2)
        for agent_id in (0, 1)
    )

    metrics = calculate_persistence(records, cohort_history((10.0, 10.0), 2), completed_ticks=2)

    assert metrics.material_rank_autocorrelation.value is None
    assert metrics.material_rank_autocorrelation.reason == "constant cumulative-harvest ranks"
    assert metrics.inequality_half_life.value == 0
    assert metrics.inequality_half_life.right_censored is False


def test_ecology_metrics_reconstruct_deficits_and_completed_recovery() -> None:
    stock = np.array([[[10.0]], [[5.0]], [[7.5]], [[8.75]]])
    effective_capacity = np.array([[[10.0]], [[5.0]], [[7.5]], [[10.0]]])
    effective_regeneration = np.array([[[0.2]], [[0.1]], [[0.15]], [[0.2]]])
    remaining = np.array([[[0]], [[2]], [[1]], [[0]]])

    metrics = calculate_ecology(
        resource_stock=stock,
        effective_capacity=effective_capacity,
        effective_regeneration=effective_regeneration,
        recovery_remaining=remaining,
        baseline_capacity=np.array([[10.0]]),
        baseline_regeneration=np.array([[0.2]]),
    )

    assert metrics.resource_depletion.values == pytest.approx((0.0, 0.5, 0.25, 0.125))
    assert metrics.capacity_deficit.values == pytest.approx((0.0, 0.5, 0.25, 0.0))
    assert metrics.regeneration_deficit.values == pytest.approx((0.0, 0.5, 0.25, 0.0))
    assert metrics.recovery_spells[0].length == 2
    assert metrics.recovery_spells[0].right_censored is False
    assert metrics.completed_mean_recovery_duration == 2.0
    assert metrics.cumulative_capacity_deficit == pytest.approx(0.75)
    assert metrics.cumulative_regeneration_deficit == pytest.approx(0.75)
    assert metrics.cumulative_recovery_deficit == pytest.approx(0.75)


def test_ecology_metrics_define_no_damage_and_right_censoring() -> None:
    baseline = np.array([[10.0]])
    rate = np.array([[0.1]])
    no_damage = calculate_ecology(
        resource_stock=np.repeat(baseline[None, :, :], 2, axis=0),
        effective_capacity=np.repeat(baseline[None, :, :], 2, axis=0),
        effective_regeneration=np.repeat(rate[None, :, :], 2, axis=0),
        recovery_remaining=np.zeros((2, 1, 1), dtype=np.int64),
        baseline_capacity=baseline,
        baseline_regeneration=rate,
    )
    assert no_damage.cumulative_recovery_deficit == 0.0
    assert no_damage.recovery_spells == ()

    censored = calculate_ecology(
        resource_stock=np.array([[[10.0]], [[8.0]], [[9.0]]]),
        effective_capacity=np.array([[[10.0]], [[8.0]], [[9.0]]]),
        effective_regeneration=np.array([[[0.1]], [[0.08]], [[0.09]]]),
        recovery_remaining=np.array([[[0]], [[2]], [[1]]]),
        baseline_capacity=baseline,
        baseline_regeneration=rate,
    )
    assert censored.recovery_spells[0].right_censored is True
    assert censored.completed_mean_recovery_duration == 0.0


def test_ecology_metrics_reject_shape_and_physical_bound_errors() -> None:
    valid = {
        "resource_stock": np.array([[[1.0]]]),
        "effective_capacity": np.array([[[1.0]]]),
        "effective_regeneration": np.array([[[0.1]]]),
        "recovery_remaining": np.array([[[0]]]),
        "baseline_capacity": np.array([[1.0]]),
        "baseline_regeneration": np.array([[0.1]]),
    }
    with pytest.raises(ValueError, match="same three-dimensional shape"):
        calculate_ecology(**{**valid, "resource_stock": np.ones((1, 2, 1))})
    with pytest.raises(ValueError, match="baseline capacity"):
        calculate_ecology(**{**valid, "resource_stock": np.array([[[2.0]]])})
