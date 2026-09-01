"""Strict, deterministic expansion of the canonical Project 1 experiments."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from social_cybernetics.batch_config import (
    BatchSpecification,
    ResolvedBatchRun,
    ResolvedBatchSpecification,
    resolve_batch_specification,
)
from social_cybernetics.config import NoShockConfig, ShockVariant, Study01Config, load_config

MAX_PROJECT1_PLAN_BYTES = 1_048_576
_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_HOMOGENEOUS = {
    "kind": "uniform",
    "capacity": 10.0,
    "initial_stock": 10.0,
    "regeneration_rate": 0.1,
}


class _StrictProject1Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Project1ConditionSpecification(_StrictProject1Model):
    """One scientifically named Project 1 condition."""

    id: str = Field(min_length=1, max_length=64, strict=True)
    agent_count: int = Field(ge=0, le=25, strict=True)
    movement_cost: float = Field(default=0.25, ge=0, strict=True)
    landscape: Literal["homogeneous", "checkerboard"] = "homogeneous"
    shock: ShockVariant = Field(default_factory=NoShockConfig)

    @field_validator("id")
    @classmethod
    def stable_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("condition ID must be lowercase kebab-case")
        return value


class Project1ExperimentGroup(_StrictProject1Model):
    """An ordered comparison whose conditions share seeds and horizon."""

    id: str = Field(min_length=1, max_length=16, strict=True)
    duration: int = Field(ge=1, strict=True)
    conditions: tuple[Project1ConditionSpecification, ...] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def stable_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("experiment ID must be lowercase kebab-case")
        return value

    @model_validator(mode="after")
    def unique_condition_ids(self) -> Self:
        identifiers = tuple(condition.id for condition in self.conditions)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("condition IDs must be unique within an experiment")
        return self


class Project1ExperimentSpecification(_StrictProject1Model):
    """External contract for the complete ordered Project 1 design."""

    study: Literal["project_1"]
    schema_version: Literal["1.0.0"]
    base_config: str = Field(min_length=1, strict=True)
    seeds: tuple[int, ...] = Field(min_length=1)
    expected_runs: int = Field(ge=1, strict=True)
    max_runs: int = Field(ge=1, strict=True)
    groups: tuple[Project1ExperimentGroup, ...] = Field(min_length=1)

    @field_validator("seeds", mode="before")
    @classmethod
    def valid_seeds(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)) or any(
            isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in value
        ):
            raise ValueError("seeds must be non-negative integers")
        if len(set(value)) != len(value):
            raise ValueError("seeds must be unique")
        return value

    @model_validator(mode="after")
    def consistent_design(self) -> Self:
        group_ids = tuple(group.id for group in self.groups)
        if len(set(group_ids)) != len(group_ids):
            raise ValueError("experiment IDs must be unique")
        generated_runs = len(self.seeds) * sum(len(group.conditions) for group in self.groups)
        if generated_runs != self.expected_runs:
            raise ValueError(
                f"expected_runs is {self.expected_runs}, but the design expands to {generated_runs}"
            )
        if generated_runs > self.max_runs:
            raise ValueError(
                f"design expands to {generated_runs} runs and exceeds max_runs {self.max_runs}"
            )
        return self


@dataclass(frozen=True, slots=True)
class ResolvedProject1Run:
    """One study-labelled run backed by a fully resolved batch contract."""

    experiment_id: str
    condition_id: str
    seed: int
    resolved: ResolvedBatchRun

    @property
    def run_id(self) -> str:
        return self.resolved.run_id


@dataclass(frozen=True, slots=True)
class ResolvedProject1Design:
    """Validated Project 1 plan, ordinary batch plan, and ordered run crosswalk."""

    source_path: Path
    specification: Project1ExperimentSpecification
    batch: ResolvedBatchSpecification
    runs: tuple[ResolvedProject1Run, ...]


def _checkerboard() -> dict[str, object]:
    capacity = [
        [10.0 if (x, y) == (2, 2) else (5.0 if (x + y) % 2 == 0 else 15.0) for y in range(5)]
        for x in range(5)
    ]
    return {
        "kind": "explicit",
        "capacity": capacity,
        "initial_stock": capacity,
        "regeneration_rate": 0.1,
    }


def _row_major_positions(count: int) -> list[list[int]]:
    positions = [[x, y] for y in range(5) for x in range(5)]
    return positions[:count]


def _validate_base_fixture(base: Study01Config) -> None:
    expected_world = (5, 5, True, "unlimited")
    actual_world = (base.world.width, base.world.height, base.world.torus, base.world.occupancy)
    if actual_world != expected_world:
        raise ValueError("Project 1 experiments require the canonical 5x5 torus")
    physiology = (
        base.agents.initial_energy,
        base.agents.viability_target,
        base.agents.basal_cost,
        base.agents.harvest_capacity,
        base.agents.harvest_threshold,
        base.agents.conversion_efficiency,
    )
    if physiology != (10.0, 10.0, 1.0, 2.0, 1.0, 1.0):
        raise ValueError("Project 1 base config does not match the frozen physiology")
    if base.policy.kind != "literal_local" or base.gate.kind != "allow_all":
        raise ValueError("Project 1 experiments require the fixed policy and allow-all gate")


def _condition_overrides(
    condition: Project1ConditionSpecification, *, duration: int, seed: int
) -> dict[str, object]:
    resources = _HOMOGENEOUS if condition.landscape == "homogeneous" else _checkerboard()
    return {
        "seed": seed,
        "duration": duration,
        "resources": resources,
        "agents": {
            "count": condition.agent_count,
            "initial_positions": _row_major_positions(condition.agent_count),
            "movement_cost": condition.movement_cost,
        },
        "shock": condition.shock.model_dump(mode="json"),
    }


def _batch_specification(
    specification: Project1ExperimentSpecification,
) -> tuple[BatchSpecification, tuple[tuple[str, str, int], ...]]:
    runs: list[dict[str, object]] = []
    identities: list[tuple[str, str, int]] = []
    for group in specification.groups:
        for condition in group.conditions:
            for seed in specification.seeds:
                runs.append(
                    {
                        "id": f"{group.id}-{condition.id}-seed-{seed}",
                        "overrides": _condition_overrides(
                            condition, duration=group.duration, seed=seed
                        ),
                    }
                )
                identities.append((group.id, condition.id, seed))
    batch = BatchSpecification.model_validate(
        {
            "schema_version": "0.1.0",
            "base_config": specification.base_config,
            "runs": runs,
        }
    )
    return batch, tuple(identities)


def load_project1_design(path: Path) -> ResolvedProject1Design:
    """Load and validate every canonical run before any model execution."""

    path = Path(path)
    if path.stat().st_size > MAX_PROJECT1_PLAN_BYTES:
        raise ValueError(f"Project 1 plan exceeds {MAX_PROJECT1_PLAN_BYTES} bytes")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Project 1 experiment plan root must be a mapping")
    specification = Project1ExperimentSpecification.model_validate(payload)
    base_source = Path(specification.base_config)
    base_path = base_source if base_source.is_absolute() else path.parent / base_source
    _validate_base_fixture(load_config(base_path.resolve()))
    batch_specification, identities = _batch_specification(specification)
    batch = resolve_batch_specification(batch_specification, source_directory=path.parent)
    runs = tuple(
        ResolvedProject1Run(experiment_id, condition_id, seed, resolved)
        for (experiment_id, condition_id, seed), resolved in zip(
            identities, batch.runs, strict=True
        )
    )
    return ResolvedProject1Design(path.resolve(), specification, batch, runs)
