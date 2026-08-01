import pytest

from social_cybernetics.metrics import gini


def test_gini_zero_for_equal_values() -> None:
    assert gini([1, 1, 1, 1]) == 0.0


def test_gini_positive_for_unequal_values() -> None:
    assert gini([0, 0, 0, 10]) > 0.0


def test_gini_zero_for_empty_input() -> None:
    assert gini([]) == 0.0


def test_gini_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        gini([1, -1, 2])
