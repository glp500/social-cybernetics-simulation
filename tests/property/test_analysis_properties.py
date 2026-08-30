import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from social_cybernetics.analysis import (
    calculate_distribution,
    calculate_ecology,
    calculate_persistence,
)
from social_cybernetics.domain import (
    ActionKind,
    AgentSnapshot,
    AgentTransitionRecord,
    CohortRecord,
)


def _records(harvests: list[float], agent_count: int) -> tuple[AgentTransitionRecord, ...]:
    return tuple(
        AgentTransitionRecord(
            tick=tick,
            agent_id=agent_id,
            origin=(agent_id, 0),
            observed_stock=harvested,
            believed_stock=harvested,
            intent_kind=ActionKind.HARVEST,
            requested_amount=harvested,
            intended_destination=None,
            gate_allowed=True,
            harvested=harvested,
            moved=False,
            final_position=(agent_id, 0),
            energy_before=10.0,
            energy_after=10.0,
            shortfall=0.0,
            died=False,
        )
        for tick in (1, 2, 3)
        for agent_id, harvested in enumerate(
            harvests[(tick - 1) * agent_count : tick * agent_count]
        )
    )


def _cohort(agent_count: int) -> tuple[CohortRecord, ...]:
    return tuple(
        CohortRecord(tick, AgentSnapshot(tick, agent_id, (agent_id, 0), 10.0, True))
        for tick in range(4)
        for agent_id in range(agent_count)
    )


@given(
    agent_count=st.integers(min_value=1, max_value=8),
    data=st.data(),
)
def test_distribution_and_persistence_are_record_order_independent(
    agent_count: int, data: st.DataObject
) -> None:
    harvests = data.draw(
        st.lists(
            st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
            min_size=agent_count * 3,
            max_size=agent_count * 3,
        )
    )
    records = _records(harvests, agent_count)
    cohort = _cohort(agent_count)

    forward_distribution = calculate_distribution(records, cohort, completed_ticks=3)
    reverse_distribution = calculate_distribution(
        tuple(reversed(records)), tuple(reversed(cohort)), completed_ticks=3
    )
    forward_persistence = calculate_persistence(records, cohort, completed_ticks=3)
    reverse_persistence = calculate_persistence(
        tuple(reversed(records)), tuple(reversed(cohort)), completed_ticks=3
    )

    assert forward_distribution == reverse_distribution
    assert forward_persistence == reverse_persistence
    assert 0 <= forward_distribution.harvest_gini <= 1
    assert 0 <= forward_distribution.top_10_percent_harvest_share.value <= 1


@given(
    stock_factors=st.lists(
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=4,
        max_size=4,
    ),
    capacity_factors=st.lists(
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=4,
        max_size=4,
    ),
    regeneration_factors=st.lists(
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=4,
        max_size=4,
    ),
)
def test_ecological_deficits_are_finite_and_bounded(
    stock_factors: list[float],
    capacity_factors: list[float],
    regeneration_factors: list[float],
) -> None:
    baseline_capacity = np.array([[5.0, 10.0], [15.0, 20.0]])
    baseline_regeneration = np.full((2, 2), 0.2)
    stock = np.stack([baseline_capacity * factor for factor in stock_factors])
    capacity = np.stack([baseline_capacity * factor for factor in capacity_factors])
    regeneration = np.stack([baseline_regeneration * factor for factor in regeneration_factors])
    metrics = calculate_ecology(
        resource_stock=stock,
        effective_capacity=capacity,
        effective_regeneration=regeneration,
        recovery_remaining=np.zeros((4, 2, 2), dtype=np.int64),
        baseline_capacity=baseline_capacity,
        baseline_regeneration=baseline_regeneration,
    )

    for summary in (
        metrics.resource_depletion,
        metrics.capacity_deficit,
        metrics.regeneration_deficit,
    ):
        assert all(np.isfinite(value) and 0 <= value <= 1 for value in summary.values)
    assert (
        metrics.cumulative_recovery_deficit
        == (metrics.cumulative_capacity_deficit + metrics.cumulative_regeneration_deficit) / 2
    )
