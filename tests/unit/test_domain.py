from dataclasses import FrozenInstanceError

import numpy as np
import pytest
from numpy.typing import NDArray

from social_cybernetics.domain import (
    ActionIntent,
    ActionKind,
    AgentSnapshot,
    AgentState,
    AgentTransitionRecord,
    BeliefState,
    DamageParameters,
    GateDecision,
    InvariantViolationError,
    Observation,
    RecoveryState,
    ShockEventState,
    ShockEventStatus,
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
    regenerate,
    relax_resources,
    resolve_actions,
    start_correlated_event,
    von_neumann_neighbors,
)


def snapshot(agent_id: int = 1, energy: float = 10.0) -> AgentSnapshot:
    return AgentSnapshot(
        tick=0,
        agent_id=agent_id,
        position=(1, 1),
        energy=energy,
        alive=True,
    )


def test_agent_transition_record_is_immutable_and_reconstructs_one_active_tick() -> None:
    transition = AgentTransitionRecord(
        tick=1,
        agent_id=7,
        origin=(1, 1),
        observed_stock=3.0,
        believed_stock=3.0,
        intent_kind=ActionKind.HARVEST,
        requested_amount=2.0,
        intended_destination=None,
        gate_allowed=True,
        harvested=1.5,
        moved=False,
        final_position=(1, 1),
        energy_before=10.0,
        energy_after=10.5,
        shortfall=0.0,
        died=False,
    )

    assert transition.observed_stock == transition.believed_stock == 3.0
    assert transition.requested_amount == 2.0
    assert transition.harvested == 1.5
    assert transition.origin == transition.final_position
    with pytest.raises(FrozenInstanceError):
        transition.energy_after = 0.0  # type: ignore[misc]


def test_relaxation_regeneration_returns_a_bounded_copy() -> None:
    stock = np.array([[0.0, 5.0], [10.0, 8.0]])
    capacity = np.full((2, 2), 10.0)

    updated = regenerate(stock, capacity, rate=0.1)

    np.testing.assert_allclose(updated, [[1.0, 5.5], [10.0, 8.2]])
    np.testing.assert_array_equal(stock, [[0.0, 5.0], [10.0, 8.0]])


def test_resource_initialization_builds_uniform_independent_float_arrays() -> None:
    stock, capacity = initialize_resources((2, 3), initial_stock=4.0, capacity=10.0)

    np.testing.assert_array_equal(stock, np.full((2, 3), 4.0))
    np.testing.assert_array_equal(capacity, np.full((2, 3), 10.0))
    assert stock.dtype == capacity.dtype == np.float64
    assert not np.shares_memory(stock, capacity)


def test_resource_initialization_preserves_explicit_xy_orientation() -> None:
    configured_capacity = ((4.0, 8.0), (6.0, 10.0), (2.0, 12.0))
    configured_stock = ((2.0, 8.0), (3.0, 5.0), (1.0, 6.0))

    stock, capacity = initialize_resources(
        (3, 2), initial_stock=configured_stock, capacity=configured_capacity
    )

    np.testing.assert_array_equal(capacity, configured_capacity)
    np.testing.assert_array_equal(stock, configured_stock)
    capacity[0, 0] = 99.0
    assert configured_capacity[0][0] == 4.0


def test_resource_initialization_rejects_wrong_shape_or_mixed_representations() -> None:
    with pytest.raises(InvariantViolationError, match="configured world"):
        initialize_resources((2, 2), initial_stock=((1.0,),), capacity=((2.0,),))
    with pytest.raises(InvariantViolationError, match="both be scalars or both be matrices"):
        initialize_resources((1, 1), initial_stock=1.0, capacity=((2.0,),))


def test_resource_and_regeneration_invariants_reject_invalid_inputs() -> None:
    with pytest.raises(InvariantViolationError, match="two positive dimensions"):
        initialize_resources((0, 1), initial_stock=0.0, capacity=1.0)
    with pytest.raises(InvariantViolationError, match="only finite"):
        initialize_resources((1, 1), initial_stock=np.nan, capacity=1.0)
    with pytest.raises(InvariantViolationError, match="between zero and capacity"):
        initialize_resources((1, 1), initial_stock=2.0, capacity=1.0)
    with pytest.raises(InvariantViolationError, match="finite and in"):
        regenerate(np.array([[0.0]]), np.array([[1.0]]), rate=1.1)


