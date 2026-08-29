"""Pure resource dynamics and invariant checks."""

import numpy as np

from .types import (
    CellDamageApplication,
    DamageBatch,
    DamageParameters,
    EventCellExposure,
    FloatArray,
    RecoveryState,
    ShockEventState,
    ShockEventStatus,
    ShockTerminationReason,
    WavefrontAdvance,
)

type ResourceInput = float | tuple[tuple[float, ...], ...] | FloatArray


class InvariantViolationError(ValueError):
    """Raised when a scientific state violates a physical invariant."""


def validate_resource_arrays(stock: FloatArray, capacity: FloatArray) -> None:
    if stock.shape != capacity.shape or stock.ndim != 2:
        raise InvariantViolationError("resource stock and capacity must be equal-shaped 2D arrays")
    if not np.isfinite(stock).all() or not np.isfinite(capacity).all():
        raise InvariantViolationError("resource arrays must contain only finite values")
    if (stock < 0).any() or (capacity < 0).any() or (stock > capacity).any():
        raise InvariantViolationError("resource stock must remain between zero and capacity")


def initialize_resources(
    shape: tuple[int, int],
    *,
    initial_stock: ResourceInput,
    capacity: ResourceInput,
) -> tuple[FloatArray, FloatArray]:
    """Build independent ``(x, y)`` stock and capacity arrays from validated inputs."""

    if len(shape) != 2 or any(length <= 0 for length in shape):
        raise InvariantViolationError("configured world shape must contain two positive dimensions")

    stock_is_scalar = np.isscalar(initial_stock)
    capacity_is_scalar = np.isscalar(capacity)
    if stock_is_scalar != capacity_is_scalar:
        raise InvariantViolationError("stock and capacity must both be scalars or both be matrices")

    if stock_is_scalar:
        stock_array = np.full(shape, initial_stock, dtype=np.float64)
        capacity_array = np.full(shape, capacity, dtype=np.float64)
    else:
        stock_array = np.array(initial_stock, dtype=np.float64, copy=True)
        capacity_array = np.array(capacity, dtype=np.float64, copy=True)
        if stock_array.shape != shape or capacity_array.shape != shape:
            raise InvariantViolationError(
                f"resource matrix shape must match configured world shape {shape}"
            )

    validate_resource_arrays(stock_array, capacity_array)
    return stock_array, capacity_array


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


def _validate_baseline_rate(rate: FloatArray, shape: tuple[int, ...]) -> FloatArray:
    rate_array = np.asarray(rate, dtype=np.float64)
    if rate_array.shape != shape or rate_array.ndim != 2:
        raise InvariantViolationError("regeneration arrays must match the 2D resource shape")
    if not np.isfinite(rate_array).all() or (rate_array < 0).any() or (rate_array > 1).any():
        raise InvariantViolationError("regeneration rates must be finite and in [0, 1]")
    return rate_array


def initialize_recovery_state(
    baseline_capacity: FloatArray, baseline_regeneration: FloatArray
) -> RecoveryState:
    """Create undamaged effective ecology and zeroed finite-recovery clocks."""

    capacity = np.asarray(baseline_capacity, dtype=np.float64)
    if capacity.ndim != 2 or not np.isfinite(capacity).all() or (capacity < 0).any():
        raise InvariantViolationError("baseline capacity must be a finite nonnegative 2D array")
    rate = _validate_baseline_rate(baseline_regeneration, capacity.shape)
    return RecoveryState.create(
        capacity,
        rate,
        np.zeros(capacity.shape, dtype=np.int64),
        np.zeros(capacity.shape, dtype=np.float64),
        np.zeros(capacity.shape, dtype=np.float64),
    )


