from __future__ import annotations

import numpy as np


def gini(values: list[float] | np.ndarray) -> float:
    """Compute the Gini coefficient for non-negative values."""
    x = np.asarray(values, dtype=float)

    if x.size == 0:
        return 0.0

    if np.any(x < 0):
        raise ValueError("Gini input must be non-negative.")

    total = x.sum()
    if total == 0:
        return 0.0

    x = np.sort(x)
    n = x.size
    index = np.arange(1, n + 1)

    return float((2 * np.sum(index * x)) / (n * total) - (n + 1) / n)
