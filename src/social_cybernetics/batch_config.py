"""Validated deterministic batch specifications and recursive configuration overrides."""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from social_cybernetics.artifact_io import canonical_payload_sha256
from social_cybernetics.config import SimulationConfig, load_config

MAX_BATCH_SPEC_BYTES = 1_048_576
_RUN_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class _StrictBatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class BatchRunSpecification(_StrictBatchModel):
    """One stable run identifier and its explicit configuration overrides."""

    id: str = Field(min_length=1, max_length=64, strict=True)
    overrides: dict[str, Any]

    @field_validator("id")
    @classmethod
    def validate_run_id(cls, value: str) -> str:
        if _RUN_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("run ID must be lowercase kebab-case")
        return value

    @field_validator("overrides")
    @classmethod
    def validate_overrides(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_configuration_tree(value, path="overrides")
        seed = value.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("every run override requires an explicit top-level integer seed")
        return value


class BatchSpecification(_StrictBatchModel):
    """External YAML contract for one ordered deterministic batch."""

    schema_version: Literal["0.1.0"]
    base_config: str = Field(min_length=1, strict=True)
    runs: tuple[BatchRunSpecification, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_run_ids(self) -> Self:
        identifiers = tuple(run.id for run in self.runs)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("batch run IDs must be unique")
        return self


@dataclass(frozen=True, slots=True)
class ResolvedBatchRun:
    """One fully validated run in declared execution order."""

    ordinal: int
    run_id: str
    overrides: dict[str, Any]
    config: SimulationConfig
    configuration_sha256: str


@dataclass(frozen=True, slots=True)
class ResolvedBatchSpecification:
    """A validated base configuration and every resolved run configuration."""

    source_schema_version: str
    base_config_source: str
    base_config_path: Path
    base_config: SimulationConfig
    runs: tuple[ResolvedBatchRun, ...]


def validate_configuration_tree(value: object, *, path: str) -> None:
    """Reject configuration values that cannot be represented portably in YAML/JSON."""

    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain only finite numbers")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_configuration_tree(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} mapping keys must be strings")
            validate_configuration_tree(item, path=f"{path}.{key}")
        return
    raise ValueError(f"{path} contains an unsupported YAML value: {type(value).__name__}")


def deep_merge_configuration(
    base: Mapping[str, Any], override: Mapping[str, Any]
) -> dict[str, Any]:
    """Recursively merge mappings while replacing scalar and list values completely."""

    merged = copy.deepcopy(dict(base))
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = deep_merge_configuration(existing, value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _configuration_digest(config: SimulationConfig) -> str:
    return canonical_payload_sha256(config.model_dump(mode="json"))


def load_batch_specification(path: Path) -> ResolvedBatchSpecification:
    """Load and fully resolve a batch before any model execution or output staging."""

    path = Path(path)
    if path.stat().st_size > MAX_BATCH_SPEC_BYTES:
        raise ValueError(f"batch specification exceeds {MAX_BATCH_SPEC_BYTES} bytes")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("batch specification root must be a mapping")
    specification = BatchSpecification.model_validate(payload)

    return resolve_batch_specification(specification, source_directory=path.parent)


def resolve_batch_specification(
    specification: BatchSpecification, *, source_directory: Path
) -> ResolvedBatchSpecification:
    """Resolve an already validated batch contract relative to its source directory."""

    base_source = Path(specification.base_config)
    base_path = base_source if base_source.is_absolute() else Path(source_directory) / base_source
    base_path = base_path.resolve()
    base_config = load_config(base_path)
    base_payload = base_config.model_dump(mode="json")

    resolved_runs: list[ResolvedBatchRun] = []
    for ordinal, run in enumerate(specification.runs):
        merged = deep_merge_configuration(base_payload, run.overrides)
        config = SimulationConfig.model_validate(merged)
        resolved_runs.append(
            ResolvedBatchRun(
                ordinal=ordinal,
                run_id=run.id,
                overrides=copy.deepcopy(run.overrides),
                config=config,
                configuration_sha256=_configuration_digest(config),
            )
        )
    return ResolvedBatchSpecification(
        source_schema_version=specification.schema_version,
        base_config_source=specification.base_config,
        base_config_path=base_path,
        base_config=base_config,
        runs=tuple(resolved_runs),
    )