def _validate_recovery_state(
    state: RecoveryState,
    baseline_capacity: FloatArray,
    baseline_regeneration: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    capacity = np.asarray(baseline_capacity, dtype=np.float64)
    if capacity.ndim != 2 or not np.isfinite(capacity).all() or (capacity < 0).any():
        raise InvariantViolationError("baseline capacity must be a finite nonnegative 2D array")
    rate = _validate_baseline_rate(baseline_regeneration, capacity.shape)
    arrays = (
        state.effective_capacity,
        state.effective_regeneration,
        state.remaining_ticks,
        state.capacity_increment,
        state.regeneration_increment,
    )
    if any(array.shape != capacity.shape for array in arrays):
        raise InvariantViolationError("recovery arrays must match baseline capacity")
    if any(not np.isfinite(array).all() for array in arrays):
        raise InvariantViolationError("recovery arrays must contain finite values")
    if (
        (state.effective_capacity < 0).any()
        or (state.effective_capacity > capacity).any()
        or (state.effective_regeneration < 0).any()
        or (state.effective_regeneration > rate).any()
        or (state.remaining_ticks < 0).any()
        or (state.capacity_increment < 0).any()
        or (state.regeneration_increment < 0).any()
    ):
        raise InvariantViolationError("recovery state exceeds its physical bounds")
    return capacity, rate


def apply_recovery(
    state: RecoveryState,
    baseline_capacity: FloatArray,
    baseline_regeneration: FloatArray,
) -> RecoveryState:
    """Advance every active cell-local linear recovery clock by one tick."""

    capacity, rate = _validate_recovery_state(state, baseline_capacity, baseline_regeneration)
    remaining = np.array(state.remaining_ticks, copy=True)
    effective_capacity = np.array(state.effective_capacity, copy=True)
    effective_regeneration = np.array(state.effective_regeneration, copy=True)
    capacity_increment = np.array(state.capacity_increment, copy=True)
    regeneration_increment = np.array(state.regeneration_increment, copy=True)

    active = remaining > 0
    final = remaining == 1
    effective_capacity[active] += capacity_increment[active]
    effective_regeneration[active] += regeneration_increment[active]
    # Floating-point addition can overshoot the analytical baseline by one ulp
    # before the final tick; keep every intermediate state inside its invariant.
    effective_capacity[active] = np.minimum(effective_capacity[active], capacity[active])
    effective_regeneration[active] = np.minimum(effective_regeneration[active], rate[active])
    remaining[active] -= 1
    effective_capacity[final] = capacity[final]
    effective_regeneration[final] = rate[final]
    capacity_increment[final] = 0.0
    regeneration_increment[final] = 0.0

    return RecoveryState.create(
        effective_capacity,
        effective_regeneration,
        remaining,
        capacity_increment,
        regeneration_increment,
    )


def relax_resources(
    stock: FloatArray,
    *,
    effective_capacity: FloatArray,
    effective_regeneration: FloatArray,
    baseline_capacity: FloatArray,
) -> FloatArray:
    """Move stock toward effective capacity while enforcing the baseline physical bound."""

    stock_array = np.asarray(stock, dtype=np.float64)
    baseline = np.asarray(baseline_capacity, dtype=np.float64)
    effective = np.asarray(effective_capacity, dtype=np.float64)
    rate = np.asarray(effective_regeneration, dtype=np.float64)
    if any(array.shape != baseline.shape for array in (stock_array, effective, rate)):
        raise InvariantViolationError("ecology arrays must have equal shapes")
    if baseline.ndim != 2 or any(
        not np.isfinite(array).all() for array in (stock_array, baseline, effective, rate)
    ):
        raise InvariantViolationError("ecology arrays must be finite and two-dimensional")
    if (
        (baseline < 0).any()
        or (stock_array < 0).any()
        or (stock_array > baseline).any()
        or (effective < 0).any()
        or (effective > baseline).any()
        or (rate < 0).any()
        or (rate > 1).any()
    ):
        raise InvariantViolationError("ecology arrays exceed their physical bounds")
    return np.clip(stock_array + rate * (effective - stock_array), 0.0, baseline)


def _validate_damage_parameters(parameters: DamageParameters) -> None:
    fractions = (
        parameters.stock_loss_fraction,
        parameters.capacity_loss_fraction,
        parameters.regeneration_suppression_fraction,
    )
    if any(not np.isfinite(value) or not 0 <= value <= 1 for value in fractions):
        raise InvariantViolationError("damage fractions must be finite and in [0, 1]")
    if parameters.recovery_ticks < 1:
        raise InvariantViolationError("recovery_ticks must be at least one")


def apply_simultaneous_damage(
    stock: FloatArray,
    recovery: RecoveryState,
    baseline_capacity: FloatArray,
    baseline_regeneration: FloatArray,
    *,
    hits: dict[tuple[int, int], tuple[int, ...]],
    parameters: DamageParameters,
    tick: int,
) -> DamageBatch:
    """Compound all same-tick event hits once per cell and restart finite recovery."""

    if tick < 0:
        raise InvariantViolationError("damage tick cannot be negative")
    _validate_damage_parameters(parameters)
    capacity, rate = _validate_recovery_state(recovery, baseline_capacity, baseline_regeneration)
    stock_array = np.asarray(stock, dtype=np.float64)
    if stock_array.shape != capacity.shape or not np.isfinite(stock_array).all():
        raise InvariantViolationError("resource stock must match finite baseline capacity")
    if (stock_array < 0).any() or (stock_array > capacity).any():
        raise InvariantViolationError("resource stock must remain within baseline capacity")

    updated_stock = np.array(stock_array, copy=True)
    effective_capacity = np.array(recovery.effective_capacity, copy=True)
    effective_regeneration = np.array(recovery.effective_regeneration, copy=True)
    remaining = np.array(recovery.remaining_ticks, copy=True)
    capacity_increment = np.array(recovery.capacity_increment, copy=True)
    regeneration_increment = np.array(recovery.regeneration_increment, copy=True)
    applications: list[CellDamageApplication] = []

    for position in sorted(hits):
        x, y = position
        if not (0 <= x < capacity.shape[0] and 0 <= y < capacity.shape[1]):
            raise InvariantViolationError(f"damage position {position} is outside the world")
        event_ids = tuple(sorted(hits[position]))
        if not event_ids or any(event_id <= 0 for event_id in event_ids):
            raise InvariantViolationError("damage hits require positive event IDs")
        if len(set(event_ids)) != len(event_ids):
            raise InvariantViolationError("a cell cannot list the same event hit twice")

        hit_count = len(event_ids)
        stock_multiplier = (1.0 - parameters.stock_loss_fraction) ** hit_count
        capacity_multiplier = (1.0 - parameters.capacity_loss_fraction) ** hit_count
        regeneration_multiplier = (1.0 - parameters.regeneration_suppression_fraction) ** hit_count
        pre_stock = float(updated_stock[position])
        pre_capacity = float(effective_capacity[position])
        pre_regeneration = float(effective_regeneration[position])
        updated_stock[position] *= stock_multiplier
        effective_capacity[position] *= capacity_multiplier
        effective_regeneration[position] *= regeneration_multiplier
        remaining[position] = parameters.recovery_ticks
        capacity_increment[position] = (
            capacity[position] - effective_capacity[position]
        ) / parameters.recovery_ticks
        regeneration_increment[position] = (
            rate[position] - effective_regeneration[position]
        ) / parameters.recovery_ticks
        applications.append(
            CellDamageApplication(
                tick=tick,
                position=position,
                event_ids=event_ids,
                combined_stock_multiplier=stock_multiplier,
                combined_capacity_multiplier=capacity_multiplier,
                combined_regeneration_multiplier=regeneration_multiplier,
                pre_stock=pre_stock,
                post_stock=float(updated_stock[position]),
                pre_effective_capacity=pre_capacity,
                post_effective_capacity=float(effective_capacity[position]),
                pre_effective_regeneration=pre_regeneration,
                post_effective_regeneration=float(effective_regeneration[position]),
                recovery_completion_tick=tick + parameters.recovery_ticks,
            )
        )

    updated_recovery = RecoveryState.create(
        effective_capacity,
        effective_regeneration,
        remaining,
        capacity_increment,
        regeneration_increment,
    )
    return DamageBatch.create(updated_stock, updated_recovery, tuple(applications))


def von_neumann_neighbors(
    position: tuple[int, int], shape: tuple[int, int], *, torus: bool
) -> tuple[tuple[int, int], ...]:
    """Return unique, sorted orthogonal neighbors for an abstract rectangular world."""

    if len(shape) != 2 or any(length <= 0 for length in shape):
        raise InvariantViolationError("world shape must contain two positive dimensions")
    x, y = position
    width, height = shape
    if not (0 <= x < width and 0 <= y < height):
        raise InvariantViolationError(f"position {position} is outside the world")
    candidates = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
    neighbors: set[tuple[int, int]] = set()
    for candidate_x, candidate_y in candidates:
        if torus:
            candidate = (candidate_x % width, candidate_y % height)
            if candidate != position:
                neighbors.add(candidate)
        elif 0 <= candidate_x < width and 0 <= candidate_y < height:
            neighbors.add((candidate_x, candidate_y))
    return tuple(sorted(neighbors))


def start_correlated_event(
    event_id: int,
    tick: int,
    epicenter: tuple[int, int],
    spread_probability: float,
    max_spread_ticks: int,
) -> ShockEventState:
    """Create a correlated event whose epicenter is affected on the initiation tick."""

    if event_id <= 0 or tick < 0:
        raise InvariantViolationError("event ID must be positive and tick cannot be negative")
    if not np.isfinite(spread_probability) or not 0 <= spread_probability <= 1:
        raise InvariantViolationError("spread_probability must be finite and in [0, 1]")
    if max_spread_ticks < 0:
        raise InvariantViolationError("max_spread_ticks cannot be negative")
    terminated = max_spread_ticks == 0
    return ShockEventState.create(
        event_id=event_id,
        initiation_tick=tick,
        epicenter=epicenter,
        frontier={epicenter},
        affected={epicenter},
        spread_rounds_completed=0,
        spread_probability=spread_probability,
        max_spread_ticks=max_spread_ticks,
        status=ShockEventStatus.TERMINATED if terminated else ShockEventStatus.ACTIVE,
        termination_reason=(ShockTerminationReason.MAX_SPREAD_TICKS if terminated else None),
    )


def advance_correlated_event(
    event: ShockEventState,
    *,
    tick: int,
    shape: tuple[int, int],
    torus: bool,
    rng: np.random.Generator,
) -> WavefrontAdvance:
    """Advance one synchronous wavefront round with canonical independent edge draws."""

    if event.status is not ShockEventStatus.ACTIVE:
        raise InvariantViolationError("only active correlated events can advance")
    if tick <= event.initiation_tick or event.spread_rounds_completed >= event.max_spread_ticks:
        raise InvariantViolationError("event cannot advance at the requested tick or round")

    exposing_by_target: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for source in sorted(event.frontier):
        for target in von_neumann_neighbors(source, shape, torus=torus):
            if target not in event.affected:
                exposing_by_target.setdefault(target, []).append(source)

    exposures: list[EventCellExposure] = []
    newly_affected: list[tuple[int, int]] = []
    for target in sorted(exposing_by_target):
        exposing = tuple(sorted(exposing_by_target[target]))
        successful = tuple(source for source in exposing if rng.random() < event.spread_probability)
        exposure = EventCellExposure(
            tick=tick,
            event_id=event.event_id,
            position=target,
            exposing_neighbors=exposing,
            successful_neighbors=successful,
        )
        exposures.append(exposure)
        if exposure.transmitted:
            newly_affected.append(target)

    completed = event.spread_rounds_completed + 1
    reached_limit = completed >= event.max_spread_ticks
    exhausted = not newly_affected
    if exhausted:
        status = ShockEventStatus.TERMINATED
        reason = ShockTerminationReason.FRONTIER_EXHAUSTED
    elif reached_limit:
        status = ShockEventStatus.TERMINATED
        reason = ShockTerminationReason.MAX_SPREAD_TICKS
    else:
        status = ShockEventStatus.ACTIVE
        reason = None
    updated_event = ShockEventState.create(
        event_id=event.event_id,
        initiation_tick=event.initiation_tick,
        epicenter=event.epicenter,
        frontier=set(newly_affected),
        affected=set(event.affected).union(newly_affected),
        spread_rounds_completed=completed,
        spread_probability=event.spread_probability,
        max_spread_ticks=event.max_spread_ticks,
        status=status,
        termination_reason=reason,
    )
    return WavefrontAdvance(updated_event, tuple(exposures), tuple(newly_affected))


def draw_event(event_probability: float, rng: np.random.Generator) -> bool:
    """Draw one explicit per-tick event hazard."""

    if not np.isfinite(event_probability) or not 0 <= event_probability <= 1:
        raise InvariantViolationError("event_probability must be finite and in [0, 1]")
    if event_probability == 0:
        return False
    if event_probability == 1:
        return True
    return bool(rng.random() < event_probability)


def draw_independent_hits(
    shape: tuple[int, int], event_probability: float, rng: np.random.Generator
) -> tuple[tuple[int, int], ...]:
    """Draw one independent hazard per cell in canonical ``(x, y)`` order."""

    if len(shape) != 2 or any(length <= 0 for length in shape):
        raise InvariantViolationError("world shape must contain two positive dimensions")
    if not np.isfinite(event_probability) or not 0 <= event_probability <= 1:
        raise InvariantViolationError("event_probability must be finite and in [0, 1]")
    positions = tuple((x, y) for x in range(shape[0]) for y in range(shape[1]))
    if event_probability == 0:
        return ()
    if event_probability == 1:
        return positions
    return tuple(position for position in positions if rng.random() < event_probability)


def draw_uniform_position(shape: tuple[int, int], rng: np.random.Generator) -> tuple[int, int]:
    """Draw one cell uniformly using the documented x-major matrix orientation."""

    if len(shape) != 2 or any(length <= 0 for length in shape):
        raise InvariantViolationError("world shape must contain two positive dimensions")
    flat_index = int(rng.integers(shape[0] * shape[1]))
    return divmod(flat_index, shape[1])
