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
    def __call__(self, snapshot: AgentSnapshot, local_stock: float) -> Observation: ...


class DecisionPolicy(Protocol):
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
    def __call__(self, intent: ActionIntent) -> GateDecision: ...


class PhysicalResolver(Protocol):
    def __call__(
        self, resource_stock: FloatArray, decisions: Sequence[GateDecision]
    ) -> ResolutionBatch: ...
