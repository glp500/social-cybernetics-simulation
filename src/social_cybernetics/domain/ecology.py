"""Pure resource dynamics and invariant checks."""

import numpy as np

from .types import FloatArray


class InvariantViolationError(ValueError):
    """Raised when a scientific state violates a physical invariant."""


def validate_resource_arrays(stock: FloatArray, capacity: FloatArray) -> None:
    if stock.shape != capacity.shape or stock.ndim != 2:
        raise InvariantViolationError("resource stock and capacity must be equal-shaped 2D arrays")
    if not np.isfinite(stock).all() or not np.isfinite(capacity).all():
        raise InvariantViolationError("resource arrays must contain only finite values")
    if (stock < 0).any() or (capacity < 0).any() or (stock > capacity).any():
        raise InvariantViolationError("resource stock must remain between zero and capacity")


def regenerate(stock: FloatArray, capacity: FloatArray, rate: float) -> FloatArray:
    """Apply relaxation regeneration without mutating either input array."""

    stock_array = np.asarray(stock, dtype=np.float64)
    capacity_array = np.asarray(capacity, dtype=np.float64)
    validate_resource_arrays(stock_array, capacity_array)
    if not np.isfinite(rate) or not 0 <= rate <= 1:
        raise InvariantViolationError("regeneration rate must be finite and in [0, 1]")
    updated = stock_array + rate * (capacity_array - stock_array)
    updated = np.clip(updated, 0.0, capacity_array)
    validate_resource_arrays(updated, capacity_array)
    return updated
