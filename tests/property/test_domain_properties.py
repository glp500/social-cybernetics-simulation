import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from social_cybernetics.domain import ActionIntent, allow_all, regenerate, resolve_actions


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
