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
type IntArray = NDArray[np.int64]


class ActionKind(StrEnum):
    HARVEST = "harvest"
    MOVE = "move"
    REST = "rest"


class ShockEventStatus(StrEnum):
    ACTIVE = "active"
    TERMINATED = "terminated"


class ShockTerminationReason(StrEnum):
    FRONTIER_EXHAUSTED = "frontier_exhausted"
    MAX_SPREAD_TICKS = "max_spread_ticks"
    NONSPREADING = "nonspreading"


class ShockScope(StrEnum):
    INDEPENDENT = "independent"
    CORRELATED = "correlated"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class AgentState:
    agent_id: AgentId
    energy: float
    alive: bool = True


@dataclass(frozen=True, slots=True)
class AgentSnapshot:
    tick: int
    agent_id: AgentId
    position: Position
    energy: float
    alive: bool


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
    def move(cls, agent_id: AgentId, position: Position, destination: Position) -> "ActionIntent":
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
class DamageParameters:
    stock_loss_fraction: float
    capacity_loss_fraction: float
    regeneration_suppression_fraction: float
    recovery_ticks: int


@dataclass(frozen=True, slots=True)
class RecoveryState:
    effective_capacity: FloatArray
    effective_regeneration: FloatArray
    remaining_ticks: IntArray
    capacity_increment: FloatArray
    regeneration_increment: FloatArray

    @classmethod
    def create(
        cls,
        effective_capacity: FloatArray,
        effective_regeneration: FloatArray,
        remaining_ticks: IntArray,
        capacity_increment: FloatArray,
        regeneration_increment: FloatArray,
    ) -> "RecoveryState":
        arrays = (
            np.array(effective_capacity, dtype=np.float64, copy=True),
            np.array(effective_regeneration, dtype=np.float64, copy=True),
            np.array(remaining_ticks, dtype=np.int64, copy=True),
            np.array(capacity_increment, dtype=np.float64, copy=True),
            np.array(regeneration_increment, dtype=np.float64, copy=True),
        )
        for array in arrays:
            array.setflags(write=False)
        return cls(*arrays)


@dataclass(frozen=True, slots=True)
class CellDamageApplication:
    tick: int
    position: Position
    event_ids: tuple[int, ...]
    combined_stock_multiplier: float
    combined_capacity_multiplier: float
    combined_regeneration_multiplier: float
    pre_stock: float
    post_stock: float
    pre_effective_capacity: float
    post_effective_capacity: float
    pre_effective_regeneration: float
    post_effective_regeneration: float
    recovery_completion_tick: int


@dataclass(frozen=True, slots=True)
class DamageBatch:
    resource_stock: FloatArray
    recovery: RecoveryState
    applications: tuple[CellDamageApplication, ...]

    @classmethod
    def create(
        cls,
        resource_stock: FloatArray,
        recovery: RecoveryState,
        applications: tuple[CellDamageApplication, ...],
    ) -> "DamageBatch":
        stock = np.array(resource_stock, dtype=np.float64, copy=True)
        stock.setflags(write=False)
        return cls(stock, recovery, applications)


@dataclass(frozen=True, slots=True)
class ShockEventState:
    event_id: int
    initiation_tick: int
    epicenter: Position
    frontier: frozenset[Position]
    affected: frozenset[Position]
    spread_rounds_completed: int
    spread_probability: float
    max_spread_ticks: int
    status: ShockEventStatus = ShockEventStatus.ACTIVE
    termination_reason: ShockTerminationReason | None = None

    @classmethod
    def create(
        cls,
        event_id: int,
        initiation_tick: int,
        epicenter: Position,
        frontier: set[Position] | frozenset[Position],
        affected: set[Position] | frozenset[Position],
        spread_rounds_completed: int,
        spread_probability: float,
        max_spread_ticks: int,
        status: ShockEventStatus = ShockEventStatus.ACTIVE,
        termination_reason: ShockTerminationReason | None = None,
    ) -> "ShockEventState":
        return cls(
            event_id=event_id,
            initiation_tick=initiation_tick,
            epicenter=epicenter,
            frontier=frozenset(frontier),
            affected=frozenset(affected),
            spread_rounds_completed=spread_rounds_completed,
            spread_probability=spread_probability,
            max_spread_ticks=max_spread_ticks,
            status=status,
            termination_reason=termination_reason,
        )


@dataclass(frozen=True, slots=True)
class EventCellExposure:
    tick: int
    event_id: int
    position: Position
    exposing_neighbors: tuple[Position, ...]
    successful_neighbors: tuple[Position, ...]

    @property
    def transmitted(self) -> bool:
        return bool(self.successful_neighbors)


@dataclass(frozen=True, slots=True)
class WavefrontAdvance:
    event: ShockEventState
    exposures: tuple[EventCellExposure, ...]
    newly_affected: tuple[Position, ...]


@dataclass(frozen=True, slots=True)
class ShockEventSnapshot:
    tick: int
    event_id: int
    scope: ShockScope
    initiation_tick: int
    epicenter: Position | None
    age: int
    status: ShockEventStatus
    frontier: tuple[Position, ...]
    affected_count: int
    event_probability: float
    damage: DamageParameters
    spread_probability: float | None = None
    max_spread_ticks: int | None = None
    termination_reason: ShockTerminationReason | None = None


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
