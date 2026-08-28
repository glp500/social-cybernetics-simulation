"""Validated executable configuration for the implemented v0.1 variants."""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Position = tuple[int, int]
MAX_CONFIG_BYTES = 1_048_576


class StrictModel(BaseModel):
    """Base configuration contract that rejects misspelled or future fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class WorldConfig(StrictModel):
    width: int = Field(default=5, ge=1)
    height: int = Field(default=5, ge=1)
    torus: bool = True
    occupancy: Literal["unlimited"] = "unlimited"


class ResourceConfig(StrictModel):
    capacity: float = Field(default=10.0, ge=0)
    initial_stock: float = Field(default=10.0, ge=0)
    regeneration_rate: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def stock_fits_capacity(self) -> Self:
        if self.initial_stock > self.capacity:
            raise ValueError("initial_stock cannot exceed capacity")
        return self


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


class AllowAllGateConfig(StrictModel):
    kind: Literal["allow_all"] = "allow_all"


class SimulationConfig(StrictModel):
    schema_version: Literal["0.1.0"] = "0.1.0"
    seed: int = Field(default=42, ge=0)
    duration: int = Field(default=100, ge=0)
    world: WorldConfig = Field(default_factory=WorldConfig)
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    policy: LiteralLocalPolicyConfig = Field(default_factory=LiteralLocalPolicyConfig)
    shock: NoShockConfig = Field(default_factory=NoShockConfig)
    gate: AllowAllGateConfig = Field(default_factory=AllowAllGateConfig)

    @model_validator(mode="after")
    def positions_fit_world(self) -> Self:
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
