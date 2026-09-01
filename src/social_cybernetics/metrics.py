"""Small public distribution metrics shared by runtime and Project 1 analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class RankedShare:
    """A fixed-size group share plus selection and cutoff-tie metadata."""

    value: float
    group_size: int
    cutoff_tie_count: int


def _nonnegative_vector(values: list[float] | np.ndarray, *, name: str) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if x.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional vector.")
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must contain only finite values.")
    if np.any(x < 0):
        raise ValueError(f"{name} must be non-negative.")
    return x


def _group_size(size: int, fraction: float) -> int:
    if isinstance(fraction, bool) or not math.isfinite(fraction) or not 0 < fraction <= 1:
        raise ValueError("fraction must be finite and within (0, 1].")
    return min(size, math.ceil(fraction * size)) if size else 0


def gini(values: list[float] | np.ndarray) -> float:
    """Compute the Gini coefficient for a non-negative finite vector."""

    x = _nonnegative_vector(values, name="Gini input")

    if x.size == 0:
        return 0.0

    total = x.sum()
    if total == 0:
        return 0.0

    x = np.sort(x)
    n = x.size
    index = np.arange(1, n + 1)

    result = float((2 * np.sum(index * x)) / (n * total) - (n + 1) / n)
    return min(1.0, max(0.0, result))


def top_fraction_share(values: list[float] | np.ndarray, fraction: float) -> RankedShare:
    """Return the share held by the largest ceiling-sized fraction of a vector."""

    x = _nonnegative_vector(values, name="share input")
    group_size = _group_size(x.size, fraction)
    if group_size == 0:
        return RankedShare(0.0, 0, 0)
    selected = np.sort(x)[-group_size:]
    total = float(x.sum())
    value = float(selected.sum() / total) if total else 0.0
    cutoff_tie_count = int(np.count_nonzero(x == selected[0]))
    return RankedShare(value, group_size, cutoff_tie_count)


def bottom_fraction_burden_share(
    burdens: list[float] | np.ndarray,
    ranking: list[float] | np.ndarray,
    fraction: float,
    *,
    identifiers: list[int] | np.ndarray | None = None,
) -> RankedShare:
    """Return burden borne by the lowest ranked, explicitly tie-broken group."""

    burden = _nonnegative_vector(burdens, name="burden input")
    rank = _nonnegative_vector(ranking, name="ranking input")
    if burden.size != rank.size:
        raise ValueError("burden and ranking vectors must have the same size.")
    group_size = _group_size(burden.size, fraction)
    if group_size == 0:
        return RankedShare(0.0, 0, 0)

    ids = np.arange(burden.size) if identifiers is None else np.asarray(identifiers)
    if ids.ndim != 1 or ids.size != burden.size or len(set(ids.tolist())) != ids.size:
        raise ValueError("identifiers must be a unique one-dimensional vector of matching size.")
    order = np.lexsort((ids, rank))
    selected = order[:group_size]
    total = float(burden.sum())
    value = float(burden[selected].sum() / total) if total else 0.0
    cutoff_tie_count = int(np.count_nonzero(rank == rank[selected[-1]]))
    return RankedShare(value, group_size, cutoff_tie_count)
