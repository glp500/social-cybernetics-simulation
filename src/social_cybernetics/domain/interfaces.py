"""Substitutable mechanism interfaces owned by the pure domain."""

from collections.abc import Sequence
from typing import Protocol

import numpy as np

from .types import (
    ActionIntent,
    AgentSnapshot,
    BeliefState,
    FloatArray,
    GateDecision,
    Observation,
    Position,
    ResolutionBatch,
)


class ObservationSystem(Protocol):
    """Contract for converting an agent snapshot and environment into information."""

    def __call__(self, snapshot: AgentSnapshot, local_stock: float) -> Observation: ...


class DecisionPolicy(Protocol):
    """Contract for producing one side-effect-free intent per living agent."""

    def __call__(
        self,
        snapshot: AgentSnapshot,
        belief: BeliefState,
        neighbors: Sequence[Position],
        *,
        harvest_threshold: float,
        harvest_capacity: float,
        rng: np.random.Generator,
    ) -> ActionIntent: ...


class InstitutionalGate(Protocol):
    """Contract for permitting, rejecting, or later modifying action access."""

    def __call__(self, intent: ActionIntent) -> GateDecision: ...


class PhysicalResolver(Protocol):
    """Contract for resolving a complete decision stage simultaneously."""

    def __call__(
        self, resource_stock: FloatArray, decisions: Sequence[GateDecision]
    ) -> ResolutionBatch: ...
