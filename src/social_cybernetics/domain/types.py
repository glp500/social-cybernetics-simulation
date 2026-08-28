"""Mesa-independent state, stage, and record contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

import numpy as np
from numpy.typing import NDArray

type AgentId = int
type Position = tuple[int, int]
type FloatArray = NDArray[np.float64]


class ActionKind(StrEnum):
    HARVEST = "harvest"
    MOVE = "move"
    REST = "rest"


@dataclass(frozen=True, slots=True)
class AgentState:
    agent_id: AgentId
    energy: float
    alive: bool = True
    action_capacity: float = 1.0
    resource_holdings: float = 0.0
    debt: float = 0.0
    information_capabilities: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class AgentSnapshot:
    tick: int
    agent_id: AgentId
    position: Position
    energy: float
    alive: bool
    resource_holdings: float = 0.0
    debt: float = 0.0
    information_capabilities: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class Observation:
    agent_id: AgentId
    position: Position
    local_stock: float


@dataclass(frozen=True, slots=True)
class BeliefState:
    agent_id: AgentId
    believed_local_stock: float


@dataclass(frozen=True, slots=True)
class ActionIntent:
    agent_id: AgentId
    kind: ActionKind
    position: Position
    amount: float = 0.0
    destination: Position | None = None

    @classmethod
    def harvest(cls, agent_id: AgentId, position: Position, amount: float) -> "ActionIntent":
        return cls(agent_id, ActionKind.HARVEST, position, amount=amount)

    @classmethod
    def move(
        cls, agent_id: AgentId, position: Position, destination: Position
    ) -> "ActionIntent":
        return cls(agent_id, ActionKind.MOVE, position, destination=destination)


@dataclass(frozen=True, slots=True)
class GateDecision:
    agent_id: AgentId
    allowed: bool
    intent: ActionIntent
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ActionResolution:
    agent_id: AgentId
    kind: ActionKind
    harvested: float = 0.0
    moved: bool = False
    destination: Position | None = None
    rejected: bool = False


@dataclass(frozen=True, slots=True)
class ResolutionBatch:
    resource_stock: FloatArray
    by_agent: Mapping[AgentId, ActionResolution]

    @classmethod
    def create(
        cls, resource_stock: FloatArray, by_agent: dict[AgentId, ActionResolution]
    ) -> "ResolutionBatch":
        return cls(resource_stock, MappingProxyType(dict(sorted(by_agent.items()))))


@dataclass(frozen=True, slots=True)
class ModelRecord:
    tick: int
    total_resources: float
    alive_count: int
    cohort_mean_energy: float
    total_harvest: float
    unmet_need: float
    energy_gini: float


@dataclass(frozen=True, slots=True)
class CohortRecord:
    tick: int
    snapshot: AgentSnapshot


@dataclass(frozen=True, slots=True)
class EventRecord:
    tick: int
    event: str
    agent_id: AgentId | None = None
    amount: float | None = None
    position: Position | None = None
