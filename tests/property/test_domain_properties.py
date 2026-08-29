import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from social_cybernetics.domain import (
    ActionIntent,
    DamageParameters,
    advance_correlated_event,
    allow_all,
    apply_recovery,
    apply_simultaneous_damage,
    initialize_recovery_state,
    initialize_resources,
    regenerate,
    relax_resources,
    resolve_actions,
    start_correlated_event,
)


@given(
    width=st.integers(min_value=1, max_value=20),
    height=st.integers(min_value=1, max_value=20),
    capacity=st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
    fraction=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
)
def test_uniform_resource_initialization_respects_shape_and_bounds(
    width: int, height: int, capacity: float, fraction: float
) -> None:
    stock, capacities = initialize_resources(
        (width, height), initial_stock=capacity * fraction, capacity=capacity
    )

    assert stock.shape == capacities.shape == (width, height)
    assert (stock >= 0).all()
    assert (stock <= capacities).all()


@given(
    stock=st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
    capacity=st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
    rate=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
)
def test_regeneration_stays_between_stock_and_capacity(
    stock: float, capacity: float, rate: float
) -> None:
    stock = min(stock, capacity)
    updated = regenerate(np.array([[stock]]), np.array([[capacity]]), rate)

    assert stock <= updated[0, 0] <= capacity


@given(
    capacity=st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
    stock_fraction=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    stock_loss=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    capacity_loss=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    rate=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    rate_loss=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    recovery_ticks=st.integers(min_value=1, max_value=20),
    hit_count=st.integers(min_value=1, max_value=5),
)
def test_compound_damage_is_bounded_accounted_and_recovers_exactly(
    capacity: float,
    stock_fraction: float,
    stock_loss: float,
    capacity_loss: float,
    rate: float,
    rate_loss: float,
    recovery_ticks: int,
    hit_count: int,
) -> None:
    baseline_capacity = np.array([[capacity]])
    baseline_rate = np.array([[rate]])
    stock = np.array([[capacity * stock_fraction]])
    parameters = DamageParameters(stock_loss, capacity_loss, rate_loss, recovery_ticks)
    event_ids = tuple(range(1, hit_count + 1))

    batch = apply_simultaneous_damage(
        stock,
        initialize_recovery_state(baseline_capacity, baseline_rate),
        baseline_capacity,
        baseline_rate,
        hits={(0, 0): tuple(reversed(event_ids))},
        parameters=parameters,
        tick=3,
    )

    assert batch.resource_stock[0, 0] == pytest.approx(stock[0, 0] * (1 - stock_loss) ** hit_count)
    assert batch.recovery.effective_capacity[0, 0] == pytest.approx(
        capacity * (1 - capacity_loss) ** hit_count
    )
    assert batch.recovery.effective_regeneration[0, 0] == pytest.approx(
        rate * (1 - rate_loss) ** hit_count
    )
    assert batch.applications[0].event_ids == event_ids
    assert 0 <= batch.resource_stock[0, 0] <= capacity

    recovered = batch.recovery
    for _ in range(recovery_ticks):
        recovered = apply_recovery(recovered, baseline_capacity, baseline_rate)
    np.testing.assert_array_equal(recovered.effective_capacity, baseline_capacity)
    np.testing.assert_array_equal(recovered.effective_regeneration, baseline_rate)


@given(
    baseline=st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
    stock_fraction=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    target_fraction=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    rate=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
)
def test_signed_relaxation_stays_between_stock_and_effective_target(
    baseline: float, stock_fraction: float, target_fraction: float, rate: float
) -> None:
    stock = baseline * stock_fraction
    target = baseline * target_fraction
    updated = relax_resources(
        np.array([[stock]]),
        effective_capacity=np.array([[target]]),
        effective_regeneration=np.array([[rate]]),
        baseline_capacity=np.array([[baseline]]),
    )[0, 0]

    tolerance = 1e-12 * max(1.0, baseline)
    assert min(stock, target) - tolerance <= updated <= max(stock, target) + tolerance
    assert -tolerance <= updated <= baseline + tolerance


@given(
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    probability=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
)
def test_wavefront_draws_are_seeded_and_every_transmission_has_a_frontier_source(
    seed: int, probability: float
) -> None:
    event = start_correlated_event(1, 0, (1, 1), probability, 1)
    first = advance_correlated_event(
        event,
        tick=1,
        shape=(3, 3),
        torus=True,
        rng=np.random.default_rng(seed),
    )
    second = advance_correlated_event(
        event,
        tick=1,
        shape=(3, 3),
        torus=True,
        rng=np.random.default_rng(seed),
    )

    assert first == second
    assert all(exposure.exposing_neighbors for exposure in first.exposures)
    assert all(
        set(exposure.successful_neighbors) <= set(exposure.exposing_neighbors)
        for exposure in first.exposures
    )


@given(
    available=st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
    requests=st.lists(
        st.floats(min_value=0, max_value=1_000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    ),
)
def test_harvest_never_creates_resources(available: float, requests: list[float]) -> None:
    decisions = tuple(
        allow_all(ActionIntent.harvest(index, (0, 0), amount))
        for index, amount in enumerate(requests)
    )

    result = resolve_actions(np.array([[available]]), decisions)
    harvested = sum(item.harvested for item in result.by_agent.values())

    assert harvested <= available + 1e-9
    assert result.resource_stock[0, 0] >= 0
    assert harvested + result.resource_stock[0, 0] == pytest.approx(available)
