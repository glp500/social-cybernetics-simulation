"""Direct observation and literal belief-copy mechanisms."""

import math

from .ecology import InvariantViolationError
from .types import AgentSnapshot, BeliefState, Observation


def direct_observation(snapshot: AgentSnapshot, local_stock: float) -> Observation:
    if not math.isfinite(local_stock) or local_stock < 0:
        raise InvariantViolationError("observed resource stock must be finite and nonnegative")
    return Observation(snapshot.agent_id, snapshot.position, local_stock)


def copy_observation(observation: Observation) -> BeliefState:
    return BeliefState(observation.agent_id, observation.local_stock)
