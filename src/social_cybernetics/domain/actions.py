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
    policy_values = (
        belief.believed_local_stock,
        harvest_threshold,
        harvest_capacity,
    )
    if not all(math.isfinite(value) and value >= 0 for value in policy_values):
        raise InvariantViolationError("policy stocks, threshold, and capacity must be nonnegative")
    if belief.believed_local_stock >= harvest_threshold:
        return ActionIntent.harvest(snapshot.agent_id, snapshot.position, harvest_capacity)
    if not neighbors:
        raise InvariantViolationError("movement policy requires at least one neighboring cell")
    choices = tuple(sorted(neighbors))
    destination = choices[int(rng.integers(0, len(choices)))]
    return ActionIntent.move(snapshot.agent_id, snapshot.position, destination)


def allow_all(intent: ActionIntent) -> GateDecision:
    """Return Project 1's identity-like institutional control decision."""

    return GateDecision(intent.agent_id, True, intent)


def _validate_intent(intent: ActionIntent, shape: tuple[int, ...]) -> None:
    x, y = intent.position
    if not (0 <= x < shape[0] and 0 <= y < shape[1]):
        raise InvariantViolationError(
            f"intent position {intent.position} is outside resource array"
        )
    if not math.isfinite(intent.amount) or intent.amount < 0:
        raise InvariantViolationError("requested amount must be finite and nonnegative")
    if intent.kind is ActionKind.MOVE and intent.destination is None:
        raise InvariantViolationError("movement intent requires a destination")
    if intent.destination is not None:
        destination_x, destination_y = intent.destination
        if not (0 <= destination_x < shape[0] and 0 <= destination_y < shape[1]):
            raise InvariantViolationError("movement destination is outside resource array")


def _collect_requests(
    decisions: Sequence[GateDecision], shape: tuple[int, ...]
) -> tuple[dict[int, ActionResolution], dict[Position, list[ActionIntent]]]:
    resolutions: dict[int, ActionResolution] = {}
    requests: dict[Position, list[ActionIntent]] = defaultdict(list)
    seen_agents: set[int] = set()
    for decision in sorted(decisions, key=lambda item: item.agent_id):
        intent = decision.intent
        if decision.agent_id != intent.agent_id or intent.agent_id in seen_agents:
            raise InvariantViolationError("each gate decision must identify one unique agent")
        seen_agents.add(intent.agent_id)
        _validate_intent(intent, shape)
        if not decision.allowed:
            resolutions[intent.agent_id] = ActionResolution(
                intent.agent_id, intent.kind, rejected=True
            )
        elif intent.kind is ActionKind.HARVEST:
            requests[intent.position].append(intent)
        elif intent.kind is ActionKind.MOVE:
            resolutions[intent.agent_id] = ActionResolution(
                intent.agent_id,
                intent.kind,
                moved=True,
                destination=intent.destination,
            )
        else:
            resolutions[intent.agent_id] = ActionResolution(intent.agent_id, intent.kind)
    return resolutions, requests


def _allocate_requests(
    updated: FloatArray,
    requests: dict[Position, list[ActionIntent]],
    resolutions: dict[int, ActionResolution],
) -> None:
    for position, cell_requests in sorted(requests.items()):
        ordered = sorted(cell_requests, key=lambda item: item.agent_id)
        total_requested = math.fsum(item.amount for item in ordered)
        available = float(updated[position])
        target = min(available, total_requested)
        allocations = [
            0.0 if total_requested == 0.0 else min(1.0, available / total_requested) * item.amount
            for item in ordered
        ]
        if allocations:
            allocations[-1] += target - math.fsum(allocations)
        for intent, allocated in zip(ordered, allocations, strict=True):
            resolutions[intent.agent_id] = ActionResolution(
                intent.agent_id, intent.kind, harvested=allocated
            )
        updated[position] = available - target


def _validated_stock_copy(resource_stock: FloatArray) -> FloatArray:
    updated = np.asarray(resource_stock, dtype=np.float64).copy()
    if updated.ndim != 2 or not np.isfinite(updated).all() or (updated < 0).any():
        raise InvariantViolationError("resource stock must be a finite nonnegative 2D array")
    return updated


def resolve_actions(
    resource_stock: FloatArray, decisions: Sequence[GateDecision]
) -> ResolutionBatch:
    """Resolve all allowed actions from one stage snapshot, by cell."""

    updated = _validated_stock_copy(resource_stock)
    resolutions, requests = _collect_requests(decisions, updated.shape)
    _allocate_requests(updated, requests, resolutions)
    if (updated < -1e-12).any() or not np.isfinite(updated).all():
        raise InvariantViolationError("physical resolution produced invalid resource stock")
    updated[updated < 0] = 0
    return ResolutionBatch.create(updated, resolutions)
