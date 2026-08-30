"""Ecological deficit and recovery metrics over complete spatial history."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

type FloatArray = NDArray[np.float64]
type IntArray = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class SeriesSummary:
    values: tuple[float, ...]
    final: float
    mean: float
    maximum: float


@dataclass(frozen=True, slots=True)
class RecoverySpell:
    position: tuple[int, int]
    start_tick: int
    end_tick: int
    length: int
    right_censored: bool


@dataclass(frozen=True, slots=True)
class EcologyMetrics:
    resource_depletion: SeriesSummary
    capacity_deficit: SeriesSummary
    regeneration_deficit: SeriesSummary
    recovery_spells: tuple[RecoverySpell, ...]
    observed_mean_recovery_duration: float
    completed_mean_recovery_duration: float
    cumulative_capacity_deficit: float
    cumulative_regeneration_deficit: float
    cumulative_recovery_deficit: float


def _validated_spatial_arrays(
    *,
    resource_stock: NDArray[object],
    effective_capacity: NDArray[object],
    effective_regeneration: NDArray[object],
    recovery_remaining: NDArray[object],
    baseline_capacity: NDArray[object],
    baseline_regeneration: NDArray[object],
) -> tuple[FloatArray, FloatArray, FloatArray, IntArray, FloatArray, FloatArray]:
    stock = np.asarray(resource_stock, dtype=np.float64)
    capacity = np.asarray(effective_capacity, dtype=np.float64)
    regeneration = np.asarray(effective_regeneration, dtype=np.float64)
    remaining_input = np.asarray(recovery_remaining)
    baseline_k = np.asarray(baseline_capacity, dtype=np.float64)
    baseline_r = np.asarray(baseline_regeneration, dtype=np.float64)
    if stock.ndim != 3 or capacity.shape != stock.shape or regeneration.shape != stock.shape:
        raise ValueError("dynamic ecology arrays must have the same three-dimensional shape")
    if remaining_input.shape != stock.shape:
        raise ValueError("recovery history must match the dynamic ecology shape")
    if baseline_k.shape != stock.shape[1:] or baseline_r.shape != stock.shape[1:]:
        raise ValueError("baseline arrays must match spatial dimensions")
    arrays = (stock, capacity, regeneration, baseline_k, baseline_r)
    if any(not np.all(np.isfinite(array)) or np.any(array < 0) for array in arrays):
        raise ValueError("ecological histories must be finite and nonnegative")
    if not np.issubdtype(remaining_input.dtype, np.integer) or np.any(remaining_input < 0):
        raise ValueError("recovery history must contain nonnegative integers")
    if np.any(stock > baseline_k) or np.any(capacity > baseline_k):
        raise ValueError("stock and effective capacity cannot exceed baseline capacity")
    if np.any(regeneration > baseline_r):
        raise ValueError("effective regeneration cannot exceed baseline regeneration")
    return stock, capacity, regeneration, remaining_input.astype(np.int64), baseline_k, baseline_r


def _normalized_deficit(baseline: FloatArray, values: FloatArray) -> tuple[float, ...]:
    denominator = float(baseline.sum())
    deficits = np.sum(baseline[None, :, :] - values, axis=(1, 2))
    if denominator == 0.0:
        if np.any(deficits != 0.0):
            raise ValueError("zero baseline cannot have a positive deficit")
        return tuple(0.0 for _ in deficits)
    return tuple(float(value / denominator) for value in deficits)


def _summary(values: tuple[float, ...]) -> SeriesSummary:
    return SeriesSummary(
        values=values,
        final=values[-1] if values else 0.0,
        mean=math.fsum(values) / len(values) if values else 0.0,
        maximum=max(values, default=0.0),
    )


def _recovery_spells(remaining: IntArray) -> tuple[RecoverySpell, ...]:
    spells: list[RecoverySpell] = []
    final_tick = remaining.shape[0] - 1
    for x in range(remaining.shape[1]):
        for y in range(remaining.shape[2]):
            start: int | None = None
            for tick in range(remaining.shape[0]):
                recovering = remaining[tick, x, y] > 0
                if recovering and start is None:
                    start = tick
                elif not recovering and start is not None:
                    spells.append(RecoverySpell((x, y), start, tick - 1, tick - start, False))
                    start = None
            if start is not None:
                spells.append(
                    RecoverySpell(
                        (x, y),
                        start,
                        final_tick,
                        final_tick - start + 1,
                        True,
                    )
                )
    return tuple(spells)


def calculate_ecology(
    *,
    resource_stock: NDArray[object],
    effective_capacity: NDArray[object],
    effective_regeneration: NDArray[object],
    recovery_remaining: NDArray[object],
    baseline_capacity: NDArray[object],
    baseline_regeneration: NDArray[object],
) -> EcologyMetrics:
    """Calculate normalized ecological paths and cell-level recovery spells."""

    stock, capacity, regeneration, remaining, baseline_k, baseline_r = _validated_spatial_arrays(
        resource_stock=resource_stock,
        effective_capacity=effective_capacity,
        effective_regeneration=effective_regeneration,
        recovery_remaining=recovery_remaining,
        baseline_capacity=baseline_capacity,
        baseline_regeneration=baseline_regeneration,
    )
    depletion = _normalized_deficit(baseline_k, stock)
    capacity_deficit = _normalized_deficit(baseline_k, capacity)
    regeneration_deficit = _normalized_deficit(baseline_r, regeneration)
    spells = _recovery_spells(remaining)
    completed = [spell.length for spell in spells if not spell.right_censored]
    observed = [spell.length for spell in spells]
    cumulative_capacity = math.fsum(capacity_deficit)
    cumulative_regeneration = math.fsum(regeneration_deficit)
    return EcologyMetrics(
        resource_depletion=_summary(depletion),
        capacity_deficit=_summary(capacity_deficit),
        regeneration_deficit=_summary(regeneration_deficit),
        recovery_spells=spells,
        observed_mean_recovery_duration=(math.fsum(observed) / len(observed) if observed else 0.0),
        completed_mean_recovery_duration=(
            math.fsum(completed) / len(completed) if completed else 0.0
        ),
        cumulative_capacity_deficit=cumulative_capacity,
        cumulative_regeneration_deficit=cumulative_regeneration,
        cumulative_recovery_deficit=(cumulative_capacity + cumulative_regeneration) / 2,
    )
