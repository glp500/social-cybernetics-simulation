"""Direct observation and literal belief-copy mechanisms."""

import math

from .ecology import InvariantViolationError
from .types import AgentSnapshot, BeliefState, Observation


def direct_observation(snapshot: AgentSnapshot, local_stock: float) -> Observation:
    """Expose exact local stock while preserving the observing agent and position."""

    if not math.isfinite(local_stock) or local_stock < 0:
        raise InvariantViolationError("observed resource stock must be finite and nonnegative")
    return Observation(snapshot.agent_id, snapshot.position, local_stock)


def copy_observation(observation: Observation) -> BeliefState:
    """Create a distinct belief value from direct observation without aliasing."""

    return BeliefState(observation.agent_id, observation.local_stock)
