"""Validated Morris designs resolved through the existing deterministic batch contract."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from SALib.sample.morris import sample as sample_morris

from social_cybernetics.batch_config import (
    BatchSpecification,
    ResolvedBatchSpecification,
    deep_merge_configuration,
    resolve_batch_specification,
    validate_configuration_tree,
)
from social_cybernetics.config import SimulationConfig, load_config

MAX_SENSITIVITY_SPEC_BYTES = 1_048_576
ShockScope = Literal["independent", "correlated", "system"]
FactorKind = Literal["float", "integer"]


class _StrictSensitivityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class MorrisDesignSpecification(_StrictSensitivityModel):
    """Seeded controls passed directly to SALib's Morris sampler."""

    kind: Literal["morris"]
    seed: int = Field(ge=0)
    num_levels: int = Field(ge=4)
    candidate_trajectories: int = Field(ge=2)
    selected_trajectories: int = Field(ge=2)
    local_optimization: bool

    @model_validator(mode="after")
    def validate_design(self) -> Self:
        if self.num_levels % 2:
            raise ValueError("Morris num_levels must be even")
        if self.selected_trajectories > self.candidate_trajectories:
            raise ValueError("selected trajectories cannot exceed candidate trajectories")
        return self


class SensitivityFactorSpecification(_StrictSensitivityModel):
    """One declared numeric configuration path and inclusive bounds."""

    path: str = Field(pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
    kind: FactorKind
    lower: float
    upper: float

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.lower >= self.upper:
            raise ValueError("factor lower bound must be less than its upper bound")
        if self.kind == "integer" and (not self.lower.is_integer() or not self.upper.is_integer()):
            raise ValueError("integer factor bounds must be integers")
        return self


class SensitivityScopeSpecification(_StrictSensitivityModel):
    """One active shock variant and its numeric factors."""

    kind: ShockScope
    fixed_overrides: dict[str, Any]
    factors: tuple[SensitivityFactorSpecification, ...] = Field(min_length=1)

    @field_validator("fixed_overrides")
    @classmethod
    def validate_fixed_overrides(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_configuration_tree(value, path="fixed_overrides")
        if "seed" in value:
            raise ValueError("fixed overrides cannot set seed")
        return value

    @model_validator(mode="after")
    def unique_factor_paths(self) -> Self:
        paths = tuple(factor.path for factor in self.factors)
        if len(set(paths)) != len(paths):
            raise ValueError("factor paths must be unique within a scope")
        return self


class SensitivitySpecification(_StrictSensitivityModel):
    """External contract for one scope-stratified Morris experiment."""

    schema_version: Literal["0.1.0"]
    base_config: str = Field(min_length=1, strict=True)
    design: MorrisDesignSpecification
    model_seeds: tuple[int, ...] = Field(min_length=1)
    max_runs: int = Field(ge=1)
    scopes: tuple[SensitivityScopeSpecification, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_identifiers(self) -> Self:
        if any(isinstance(seed, bool) or seed < 0 for seed in self.model_seeds):
            raise ValueError("model seeds must be non-negative integers")
        if len(set(self.model_seeds)) != len(self.model_seeds):
            raise ValueError("model seeds must be unique")
        kinds = tuple(scope.kind for scope in self.scopes)
        if len(set(kinds)) != len(kinds):
            raise ValueError("shock scopes must be unique")
        return self


@dataclass(frozen=True, slots=True)
class ResolvedSensitivityDesign:
    """Validated source controls and their ordinary ordered batch."""

    source_path: Path
    specification: SensitivitySpecification
    batch: ResolvedBatchSpecification


def _path_value(configuration: dict[str, Any], path: str) -> object:
    current: object = configuration
    for component in path.split("."):
        if not isinstance(current, dict) or component not in current:
            raise ValueError(f"factor path does not exist in active configuration: {path}")
        current = current[component]
    return current


def _path_override(path: str, value: int | float) -> dict[str, Any]:
    nested: int | float | dict[str, Any] = value
    for component in reversed(path.split(".")):
        nested = {component: nested}
    if not isinstance(nested, dict):  # pragma: no cover - path validation guarantees a component
        raise AssertionError("factor path did not produce an override mapping")
    return nested


def _validate_factor(
    factor: SensitivityFactorSpecification,
    *,
    scope_payload: dict[str, Any],
) -> None:
    if not factor.path.startswith("shock."):
        raise ValueError(f"factor path must identify a numeric shock parameter: {factor.path}")
    current = _path_value(scope_payload, factor.path)
    if isinstance(current, bool) or not isinstance(current, (int, float)):
        raise ValueError(f"factor path must identify a numeric scalar: {factor.path}")
    if factor.kind == "integer" and not isinstance(current, int):
        raise ValueError(f"integer factor path must identify an integer field: {factor.path}")
    if factor.kind == "float" and not isinstance(current, float):
        raise ValueError(f"float factor path must identify a float field: {factor.path}")
    for bound in (factor.lower, factor.upper):
        value = _factor_value(factor, bound)
        candidate = deep_merge_configuration(scope_payload, _path_override(factor.path, value))
        SimulationConfig.model_validate(candidate)


def _factor_value(factor: SensitivityFactorSpecification, sampled: float) -> int | float:
    if factor.kind == "float":
        return float(sampled)
    rounded = round(sampled)
    if not math.isclose(sampled, rounded, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"integer factor does not land on an exact grid: {factor.path}")
    return int(rounded)


def _scope_payload(
    scope: SensitivityScopeSpecification, *, base_payload: dict[str, Any]
) -> dict[str, Any]:
    payload = deep_merge_configuration(base_payload, scope.fixed_overrides)
    config = SimulationConfig.model_validate(payload)
    if config.shock.kind != scope.kind:
        raise ValueError(f"scope {scope.kind} must activate {scope.kind} shock")
    normalized = config.model_dump(mode="json")
    for factor in scope.factors:
        _validate_factor(factor, scope_payload=normalized)
    return normalized


def _expected_run_count(specification: SensitivitySpecification) -> int:
    trajectories = specification.design.selected_trajectories
    replicates = len(specification.model_seeds)
    return sum(
        (len(scope.factors) + 1) * trajectories * replicates for scope in specification.scopes
    )


def _sample_scope(
    scope: SensitivityScopeSpecification,
    *,
    design: MorrisDesignSpecification,
) -> list[tuple[int | float, ...]]:
    problem = {
        "num_vars": len(scope.factors),
        "names": [factor.path for factor in scope.factors],
        "bounds": [[factor.lower, factor.upper] for factor in scope.factors],
    }
    sampled = sample_morris(
        problem,
        design.candidate_trajectories,
        num_levels=design.num_levels,
        optimal_trajectories=design.selected_trajectories,
        local_optimization=design.local_optimization,
        seed=design.seed,
    )
    return [
        tuple(
            _factor_value(factor, float(value))
            for factor, value in zip(scope.factors, row, strict=True)
        )
        for row in sampled
    ]


def _generated_runs(
    specification: SensitivitySpecification, *, base_payload: dict[str, Any]
) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for scope in specification.scopes:
        _scope_payload(scope, base_payload=base_payload)
        for point_ordinal, point in enumerate(_sample_scope(scope, design=specification.design)):
            sampled_overrides: dict[str, Any] = {}
            for factor, value in zip(scope.factors, point, strict=True):
                sampled_overrides = deep_merge_configuration(
                    sampled_overrides, _path_override(factor.path, value)
                )
            fixed_and_sampled = deep_merge_configuration(scope.fixed_overrides, sampled_overrides)
            for replicate_ordinal, seed in enumerate(specification.model_seeds):
                overrides = copy.deepcopy(fixed_and_sampled)
                overrides["seed"] = seed
                runs.append(
                    {
                        "id": (f"{scope.kind}-p{point_ordinal:03d}-r{replicate_ordinal:02d}"),
                        "overrides": overrides,
                    }
                )
    return runs


def load_sensitivity_design(path: Path) -> ResolvedSensitivityDesign:
    """Load, sample, and fully validate a sensitivity design before any execution."""

    path = Path(path)
    if path.stat().st_size > MAX_SENSITIVITY_SPEC_BYTES:
        raise ValueError(f"sensitivity specification exceeds {MAX_SENSITIVITY_SPEC_BYTES} bytes")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("sensitivity specification root must be a mapping")
    specification = SensitivitySpecification.model_validate(payload)
    expected_runs = _expected_run_count(specification)
    if expected_runs > specification.max_runs:
        raise ValueError(
            f"generated design has {expected_runs} runs and exceeds max_runs "
            f"{specification.max_runs}"
        )

    base_source = Path(specification.base_config)
    base_path = base_source if base_source.is_absolute() else path.parent / base_source
    base_config = load_config(base_path.resolve())
    generated = BatchSpecification.model_validate(
        {
            "schema_version": "0.1.0",
            "base_config": specification.base_config,
            "runs": _generated_runs(
                specification,
                base_payload=base_config.model_dump(mode="json"),
            ),
        }
    )
    batch = resolve_batch_specification(generated, source_directory=path.parent)
    if len(batch.runs) != expected_runs:
        raise ValueError("Morris sampler returned an unexpected number of design points")
    return ResolvedSensitivityDesign(
        source_path=path.resolve(),
        specification=specification,
        batch=batch,
    )