def test_recovery_state_invariants_reject_malformed_arrays() -> None:
    capacity = np.array([[10.0]])
    rate = np.array([[0.2]])

    with pytest.raises(InvariantViolationError, match="finite nonnegative"):
        initialize_recovery_state(np.array([[-1.0]]), rate)
    with pytest.raises(InvariantViolationError, match="match the 2D"):
        initialize_recovery_state(capacity, np.array([0.2]))
    with pytest.raises(InvariantViolationError, match="finite and in"):
        initialize_recovery_state(capacity, np.array([[1.1]]))

    wrong_shape = RecoveryState.create(
        np.ones((1, 2)),
        np.zeros((1, 2)),
        np.zeros((1, 2), dtype=np.int64),
        np.zeros((1, 2)),
        np.zeros((1, 2)),
    )
    with pytest.raises(InvariantViolationError, match="match baseline"):
        apply_recovery(wrong_shape, capacity, rate)

    nonfinite = RecoveryState.create(
        np.array([[np.nan]]),
        rate,
        np.zeros((1, 1), dtype=np.int64),
        np.zeros((1, 1)),
        np.zeros((1, 1)),
    )
    with pytest.raises(InvariantViolationError, match="finite values"):
        apply_recovery(nonfinite, capacity, rate)

    out_of_bounds = RecoveryState.create(
        np.array([[11.0]]),
        rate,
        np.zeros((1, 1), dtype=np.int64),
        np.zeros((1, 1)),
        np.zeros((1, 1)),
    )
    with pytest.raises(InvariantViolationError, match="physical bounds"):
        apply_recovery(out_of_bounds, capacity, rate)


def test_recovery_state_starts_at_immutable_baselines() -> None:
    capacity = np.array([[10.0, 8.0]])
    rate = np.array([[0.2, 0.1]])

    state = initialize_recovery_state(capacity, rate)
    capacity[0, 0] = 99.0
    rate[0, 0] = 99.0

    np.testing.assert_array_equal(state.effective_capacity, [[10.0, 8.0]])
    np.testing.assert_array_equal(state.effective_regeneration, [[0.2, 0.1]])
    np.testing.assert_array_equal(state.remaining_ticks, [[0, 0]])
    with pytest.raises(ValueError, match="read-only"):
        state.effective_capacity[0, 0] = 0.0


def test_simultaneous_damage_compounds_once_and_records_one_application() -> None:
    baseline_capacity = np.array([[10.0]])
    baseline_rate = np.array([[0.2]])
    recovery = initialize_recovery_state(baseline_capacity, baseline_rate)
    parameters = DamageParameters(
        stock_loss_fraction=0.5,
        capacity_loss_fraction=0.2,
        regeneration_suppression_fraction=0.5,
        recovery_ticks=4,
    )

    batch = apply_simultaneous_damage(
        np.array([[8.0]]),
        recovery,
        baseline_capacity,
        baseline_rate,
        hits={(0, 0): (5, 2)},
        parameters=parameters,
        tick=3,
    )

    np.testing.assert_allclose(batch.resource_stock, [[2.0]])
    np.testing.assert_allclose(batch.recovery.effective_capacity, [[6.4]])
    np.testing.assert_allclose(batch.recovery.effective_regeneration, [[0.05]])
    np.testing.assert_array_equal(batch.recovery.remaining_ticks, [[4]])
    np.testing.assert_allclose(batch.recovery.capacity_increment, [[0.9]])
    np.testing.assert_allclose(batch.recovery.regeneration_increment, [[0.0375]])
    assert len(batch.applications) == 1
    application = batch.applications[0]
    assert application.event_ids == (2, 5)
    assert application.combined_stock_multiplier == pytest.approx(0.25)
    assert application.combined_capacity_multiplier == pytest.approx(0.64)
    assert application.combined_regeneration_multiplier == pytest.approx(0.25)
    assert application.pre_stock == 8.0
    assert application.post_stock == 2.0
    assert application.recovery_completion_tick == 7


