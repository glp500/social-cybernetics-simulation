from dataclasses import replace

import pytest

from social_cybernetics.analysis import calculate_subsistence_security
from social_cybernetics.domain import ActionKind, AgentTransitionRecord


def transition(
    agent_id: int,
    tick: int,
    *,
    shortfall: float,
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
        harvested=0.0,
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
