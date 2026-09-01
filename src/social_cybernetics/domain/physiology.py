"""Pure conversion, metabolism, and mortality mechanisms."""

import math
from dataclasses import replace

from .ecology import InvariantViolationError
from .types import AgentState


def apply_metabolism(
    state: AgentState,
    *,
    harvested: float,
    moved: bool,
    conversion_efficiency: float,
    basal_cost: float,
    movement_cost: float,
) -> tuple[AgentState, bool]:
    """Apply harvest conversion and costs, clamping energy to zero on death."""

    if not state.alive:
        raise InvariantViolationError("dead agents cannot be metabolized")
    values = (state.energy, harvested, conversion_efficiency, basal_cost, movement_cost)
    if not all(math.isfinite(value) and value >= 0 for value in values):
        raise InvariantViolationError("energy flows and costs must be finite and nonnegative")
    energy = (
        state.energy
        + harvested * conversion_efficiency
        - basal_cost
        - (movement_cost if moved else 0.0)
    )
    died = energy <= 0
    return replace(state, energy=0.0 if died else energy, alive=not died), died