def test_linear_recovery_reaches_exact_baseline_and_a_new_hit_restarts_it() -> None:
    baseline_capacity = np.array([[10.0]])
    baseline_rate = np.array([[0.2]])
    parameters = DamageParameters(0.0, 0.5, 0.5, 4)
    damaged = apply_simultaneous_damage(
        np.array([[8.0]]),
        initialize_recovery_state(baseline_capacity, baseline_rate),
        baseline_capacity,
        baseline_rate,
        hits={(0, 0): (1,)},
        parameters=parameters,
        tick=0,
    )

    after_two = apply_recovery(
        apply_recovery(damaged.recovery, baseline_capacity, baseline_rate),
        baseline_capacity,
        baseline_rate,
    )
    np.testing.assert_allclose(after_two.effective_capacity, [[7.5]])
    np.testing.assert_allclose(after_two.effective_regeneration, [[0.15]])

    redamaged = apply_simultaneous_damage(
        damaged.resource_stock,
        after_two,
        baseline_capacity,
        baseline_rate,
        hits={(0, 0): (2,)},
        parameters=parameters,
        tick=2,
    )
    np.testing.assert_allclose(redamaged.recovery.effective_capacity, [[3.75]])
    np.testing.assert_array_equal(redamaged.recovery.remaining_ticks, [[4]])

    recovered = redamaged.recovery
    for _ in range(4):
        recovered = apply_recovery(recovered, baseline_capacity, baseline_rate)
    np.testing.assert_array_equal(recovered.effective_capacity, baseline_capacity)
    np.testing.assert_array_equal(recovered.effective_regeneration, baseline_rate)
    np.testing.assert_array_equal(recovered.remaining_ticks, [[0]])


def test_tiny_damage_recovery_cannot_overshoot_baseline_by_one_ulp() -> None:
    baseline_capacity = np.array([[0.0]])
    baseline_rate = np.array([[0.046875]])
    damaged = apply_simultaneous_damage(
        baseline_capacity,
        initialize_recovery_state(baseline_capacity, baseline_rate),
        baseline_capacity,
        baseline_rate,
        hits={(0, 0): (1, 2)},
        parameters=DamageParameters(0.0, 0.0, 2.220446049250313e-16, 5),
        tick=0,
    )

    recovered = damaged.recovery
    for _ in range(5):
        recovered = apply_recovery(recovered, baseline_capacity, baseline_rate)

    np.testing.assert_array_equal(recovered.effective_regeneration, baseline_rate)
    np.testing.assert_array_equal(recovered.remaining_ticks, [[0]])


def test_signed_relaxation_allows_temporary_effective_capacity_overshoot() -> None:
    updated = relax_resources(
        np.array([[8.0, 2.0]]),
        effective_capacity=np.array([[5.0, 5.0]]),
        effective_regeneration=np.array([[0.2, 0.2]]),
        baseline_capacity=np.array([[10.0, 10.0]]),
    )

    np.testing.assert_allclose(updated, [[7.4, 2.6]])


def test_signed_relaxation_rejects_mismatched_nonfinite_or_unbounded_ecology() -> None:
    valid = np.array([[1.0]])
    with pytest.raises(InvariantViolationError, match="equal shapes"):
        relax_resources(
            valid,
            effective_capacity=np.array([[1.0, 1.0]]),
            effective_regeneration=valid,
            baseline_capacity=valid,
        )
    with pytest.raises(InvariantViolationError, match="finite and two-dimensional"):
        relax_resources(
            np.array([[np.nan]]),
            effective_capacity=valid,
            effective_regeneration=valid,
            baseline_capacity=valid,
        )
    with pytest.raises(InvariantViolationError, match="physical bounds"):
        relax_resources(
            np.array([[2.0]]),
            effective_capacity=valid,
            effective_regeneration=valid,
            baseline_capacity=valid,
        )


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        (DamageParameters(-0.1, 0.0, 0.0, 1), "damage fractions"),
        (DamageParameters(0.0, 0.0, 0.0, 0), "recovery_ticks"),
    ],
)
def test_damage_rejects_invalid_parameters(parameters: DamageParameters, message: str) -> None:
    capacity = np.array([[1.0]])
    rate = np.array([[0.1]])
    with pytest.raises(InvariantViolationError, match=message):
        apply_simultaneous_damage(
            capacity,
            initialize_recovery_state(capacity, rate),
            capacity,
            rate,
            hits={(0, 0): (1,)},
            parameters=parameters,
            tick=0,
        )


