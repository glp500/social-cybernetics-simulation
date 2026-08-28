from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from social_cybernetics.domain import (
    ActionIntent,
    ActionKind,
    AgentSnapshot,
    AgentState,
    BeliefState,
    GateDecision,
    Observation,
    allow_all,
    apply_metabolism,
    copy_observation,
    direct_observation,
    literal_local_policy,
    regenerate,
    resolve_actions,
)


def snapshot(agent_id: int = 1, energy: float = 10.0) -> AgentSnapshot:
    return AgentSnapshot(
        tick=0,
        agent_id=agent_id,
        position=(1, 1),
        energy=energy,
        alive=True,
    )


def test_relaxation_regeneration_returns_a_bounded_copy() -> None:
    stock = np.array([[0.0, 5.0], [10.0, 8.0]])
    capacity = np.full((2, 2), 10.0)

    updated = regenerate(stock, capacity, rate=0.1)

    np.testing.assert_allclose(updated, [[1.0, 5.5], [10.0, 8.2]])
    np.testing.assert_array_equal(stock, [[0.0, 5.0], [10.0, 8.0]])


def test_direct_observation_and_belief_are_isolated_values() -> None:
    observation = direct_observation(snapshot(), local_stock=7.5)
    belief = copy_observation(observation)

    assert observation == Observation(agent_id=1, position=(1, 1), local_stock=7.5)
    assert belief == BeliefState(agent_id=1, believed_local_stock=7.5)
    assert belief is not observation


def test_literal_policy_harvests_at_threshold_without_using_rng() -> None:
    belief = BeliefState(agent_id=1, believed_local_stock=1.0)
    rng = np.random.default_rng(42)

    intent = literal_local_policy(
        snapshot(), belief, ((0, 1), (2, 1)), harvest_threshold=1.0,
        harvest_capacity=2.0, rng=rng,
    )

    assert intent == ActionIntent.harvest(agent_id=1, position=(1, 1), amount=2.0)


def test_literal_policy_moves_uniformly_when_stock_is_below_threshold() -> None:
    belief = BeliefState(agent_id=1, believed_local_stock=0.5)

    intent = literal_local_policy(
        snapshot(), belief, ((0, 1), (2, 1)), harvest_threshold=1.0,
        harvest_capacity=2.0, rng=np.random.default_rng(2),
    )

    assert intent.kind is ActionKind.MOVE
    assert intent.destination in {(0, 1), (2, 1)}


def test_intents_are_immutable_and_allow_all_gate_copies_the_intent() -> None:
    intent = ActionIntent.harvest(agent_id=1, position=(1, 1), amount=2.0)
    with pytest.raises(FrozenInstanceError):
        intent.amount = 3.0  # type: ignore[misc]

    decision = allow_all(intent)
    assert decision == GateDecision(agent_id=1, allowed=True, intent=intent)


def test_contested_harvest_is_proportional_and_conservative() -> None:
    stock = np.array([[3.0]])
    decisions = (
        allow_all(ActionIntent.harvest(2, (0, 0), 4.0)),
        allow_all(ActionIntent.harvest(1, (0, 0), 2.0)),
    )

    result = resolve_actions(stock, decisions)

    assert result.resource_stock[0, 0] == pytest.approx(0.0)
    assert result.by_agent[1].harvested == pytest.approx(1.0)
    assert result.by_agent[2].harvested == pytest.approx(2.0)
    assert sum(item.harvested for item in result.by_agent.values()) == pytest.approx(3.0)


def test_resolution_is_independent_of_request_order_and_resolves_movement() -> None:
    stock = np.array([[10.0, 10.0]])
    decisions = (
        allow_all(ActionIntent.move(2, (0, 0), (0, 1))),
        allow_all(ActionIntent.harvest(1, (0, 0), 2.0)),
    )

    forward = resolve_actions(stock, decisions)
    reverse = resolve_actions(stock, tuple(reversed(decisions)))

    np.testing.assert_array_equal(forward.resource_stock, reverse.resource_stock)
    assert forward.by_agent == reverse.by_agent
    assert forward.by_agent[2].destination == (0, 1)
    assert forward.by_agent[2].moved is True


def test_metabolism_charges_basal_and_movement_and_marks_mortality() -> None:
    alive, died = apply_metabolism(
        AgentState(agent_id=1, energy=1.5), harvested=1.0, moved=True,
        conversion_efficiency=1.0, basal_cost=1.0, movement_cost=0.25,
    )
    assert alive.energy == pytest.approx(1.25)
    assert alive.alive is True
    assert died is False

    dead, died = apply_metabolism(
        AgentState(agent_id=1, energy=0.1), harvested=0.0, moved=True,
        conversion_efficiency=1.0, basal_cost=1.0, movement_cost=0.25,
    )
    assert dead.energy == 0.0
    assert dead.alive is False
    assert died is True
