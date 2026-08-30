import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from social_cybernetics.metrics import (
    RankedShare,
    bottom_fraction_burden_share,
    gini,
    top_fraction_share,
)


def test_gini_zero_for_equal_values() -> None:
    assert gini([1, 1, 1, 1]) == 0.0


def test_gini_positive_for_unequal_values() -> None:
    assert gini([0, 0, 0, 10]) > 0.0


def test_gini_zero_for_empty_input() -> None:
    assert gini([]) == 0.0


def test_gini_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        gini([1, -1, 2])


@pytest.mark.parametrize("values", [[1.0, float("nan")], [[1.0, 2.0]]])
def test_gini_rejects_nonfinite_or_nonvector_inputs(values: list[object]) -> None:
    with pytest.raises(ValueError):
        gini(values)  # type: ignore[arg-type]


def test_top_fraction_share_uses_a_ceiling_sized_group() -> None:
    result = top_fraction_share([1.0, 2.0, 3.0, 4.0], 0.10)

    assert result == RankedShare(value=0.4, group_size=1, cutoff_tie_count=1)


def test_bottom_burden_share_uses_explicit_identifiers_to_break_rank_ties() -> None:
    first = bottom_fraction_burden_share(
        burdens=[9.0, 1.0, 0.0, 0.0],
        ranking=[0.0, 0.0, 1.0, 2.0],
        fraction=0.25,
        identifiers=[4, 3, 2, 1],
    )
    reordered = bottom_fraction_burden_share(
        burdens=[0.0, 9.0, 0.0, 1.0],
        ranking=[1.0, 0.0, 2.0, 0.0],
        fraction=0.25,
        identifiers=[2, 4, 1, 3],
    )

    assert first == reordered == RankedShare(value=0.1, group_size=1, cutoff_tie_count=2)


def test_ranked_shares_define_empty_and_zero_total_inputs() -> None:
    assert top_fraction_share([], 0.1) == RankedShare(0.0, 0, 0)
    assert bottom_fraction_burden_share([], [], 0.25) == RankedShare(0.0, 0, 0)
    assert top_fraction_share([0.0, 0.0], 0.5).value == 0.0


@pytest.mark.parametrize("fraction", [0.0, -0.1, 1.1, float("nan"), True])
def test_ranked_shares_reject_invalid_fractions(fraction: object) -> None:
    with pytest.raises(ValueError):
        top_fraction_share([1.0], fraction)  # type: ignore[arg-type]


@given(
    st.lists(
        st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        max_size=30,
    )
)
def test_gini_is_order_independent(values: list[float]) -> None:
    assert gini(values) == pytest.approx(gini(list(reversed(values))))
    assert np.isfinite(gini(values))