@pytest.mark.parametrize(
    ("tick", "stock", "hits", "message"),
    [
        (-1, np.array([[1.0]]), {(0, 0): (1,)}, "tick cannot be negative"),
        (0, np.array([[np.nan]]), {(0, 0): (1,)}, "finite baseline"),
        (0, np.array([[2.0]]), {(0, 0): (1,)}, "within baseline"),
        (0, np.array([[1.0]]), {(1, 0): (1,)}, "outside the world"),
        (0, np.array([[1.0]]), {(0, 0): ()}, "positive event IDs"),
        (0, np.array([[1.0]]), {(0, 0): (1, 1)}, "same event hit twice"),
    ],
)
def test_damage_rejects_invalid_state_or_hit_evidence(
    tick: int,
    stock: NDArray[np.float64],
    hits: dict[tuple[int, int], tuple[int, ...]],
    message: str,
) -> None:
    capacity = np.array([[1.0]])
    rate = np.array([[0.1]])
    with pytest.raises(InvariantViolationError, match=message):
        apply_simultaneous_damage(
            stock,
            initialize_recovery_state(capacity, rate),
            capacity,
            rate,
            hits=hits,
            parameters=DamageParameters(0.0, 0.0, 0.0, 1),
            tick=tick,
        )


def test_von_neumann_neighbors_are_unique_and_respect_torus_geometry() -> None:
    assert von_neumann_neighbors((0, 0), (3, 2), torus=False) == ((0, 1), (1, 0))
    assert von_neumann_neighbors((0, 0), (3, 2), torus=True) == (
        (0, 1),
        (1, 0),
        (2, 0),
    )
    assert von_neumann_neighbors((0, 0), (1, 1), torus=True) == ()


def test_neighborhood_and_event_construction_reject_invalid_inputs() -> None:
    with pytest.raises(InvariantViolationError, match="two positive dimensions"):
        von_neumann_neighbors((0, 0), (0, 1), torus=False)
    with pytest.raises(InvariantViolationError, match="outside the world"):
        von_neumann_neighbors((1, 0), (1, 1), torus=False)
    with pytest.raises(InvariantViolationError, match="event ID"):
        start_correlated_event(0, 0, (0, 0), 0.5, 1)
    with pytest.raises(InvariantViolationError, match="spread_probability"):
        start_correlated_event(1, 0, (0, 0), np.nan, 1)
    with pytest.raises(InvariantViolationError, match="max_spread_ticks"):
        start_correlated_event(1, 0, (0, 0), 0.5, -1)


def test_zero_round_correlated_event_terminates_at_its_epicenter() -> None:
    event = start_correlated_event(
        event_id=1,
        tick=4,
        epicenter=(2, 3),
        spread_probability=1.0,
        max_spread_ticks=0,
    )

    assert event.status is ShockEventStatus.TERMINATED
    assert event.termination_reason is ShockTerminationReason.MAX_SPREAD_TICKS
    assert event.frontier == frozenset({(2, 3)})
    assert event.affected == frozenset({(2, 3)})
    assert event.spread_rounds_completed == 0


def test_wavefront_zero_probability_records_failed_exposures_and_exhausts() -> None:
    event = start_correlated_event(1, 0, (1, 1), 0.0, 3)

    result = advance_correlated_event(
        event,
        tick=1,
        shape=(3, 3),
        torus=False,
        rng=np.random.default_rng(1),
    )

    assert result.event.status is ShockEventStatus.TERMINATED
    assert result.event.termination_reason is ShockTerminationReason.FRONTIER_EXHAUSTED
    assert result.newly_affected == ()
    assert len(result.exposures) == 4
    assert all(exposure.exposing_neighbors == ((1, 1),) for exposure in result.exposures)
    assert all(exposure.successful_neighbors == () for exposure in result.exposures)
    assert all(exposure.transmitted is False for exposure in result.exposures)


def test_wavefront_full_probability_spreads_synchronously_to_round_limit() -> None:
    event = start_correlated_event(1, 0, (1, 1), 1.0, 1)

    result = advance_correlated_event(
        event,
        tick=1,
        shape=(3, 3),
        torus=False,
        rng=np.random.default_rng(1),
    )

    expected = ((0, 1), (1, 0), (1, 2), (2, 1))
    assert result.newly_affected == expected
    assert result.event.frontier == frozenset(expected)
    assert result.event.affected == frozenset({(1, 1), *expected})
    assert result.event.spread_rounds_completed == 1
    assert result.event.status is ShockEventStatus.TERMINATED
    assert result.event.termination_reason is ShockTerminationReason.MAX_SPREAD_TICKS
    assert all(exposure.transmitted for exposure in result.exposures)


