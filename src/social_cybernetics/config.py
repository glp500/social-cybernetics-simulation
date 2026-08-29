"""Validated executable configuration for implemented v0.1 and v0.2 variants."""

import math
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Position = tuple[int, int]
MAX_CONFIG_BYTES = 1_048_576


class StrictModel(BaseModel):
    """Base configuration contract that rejects misspelled or future fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class WorldConfig(StrictModel):
    width: int = Field(default=5, ge=1)
    height: int = Field(default=5, ge=1)
    torus: bool = True
    occupancy: Literal["unlimited"] = "unlimited"


class ResourceConfig(StrictModel):
    kind: Literal["uniform"] = "uniform"
    capacity: float = Field(default=10.0, ge=0)
    initial_stock: float = Field(default=10.0, ge=0)
    regeneration_rate: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def stock_fits_capacity(self) -> Self:
        if self.initial_stock > self.capacity:
            raise ValueError("initial_stock cannot exceed capacity")
        return self


class ExplicitResourceConfig(StrictModel):
    """A realized resource landscape indexed as ``(x, y)``."""

    kind: Literal["explicit"] = "explicit"
    capacity: tuple[tuple[float, ...], ...]
    initial_stock: tuple[tuple[float, ...], ...]
    regeneration_rate: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_matrices(self) -> Self:
        capacity_shape = tuple(len(column) for column in self.capacity)
        stock_shape = tuple(len(column) for column in self.initial_stock)
        if len(self.capacity) != len(self.initial_stock) or capacity_shape != stock_shape:
            raise ValueError("capacity and initial_stock matrices must have the same shape")
        if not self.capacity or not capacity_shape or any(length == 0 for length in capacity_shape):
            raise ValueError("resource matrices cannot be empty")
        if len(set(capacity_shape)) != 1:
            raise ValueError("resource matrices must be rectangular")

        capacity_values = tuple(value for column in self.capacity for value in column)
        stock_values = tuple(value for column in self.initial_stock for value in column)
        if not all(math.isfinite(value) for value in capacity_values + stock_values):
            raise ValueError("resource matrices must contain finite values")
        if any(value < 0 for value in capacity_values + stock_values):
            raise ValueError("resource matrices must contain nonnegative values")
        if any(
            stock > capacity for stock, capacity in zip(stock_values, capacity_values, strict=True)
        ):
            raise ValueError("initial_stock cannot exceed capacity")
        return self


type ResourceVariant = Annotated[
    ResourceConfig | ExplicitResourceConfig,
    Field(discriminator="kind"),
]


class AgentConfig(StrictModel):
    count: int = Field(default=1, ge=0)
    initial_positions: tuple[Position, ...] = ((2, 2),)
    initial_energy: float = Field(default=10.0, ge=0)
    viability_target: float = Field(default=10.0, gt=0)
    basal_cost: float = Field(default=1.0, ge=0)
    movement_cost: float = Field(default=0.25, ge=0)
    harvest_capacity: float = Field(default=2.0, ge=0)
    harvest_threshold: float = Field(default=1.0, ge=0)
    conversion_efficiency: float = Field(default=1.0, ge=0)

    @model_validator(mode="after")
    def one_position_per_agent(self) -> Self:
        if len(self.initial_positions) != self.count:
            raise ValueError("initial_positions must contain exactly count positions")
        return self


class LiteralLocalPolicyConfig(StrictModel):
    kind: Literal["literal_local"] = "literal_local"


class NoShockConfig(StrictModel):
    kind: Literal["none"] = "none"


class DamageShockConfig(StrictModel):
    """Fields required by every enabled recoverable shock variant."""

    event_probability: float = Field(ge=0, le=1)
    stock_loss_fraction: float = Field(ge=0, le=1)
    capacity_loss_fraction: float = Field(ge=0, le=1)
    regeneration_suppression_fraction: float = Field(ge=0, le=1)
    recovery_ticks: int = Field(ge=1)


class IndependentShockConfig(DamageShockConfig):
    kind: Literal["independent"] = "independent"


class CorrelatedShockConfig(DamageShockConfig):
    kind: Literal["correlated"] = "correlated"
    spread_probability: float = Field(ge=0, le=1)
    max_spread_ticks: int = Field(ge=0)


class SystemShockConfig(DamageShockConfig):
    kind: Literal["system"] = "system"


type ShockVariant = Annotated[
    NoShockConfig | IndependentShockConfig | CorrelatedShockConfig | SystemShockConfig,
    Field(discriminator="kind"),
]


class AllowAllGateConfig(StrictModel):
    kind: Literal["allow_all"] = "allow_all"


class SimulationConfig(StrictModel):
    schema_version: Literal["0.1.0", "0.2.0"] = "0.1.0"
    seed: int = Field(default=42, ge=0)
    duration: int = Field(default=100, ge=0)
    world: WorldConfig = Field(default_factory=WorldConfig)
    resources: ResourceVariant = Field(default_factory=ResourceConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    policy: LiteralLocalPolicyConfig = Field(default_factory=LiteralLocalPolicyConfig)
    shock: ShockVariant = Field(default_factory=NoShockConfig)
    gate: AllowAllGateConfig = Field(default_factory=AllowAllGateConfig)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_uniform_resources(cls, payload: Any) -> Any:
        """Preserve v0.1 resource mappings written before the discriminator existed."""

        if not isinstance(payload, dict):
            return payload
        resources = payload.get("resources")
        if not isinstance(resources, dict) or "kind" in resources:
            return payload
        normalized = dict(payload)
        normalized["resources"] = {"kind": "uniform", **resources}
        return normalized

    @model_validator(mode="after")
    def positions_fit_world(self) -> Self:
        if isinstance(self.resources, ExplicitResourceConfig):
            if self.schema_version != "0.2.0":
                raise ValueError("explicit landscapes require schema version 0.2.0")
            shape = (len(self.resources.capacity), len(self.resources.capacity[0]))
            world_shape = (self.world.width, self.world.height)
            if shape != world_shape:
                raise ValueError(
                    f"explicit landscape shape {shape} must match world shape {world_shape}"
                )
        if not isinstance(self.shock, NoShockConfig) and self.schema_version != "0.2.0":
            raise ValueError("enabled shocks require schema version 0.2.0")
        for x, y in self.agents.initial_positions:
            if not (0 <= x < self.world.width and 0 <= y < self.world.height):
                raise ValueError(f"initial position {(x, y)} is outside the world")
        return self


def load_config(path: Path) -> SimulationConfig:
    """Load a small YAML mapping and validate it as an executable configuration."""

    if path.stat().st_size > MAX_CONFIG_BYTES:
        raise ValueError(f"configuration exceeds {MAX_CONFIG_BYTES} bytes")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("configuration root must be a mapping")
    return SimulationConfig.model_validate(payload)
