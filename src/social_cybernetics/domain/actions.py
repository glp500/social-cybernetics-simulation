"""Side-effect-free policy, gate, and simultaneous physical resolution."""

import math
from collections import defaultdict
from collections.abc import Sequence

import numpy as np

from .ecology import InvariantViolationError
from .types import (
    ActionIntent,
    ActionKind,
    ActionResolution,
    AgentSnapshot,
    BeliefState,
    FloatArray,
    GateDecision,
    Position,
    ResolutionBatch,
)


def literal_local_policy(
    snapshot: AgentSnapshot,
    belief: BeliefState,
    neighbors: Sequence[Position],
    *,
    harvest_threshold: float,
    harvest_capacity: float,
    rng: np.random.Generator,
) -> ActionIntent:
    """Harvest at threshold; otherwise choose one neighbor uniformly."""

    if belief.agent_id != snapshot.agent_id:
        raise InvariantViolationError("belief and snapshot agent identifiers differ")
    if belief.believed_local_stock >= harvest_threshold:
        return ActionIntent.harvest(snapshot.agent_id, snapshot.position, harvest_capacity)
    if not neighbors:
        raise InvariantViolationError("movement policy requires at least one neighboring cell")
    choices = tuple(sorted(neighbors))
    destination = choices[int(rng.integers(0, len(choices)))]
    return ActionIntent.move(snapshot.agent_id, snapshot.position, destination)


def allow_all(intent: ActionIntent) -> GateDecision:
    return GateDecision(intent.agent_id, True, intent)


def _validate_intent(intent: ActionIntent, shape: tuple[int, ...]) -> None:
    x, y = intent.position
    if not (0 <= x < shape[0] and 0 <= y < shape[1]):
        raise InvariantViolationError(f"intent position {intent.position} is outside resource array")
    if not math.isfinite(intent.amount) or intent.amount < 0:
        raise InvariantViolationError("requested amount must be finite and nonnegative")
    if intent.kind is ActionKind.MOVE and intent.destination is None:
        raise InvariantViolationError("movement intent requires a destination")


def resolve_actions(
    resource_stock: FloatArray, decisions: Sequence[GateDecision]
) -> ResolutionBatch:
    """Resolve all allowed actions from one stage snapshot, by cell."""

    updated = np.asarray(resource_stock, dtype=np.float64).copy()
    if updated.ndim != 2 or not np.isfinite(updated).all() or (updated < 0).any():
        raise InvariantViolationError("resource stock must be a finite nonnegative 2D array")

    by_agent: dict[int, ActionResolution] = {}
    requests: dict[Position, list[ActionIntent]] = defaultdict(list)
    for decision in sorted(decisions, key=lambda item: item.agent_id):
        intent = decision.intent
        if decision.agent_id != intent.agent_id or intent.agent_id in by_agent:
            raise InvariantViolationError("each gate decision must identify one unique agent")
        _validate_intent(intent, updated.shape)
        if not decision.allowed:
            by_agent[intent.agent_id] = ActionResolution(
                intent.agent_id, intent.kind, rejected=True
            )
        elif intent.kind is ActionKind.HARVEST:
            requests[intent.position].append(intent)
        elif intent.kind is ActionKind.MOVE:
            by_agent[intent.agent_id] = ActionResolution(
                intent.agent_id,
                intent.kind,
                moved=True,
                destination=intent.destination,
            )
        else:
            by_agent[intent.agent_id] = ActionResolution(intent.agent_id, intent.kind)

    for position, cell_requests in sorted(requests.items()):
        ordered = sorted(cell_requests, key=lambda item: item.agent_id)
        total_requested = math.fsum(item.amount for item in ordered)
        available = float(updated[position])
        target = min(available, total_requested)
        allocations = (
            [
                item.amount
                if total_requested <= available
                else available * item.amount / total_requested
                for item in ordered
            ]
            if total_requested
            else [0.0 for _ in ordered]
        )
        if allocations:
            allocations[-1] += target - math.fsum(allocations)
        for intent, allocated in zip(ordered, allocations, strict=True):
            by_agent[intent.agent_id] = ActionResolution(
                intent.agent_id, intent.kind, harvested=allocated
            )
        updated[position] = available - target

    if (updated < -1e-12).any() or not np.isfinite(updated).all():
        raise InvariantViolationError("physical resolution produced invalid resource stock")
    updated[updated < 0] = 0
    return ResolutionBatch.create(updated, by_agent)