def test_wavefront_records_all_and_successful_sources_per_target() -> None:
    event = ShockEventState.create(
        event_id=7,
        initiation_tick=0,
        epicenter=(0, 0),
        frontier={(0, 1), (1, 0)},
        affected={(0, 0), (0, 1), (1, 0)},
        spread_rounds_completed=1,
        spread_probability=1.0,
        max_spread_ticks=3,
    )

    result = advance_correlated_event(
        event,
        tick=2,
        shape=(3, 3),
        torus=False,
        rng=np.random.default_rng(1),
    )
    shared_target = next(item for item in result.exposures if item.position == (1, 1))

    assert shared_target.exposing_neighbors == ((0, 1), (1, 0))
    assert shared_target.successful_neighbors == ((0, 1), (1, 0))
    assert shared_target.transmitted is True


def test_wavefront_rejects_terminated_events_and_illegal_tick_or_round() -> None:
    terminated = start_correlated_event(1, 0, (0, 0), 1.0, 0)
    with pytest.raises(InvariantViolationError, match="only active"):
        advance_correlated_event(
            terminated,
            tick=1,
            shape=(2, 2),
            torus=False,
            rng=np.random.default_rng(1),
        )

    active = start_correlated_event(2, 3, (0, 0), 1.0, 1)
    with pytest.raises(InvariantViolationError, match="requested tick or round"):
        advance_correlated_event(
            active,
            tick=3,
            shape=(2, 2),
            torus=False,
            rng=np.random.default_rng(1),
        )


def test_scope_hazard_draws_have_explicit_zero_and_one_controls() -> None:
    rng = np.random.default_rng(7)

    assert draw_event(0.0, rng) is False
    assert draw_event(1.0, rng) is True
    assert draw_independent_hits((2, 2), 0.0, rng) == ()
    assert draw_independent_hits((2, 2), 1.0, rng) == (
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    )


def test_scope_hazard_draws_validate_inputs_and_cover_stochastic_paths() -> None:
    first = np.random.default_rng(11)
    second = np.random.default_rng(11)
    assert draw_event(0.5, first) == draw_event(0.5, second)
    assert draw_independent_hits((2, 2), 0.5, first) == draw_independent_hits((2, 2), 0.5, second)
    with pytest.raises(InvariantViolationError, match="event_probability"):
        draw_event(-0.1, first)
    with pytest.raises(InvariantViolationError, match="two positive dimensions"):
        draw_independent_hits((0, 1), 0.5, first)
    with pytest.raises(InvariantViolationError, match="event_probability"):
        draw_independent_hits((1, 1), 1.1, first)
    with pytest.raises(InvariantViolationError, match="two positive dimensions"):
        draw_uniform_position((1, 0), first)


def test_uniform_position_draw_is_seeded_and_within_xy_shape() -> None:
    first = np.random.default_rng(42)
    second = np.random.default_rng(42)

    positions = tuple(draw_uniform_position((3, 2), first) for _ in range(20))

    assert positions == tuple(draw_uniform_position((3, 2), second) for _ in range(20))
    assert all(0 <= x < 3 and 0 <= y < 2 for x, y in positions)


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
        snapshot(),
        belief,
        ((0, 1), (2, 1)),
        harvest_threshold=1.0,
        harvest_capacity=2.0,
        rng=rng,
    )

    assert intent == ActionIntent.harvest(agent_id=1, position=(1, 1), amount=2.0)


def test_literal_policy_moves_uniformly_when_stock_is_below_threshold() -> None:
    belief = BeliefState(agent_id=1, believed_local_stock=0.5)

    intent = literal_local_policy(
        snapshot(),
        belief,
        ((0, 1), (2, 1)),
        harvest_threshold=1.0,
        harvest_capacity=2.0,
        rng=np.random.default_rng(2),
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
        AgentState(agent_id=1, energy=1.5),
        harvested=1.0,
        moved=True,
        conversion_efficiency=1.0,
        basal_cost=1.0,
        movement_cost=0.25,
    )
    assert alive.energy == pytest.approx(1.25)
    assert alive.alive is True
    assert died is False

    dead, died = apply_metabolism(
        AgentState(agent_id=1, energy=0.1),
        harvested=0.0,
        moved=True,
        conversion_efficiency=1.0,
        basal_cost=1.0,
        movement_cost=0.25,
    )
    assert dead.energy == 0.0
    assert dead.alive is False
    assert died is True


