from hypothesis import given
from hypothesis import strategies as st

from social_cybernetics.analysis import calculate_distribution, calculate_persistence
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