@pytest.mark.parametrize(
    ("stock", "capacity", "rate"),
    [
        (np.zeros((2, 2)), np.zeros((3, 3)), 0.1),
        (np.array([[-1.0]]), np.array([[1.0]]), 0.1),
        (np.array([[2.0]]), np.array([[1.0]]), 0.1),
        (np.array([[np.nan]]), np.array([[1.0]]), 0.1),
        (np.array([[0.0]]), np.array([[1.0]]), -0.1),
    ],
)
def test_regeneration_rejects_invalid_physical_state(
    stock: np.ndarray, capacity: np.ndarray, rate: float
) -> None:
    with pytest.raises(InvariantViolationError):
        regenerate(stock, capacity, rate)


def test_observation_policy_and_physiology_reject_invalid_inputs() -> None:
    with pytest.raises(InvariantViolationError):
        direct_observation(snapshot(), -1)
    with pytest.raises(InvariantViolationError):
        literal_local_policy(
            snapshot(),
            BeliefState(agent_id=2, believed_local_stock=1),
            ((0, 1),),
            harvest_threshold=1,
            harvest_capacity=2,
            rng=np.random.default_rng(1),
        )
    with pytest.raises(InvariantViolationError):
        literal_local_policy(
            snapshot(),
            BeliefState(agent_id=1, believed_local_stock=0),
            (),
            harvest_threshold=1,
            harvest_capacity=2,
            rng=np.random.default_rng(1),
        )
    with pytest.raises(InvariantViolationError):
        literal_local_policy(
            snapshot(),
            BeliefState(agent_id=1, believed_local_stock=1),
            ((0, 1),),
            harvest_threshold=-1,
            harvest_capacity=2,
            rng=np.random.default_rng(1),
        )
    with pytest.raises(InvariantViolationError):
        apply_metabolism(
            AgentState(agent_id=1, energy=1),
            harvested=-1,
            moved=False,
            conversion_efficiency=1,
            basal_cost=1,
            movement_cost=0.25,
        )
    with pytest.raises(InvariantViolationError):
        apply_metabolism(
            AgentState(agent_id=1, energy=0, alive=False),
            harvested=2,
            moved=False,
            conversion_efficiency=1,
            basal_cost=1,
            movement_cost=0.25,
        )


@pytest.mark.parametrize(
    "stock",
    [np.array([1.0]), np.array([[-1.0]]), np.array([[np.inf]])],
)
def test_resolution_rejects_invalid_resource_arrays(stock: np.ndarray) -> None:
    with pytest.raises(InvariantViolationError):
        resolve_actions(stock, ())


def test_resolution_rejects_malformed_or_duplicate_decisions() -> None:
    stock = np.ones((2, 2))
    harvest = ActionIntent.harvest(1, (0, 0), 1)
    malformed = (
        GateDecision(agent_id=2, allowed=True, intent=harvest),
        GateDecision(agent_id=1, allowed=True, intent=harvest),
    )
    with pytest.raises(InvariantViolationError):
        resolve_actions(stock, malformed)

    duplicate = (allow_all(harvest), allow_all(harvest))
    with pytest.raises(InvariantViolationError):
        resolve_actions(stock, duplicate)


@pytest.mark.parametrize(
    "intent",
    [
        ActionIntent.harvest(1, (2, 0), 1),
        ActionIntent.harvest(1, (0, 0), -1),
        ActionIntent(1, ActionKind.MOVE, (0, 0)),
        ActionIntent.move(1, (0, 0), (2, 0)),
    ],
)
def test_resolution_rejects_invalid_intents(intent: ActionIntent) -> None:
    with pytest.raises(InvariantViolationError):
        resolve_actions(np.ones((2, 2)), (allow_all(intent),))


def test_resolution_records_rejected_and_rest_actions_without_side_effects() -> None:
    rejected_intent = ActionIntent.harvest(1, (0, 0), 1)
    rest_intent = ActionIntent(2, ActionKind.REST, (0, 0))
    decisions = (
        GateDecision(1, False, rejected_intent, "fixture"),
        allow_all(rest_intent),
    )

    result = resolve_actions(np.ones((1, 1)), decisions)

    assert result.resource_stock[0, 0] == 1
    assert result.by_agent[1].rejected is True
    assert result.by_agent[2].kind is ActionKind.REST
