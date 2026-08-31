"""Read validated published artifacts into pure Project 1 analysis contracts."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from netCDF4 import Dataset

from social_cybernetics.artifact_io import (
    file_descriptor,
    read_json_object,
    sha256_file,
    write_json,
)
from social_cybernetics.batch import validate_batch_bundle
from social_cybernetics.domain import (
    ActionKind,
    AgentSnapshot,
    AgentTransitionRecord,
    CohortRecord,
)
from social_cybernetics.persistence import publish_directory_atomically, validate_run_bundle
from social_cybernetics.persistence_errors import BundleValidationError
from social_cybernetics.project1_experiments import ResolvedProject1Design

from .project1_aggregate import condition_summaries, paired_differences
from .project1_outcome import Project1Outcome, calculate_project1_outcome

PROJECT1_ANALYSIS_BUNDLE_SCHEMA = "scs-project1-analysis-bundle/v1.1.0"
PROJECT1_OUTCOMES_SCHEMA = "scs-project1-outcomes/v1.0.0"
PROJECT1_OUTCOME_TABLE_SCHEMA = "scs-project1-outcome-table/v1.0.0"
PROJECT1_CONDITION_SUMMARIES_SCHEMA = "scs-project1-condition-summaries/v1.0.0"
PROJECT1_CONDITION_SUMMARY_TABLE_SCHEMA = "scs-project1-condition-summary-table/v1.0.0"
PROJECT1_PAIRED_DIFFERENCES_SCHEMA = "scs-project1-paired-differences/v1.0.0"
PROJECT1_PAIRED_DIFFERENCE_TABLE_SCHEMA = "scs-project1-paired-difference-table/v1.0.0"
PROJECT1_ANALYSIS_SUMMARY_SCHEMA = "scs-project1-analysis-summary/v1.0.0"
_MAX_ANALYSIS_JSON_BYTES = 64 * 1024 * 1024
_ANALYSIS_ROOT_ENTRIES = {
    "manifest.json",
    "outcomes.json",
    "outcomes.parquet",
    "condition_summaries.json",
    "condition_summaries.parquet",
    "paired_differences.json",
    "paired_differences.parquet",
}

_OUTCOME_SCHEMA = pa.schema(
    [
        pa.field("ordinal", pa.int64(), nullable=False),
        pa.field("experiment_id", pa.string(), nullable=False),
        pa.field("condition_id", pa.string(), nullable=False),
        pa.field("run_id", pa.string(), nullable=False),
        pa.field("seed", pa.int64(), nullable=False),
        pa.field("duration", pa.int64(), nullable=False),
        pa.field("configuration_sha256", pa.string(), nullable=False),
        pa.field("aggregate_harvest", pa.float64(), nullable=False),
        pa.field("survival_fraction", pa.float64(), nullable=False),
        pa.field("mean_unmet_need", pa.float64(), nullable=False),
        pa.field("shortfall_frequency", pa.float64(), nullable=False),
        pa.field("mean_spell_length", pa.float64(), nullable=False),
        pa.field("mean_shortfall_depth", pa.float64(), nullable=False),
        pa.field("maximum_shortfall_depth", pa.float64(), nullable=False),
        pa.field("catastrophic_shortfall_probability", pa.float64(), nullable=False),
        pa.field("harvest_gini", pa.float64(), nullable=False),
        pa.field("energy_gini", pa.float64(), nullable=False),
        pa.field("unmet_need_gini", pa.float64(), nullable=False),
        pa.field("top_harvest_share", pa.float64(), nullable=False),
        pa.field("bottom_shortfall_share", pa.float64(), nullable=False),
        pa.field("rank_autocorrelation", pa.float64()),
        pa.field("rank_autocorrelation_reason", pa.string()),
        pa.field("mean_advantage_duration", pa.float64(), nullable=False),
        pa.field("maximum_advantage_duration", pa.int64(), nullable=False),
        pa.field("inequality_half_life", pa.int64(), nullable=False),
        pa.field("inequality_half_life_peak_tick", pa.int64(), nullable=False),
        pa.field("inequality_half_life_censored", pa.bool_(), nullable=False),
        pa.field("final_resource_depletion", pa.float64(), nullable=False),
        pa.field("mean_resource_depletion", pa.float64(), nullable=False),
        pa.field("maximum_resource_depletion", pa.float64(), nullable=False),
        pa.field("final_capacity_deficit", pa.float64(), nullable=False),
        pa.field("mean_capacity_deficit", pa.float64(), nullable=False),
        pa.field("maximum_capacity_deficit", pa.float64(), nullable=False),
        pa.field("final_regeneration_deficit", pa.float64(), nullable=False),
        pa.field("mean_regeneration_deficit", pa.float64(), nullable=False),
        pa.field("maximum_regeneration_deficit", pa.float64(), nullable=False),
        pa.field("observed_mean_recovery_duration", pa.float64(), nullable=False),
        pa.field("completed_mean_recovery_duration", pa.float64(), nullable=False),
        pa.field("cumulative_capacity_deficit", pa.float64(), nullable=False),
        pa.field("cumulative_regeneration_deficit", pa.float64(), nullable=False),
        pa.field("cumulative_recovery_deficit", pa.float64(), nullable=False),
    ],
    metadata={
        b"scs.table_name": b"project1_outcomes",
        b"scs.schema_version": PROJECT1_OUTCOME_TABLE_SCHEMA.encode(),
    },
)

_CONDITION_SUMMARY_SCHEMA = pa.schema(
    [
        pa.field("experiment_id", pa.string(), nullable=False),
        pa.field("condition_id", pa.string(), nullable=False),
        pa.field("metric", pa.string(), nullable=False),
        pa.field("defined_count", pa.int64(), nullable=False),
        pa.field("undefined_count", pa.int64(), nullable=False),
        pa.field("mean", pa.float64()),
        pa.field("median", pa.float64()),
        pa.field("sample_std", pa.float64()),
        pa.field("minimum", pa.float64()),
        pa.field("maximum", pa.float64()),
    ],
    metadata={
        b"scs.table_name": b"project1_condition_summaries",
        b"scs.schema_version": PROJECT1_CONDITION_SUMMARY_TABLE_SCHEMA.encode(),
    },
)

_PAIRED_DIFFERENCE_SCHEMA = pa.schema(
    [
        pa.field("experiment_id", pa.string(), nullable=False),
        pa.field("reference_condition_id", pa.string(), nullable=False),
        pa.field("condition_id", pa.string(), nullable=False),
        pa.field("seed", pa.int64(), nullable=False),
        pa.field("metric", pa.string(), nullable=False),
        pa.field("reference_value", pa.float64()),
        pa.field("condition_value", pa.float64()),
        pa.field("difference", pa.float64()),
        pa.field("defined", pa.bool_(), nullable=False),
        pa.field("undefined_reason", pa.string()),
    ],
    metadata={
        b"scs.table_name": b"project1_paired_differences",
        b"scs.schema_version": PROJECT1_PAIRED_DIFFERENCE_TABLE_SCHEMA.encode(),
    },
)


def _read_transitions(bundle: Path) -> tuple[AgentTransitionRecord, ...]:
    rows = pq.read_table(bundle / "tables/agent_transitions.parquet").to_pylist()
    return tuple(
        AgentTransitionRecord(
            tick=row["tick"],
            agent_id=row["agent_id"],
            origin=(row["origin_x"], row["origin_y"]),
            observed_stock=row["observed_stock"],
            believed_stock=row["believed_stock"],
            intent_kind=ActionKind(row["intent_kind"]),
            requested_amount=row["requested_amount"],
            intended_destination=(
                (row["intended_destination_x"], row["intended_destination_y"])
                if row["intended_destination_x"] is not None
                else None
            ),
            gate_allowed=row["gate_allowed"],
            harvested=row["harvested"],
            moved=row["moved"],
            final_position=(row["final_position_x"], row["final_position_y"]),
            energy_before=row["energy_before"],
            energy_after=row["energy_after"],
            shortfall=row["shortfall"],
            died=row["died"],
        )
        for row in rows
    )


def _read_cohort(bundle: Path) -> tuple[CohortRecord, ...]:
    rows = pq.read_table(bundle / "tables/cohort.parquet").to_pylist()
    return tuple(
        CohortRecord(
            row["tick"],
            AgentSnapshot(
                tick=row["tick"],
                agent_id=row["agent_id"],
                position=(row["position_x"], row["position_y"]),
                energy=row["energy"],
                alive=row["alive"],
            ),
        )
        for row in rows
    )


def analyze_run_bundle(bundle: Path) -> Project1Outcome:
    """Validate and analyze one published Project 1 run without model access."""

    bundle = Path(bundle)
    manifest = validate_run_bundle(bundle)
    transitions = _read_transitions(bundle)
    cohort = _read_cohort(bundle)
    with Dataset(bundle / "spatial.nc", "r") as spatial:
        return calculate_project1_outcome(
            seed=manifest["seed"],
            completed_ticks=manifest["completed_ticks"],
            transitions=transitions,
            cohort=cohort,
            resource_stock=spatial.variables["resource_stock"][:],
            effective_capacity=spatial.variables["effective_capacity"][:],
            effective_regeneration=spatial.variables["effective_regeneration"][:],
            recovery_remaining=spatial.variables["recovery_remaining"][:],
            baseline_capacity=spatial.variables["baseline_capacity"][:],
            baseline_regeneration=spatial.variables["baseline_regeneration"][:],
        )


def _mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BundleValidationError(f"{name} must be an object")
    return value


def _flatten_outcome_record(record: Mapping[str, Any]) -> dict[str, object]:
    outcome = _mapping(record.get("outcome"), name="Project 1 outcome")
    subsistence = _mapping(outcome.get("subsistence"), name="subsistence outcome")
    distribution = _mapping(outcome.get("distribution"), name="distribution outcome")
    persistence = _mapping(outcome.get("persistence"), name="persistence outcome")
    ecology = _mapping(outcome.get("ecology"), name="ecology outcome")
    rank = _mapping(persistence.get("material_rank_autocorrelation"), name="rank autocorrelation")
    advantage = _mapping(persistence.get("advantage_duration"), name="advantage duration")
    half_life = _mapping(persistence.get("inequality_half_life"), name="inequality half-life")
    resource = _mapping(ecology.get("resource_depletion"), name="resource depletion")
    capacity = _mapping(ecology.get("capacity_deficit"), name="capacity deficit")
    regeneration = _mapping(ecology.get("regeneration_deficit"), name="regeneration deficit")
    top_share = _mapping(distribution.get("top_10_percent_harvest_share"), name="top harvest share")
    bottom_share = _mapping(
        distribution.get("bottom_25_percent_shortfall_share"), name="bottom shortfall share"
    )
    return {
        "ordinal": record.get("ordinal"),
        "experiment_id": record.get("experiment_id"),
        "condition_id": record.get("condition_id"),
        "run_id": record.get("run_id"),
        "seed": record.get("seed"),
        "duration": outcome.get("completed_ticks"),
        "configuration_sha256": record.get("configuration_sha256"),
        "aggregate_harvest": outcome.get("aggregate_harvest"),
        "survival_fraction": outcome.get("survival_fraction"),
        "mean_unmet_need": outcome.get("mean_unmet_need"),
        "shortfall_frequency": subsistence.get("shortfall_frequency"),
        "mean_spell_length": subsistence.get("mean_spell_length"),
        "mean_shortfall_depth": subsistence.get("mean_shortfall_depth"),
        "maximum_shortfall_depth": subsistence.get("maximum_shortfall_depth"),
        "catastrophic_shortfall_probability": subsistence.get("catastrophic_shortfall_probability"),
        "harvest_gini": distribution.get("harvest_gini"),
        "energy_gini": distribution.get("energy_gini"),
        "unmet_need_gini": distribution.get("unmet_need_gini"),
        "top_harvest_share": top_share.get("value"),
        "bottom_shortfall_share": bottom_share.get("value"),
        "rank_autocorrelation": rank.get("value"),
        "rank_autocorrelation_reason": rank.get("reason"),
        "mean_advantage_duration": advantage.get("mean"),
        "maximum_advantage_duration": advantage.get("maximum"),
        "inequality_half_life": half_life.get("value"),
        "inequality_half_life_peak_tick": half_life.get("peak_tick"),
        "inequality_half_life_censored": half_life.get("right_censored"),
        "final_resource_depletion": resource.get("final"),
        "mean_resource_depletion": resource.get("mean"),
        "maximum_resource_depletion": resource.get("maximum"),
        "final_capacity_deficit": capacity.get("final"),
        "mean_capacity_deficit": capacity.get("mean"),
        "maximum_capacity_deficit": capacity.get("maximum"),
        "final_regeneration_deficit": regeneration.get("final"),
        "mean_regeneration_deficit": regeneration.get("mean"),
        "maximum_regeneration_deficit": regeneration.get("maximum"),
        "observed_mean_recovery_duration": ecology.get("observed_mean_recovery_duration"),
        "completed_mean_recovery_duration": ecology.get("completed_mean_recovery_duration"),
        "cumulative_capacity_deficit": ecology.get("cumulative_capacity_deficit"),
        "cumulative_regeneration_deficit": ecology.get("cumulative_regeneration_deficit"),
        "cumulative_recovery_deficit": ecology.get("cumulative_recovery_deficit"),
    }


def _validate_design_matches_batch(design: ResolvedProject1Design, batch: Path) -> None:
    manifest = validate_batch_bundle(batch)
    if manifest["failed_runs"] != 0:
        raise BundleValidationError("Project 1 analysis requires a fully completed batch")
    normalized = read_json_object(
        batch / "batch_specification.json", max_bytes=_MAX_ANALYSIS_JSON_BYTES
    )
    batch_runs = normalized.get("runs")
    if not isinstance(batch_runs, list) or len(batch_runs) != len(design.runs):
        raise BundleValidationError("Project 1 design and batch run counts differ")
    for planned, published in zip(design.runs, batch_runs, strict=True):
        run = _mapping(published, name="published batch run")
        if (
            run.get("run_id") != planned.run_id
            or run.get("configuration_sha256") != planned.resolved.configuration_sha256
        ):
            raise BundleValidationError("Project 1 design differs from published batch provenance")


def _outcome_records(design: ResolvedProject1Design, batch: Path) -> list[dict[str, object]]:
    return [
        {
            "ordinal": run.resolved.ordinal,
            "experiment_id": run.experiment_id,
            "condition_id": run.condition_id,
            "run_id": run.run_id,
            "seed": run.seed,
            "configuration_sha256": run.resolved.configuration_sha256,
            "outcome": analyze_run_bundle(batch / "runs" / run.run_id).as_payload(),
        }
        for run in design.runs
    ]


def _write_parquet(path: Path, rows: list[dict[str, object]], schema: pa.Schema) -> None:
    table = pa.Table.from_pylist(rows, schema)
    pq.write_table(
        table,
        path,
        version="2.6",
        compression="zstd",
        write_page_checksum=True,
    )


def _analysis_file_descriptors(staging: Path) -> dict[str, dict[str, object]]:
    schemas = {
        "outcomes.json": PROJECT1_OUTCOMES_SCHEMA,
        "outcomes.parquet": PROJECT1_OUTCOME_TABLE_SCHEMA,
        "condition_summaries.json": PROJECT1_CONDITION_SUMMARIES_SCHEMA,
        "condition_summaries.parquet": PROJECT1_CONDITION_SUMMARY_TABLE_SCHEMA,
        "paired_differences.json": PROJECT1_PAIRED_DIFFERENCES_SCHEMA,
        "paired_differences.parquet": PROJECT1_PAIRED_DIFFERENCE_TABLE_SCHEMA,
    }
    return {
        name: file_descriptor(staging / name, schema_version=schema)
        for name, schema in schemas.items()
    }


def analyze_project1_batch(
    design: ResolvedProject1Design, batch: Path, destination: Path
) -> dict[str, object]:
    """Analyze a matching published batch and atomically publish Project 1 outcomes."""

    batch = Path(batch)
    _validate_design_matches_batch(design, batch)
    records = _outcome_records(design, batch)
    flat_rows = [_flatten_outcome_record(record) for record in records]
    summaries = condition_summaries(flat_rows)
    differences = paired_differences(flat_rows)
    summary = {
        "schema_version": PROJECT1_ANALYSIS_SUMMARY_SCHEMA,
        "status": "completed",
        "run_count": len(records),
    }

    def build(staging: Path) -> None:
        write_json(
            staging / "outcomes.json",
            {"schema_version": PROJECT1_OUTCOMES_SCHEMA, "runs": records},
        )
        write_json(
            staging / "condition_summaries.json",
            {
                "schema_version": PROJECT1_CONDITION_SUMMARIES_SCHEMA,
                "summaries": summaries,
            },
        )
        write_json(
            staging / "paired_differences.json",
            {
                "schema_version": PROJECT1_PAIRED_DIFFERENCES_SCHEMA,
                "contrasts": differences,
            },
        )
        _write_parquet(staging / "outcomes.parquet", flat_rows, _OUTCOME_SCHEMA)
        _write_parquet(
            staging / "condition_summaries.parquet", summaries, _CONDITION_SUMMARY_SCHEMA
        )
        _write_parquet(
            staging / "paired_differences.parquet", differences, _PAIRED_DIFFERENCE_SCHEMA
        )
        write_json(
            staging / "manifest.json",
            {
                "schema_version": PROJECT1_ANALYSIS_BUNDLE_SCHEMA,
                "status": "completed",
                "run_count": len(records),
                "condition_summary_count": len(summaries),
                "paired_difference_count": len(differences),
                "plan_sha256": sha256_file(design.source_path),
                "batch_manifest_sha256": sha256_file(batch / "batch_manifest.json"),
                "files": _analysis_file_descriptors(staging),
            },
        )
        validate_project1_analysis_bundle(staging)

    publish_directory_atomically(destination, build)
    return summary


def _validated_json_rows(
    bundle: Path, filename: str, schema_version: str, collection: str
) -> list[object]:
    payload = read_json_object(bundle / filename, max_bytes=_MAX_ANALYSIS_JSON_BYTES)
    rows = payload.get(collection)
    if (
        set(payload) != {"schema_version", collection}
        or payload.get("schema_version") != schema_version
        or not isinstance(rows, list)
    ):
        raise BundleValidationError(f"Project 1 {filename} differs from its schema")
    return rows


def _validate_parquet_matches(
    bundle: Path,
    filename: str,
    rows: list[dict[str, object]],
    schema: pa.Schema,
) -> None:
    expected = pa.Table.from_pylist(rows, schema)
    try:
        actual = pq.read_table(bundle / filename)
    except Exception as error:
        raise BundleValidationError(f"cannot read Project 1 table: {filename}") from error
    if not actual.schema.equals(schema, check_metadata=True) or not actual.equals(
        expected, check_metadata=True
    ):
        raise BundleValidationError(f"Project 1 JSON and Parquet differ: {filename}")


def _validated_analysis_manifest(bundle: Path) -> dict[str, Any]:
    if not bundle.is_dir() or {path.name for path in bundle.iterdir()} != _ANALYSIS_ROOT_ENTRIES:
        raise BundleValidationError("Project 1 analysis bundle entries differ from its schema")
    if any(path.is_symlink() for path in bundle.iterdir()):
        raise BundleValidationError("Project 1 analysis bundle cannot contain symbolic links")
    manifest = read_json_object(bundle / "manifest.json", max_bytes=_MAX_ANALYSIS_JSON_BYTES)
    if (
        set(manifest)
        != {
            "schema_version",
            "status",
            "run_count",
            "condition_summary_count",
            "paired_difference_count",
            "plan_sha256",
            "batch_manifest_sha256",
            "files",
        }
        or manifest.get("schema_version") != PROJECT1_ANALYSIS_BUNDLE_SCHEMA
    ):
        raise BundleValidationError("Project 1 analysis manifest differs from its schema")
    return manifest


def _validate_analysis_descriptors(bundle: Path, manifest: Mapping[str, Any]) -> None:
    files = _mapping(manifest.get("files"), name="analysis files")
    expected_schemas = {
        "outcomes.json": PROJECT1_OUTCOMES_SCHEMA,
        "outcomes.parquet": PROJECT1_OUTCOME_TABLE_SCHEMA,
        "condition_summaries.json": PROJECT1_CONDITION_SUMMARIES_SCHEMA,
        "condition_summaries.parquet": PROJECT1_CONDITION_SUMMARY_TABLE_SCHEMA,
        "paired_differences.json": PROJECT1_PAIRED_DIFFERENCES_SCHEMA,
        "paired_differences.parquet": PROJECT1_PAIRED_DIFFERENCE_TABLE_SCHEMA,
    }
    if set(files) != set(expected_schemas):
        raise BundleValidationError("Project 1 analysis file set differs from its schema")
    for name, schema_version in expected_schemas.items():
        descriptor = _mapping(files[name], name="analysis file descriptor")
        path = bundle / name
        if (
            set(descriptor) != {"schema_version", "byte_count", "sha256"}
            or descriptor.get("schema_version") != schema_version
            or descriptor.get("byte_count") != path.stat().st_size
            or descriptor.get("sha256") != sha256_file(path)
        ):
            raise BundleValidationError(f"Project 1 analysis descriptor is invalid: {name}")


def _validated_outcome_rows(bundle: Path, manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    runs = _validated_json_rows(bundle, "outcomes.json", PROJECT1_OUTCOMES_SCHEMA, "runs")
    if len(runs) != manifest.get("run_count") or manifest.get("status") != "completed":
        raise BundleValidationError("Project 1 JSON outcomes differ from their schema")
    flat_rows = [_flatten_outcome_record(_mapping(run, name="outcome record")) for run in runs]
    _validate_parquet_matches(bundle, "outcomes.parquet", flat_rows, _OUTCOME_SCHEMA)
    return flat_rows


def _validate_condition_summaries(
    bundle: Path, manifest: Mapping[str, Any], flat_rows: list[dict[str, object]]
) -> None:
    published_summaries = _validated_json_rows(
        bundle,
        "condition_summaries.json",
        PROJECT1_CONDITION_SUMMARIES_SCHEMA,
        "summaries",
    )
    try:
        expected_summaries = condition_summaries(flat_rows)
    except ValueError as error:
        raise BundleValidationError("Project 1 summary inputs are invalid") from error
    if published_summaries != expected_summaries or len(published_summaries) != manifest.get(
        "condition_summary_count"
    ):
        raise BundleValidationError("Project 1 condition summaries are invalid")
    _validate_parquet_matches(
        bundle, "condition_summaries.parquet", expected_summaries, _CONDITION_SUMMARY_SCHEMA
    )


def _validate_paired_differences(
    bundle: Path, manifest: Mapping[str, Any], flat_rows: list[dict[str, object]]
) -> None:
    published_differences = _validated_json_rows(
        bundle,
        "paired_differences.json",
        PROJECT1_PAIRED_DIFFERENCES_SCHEMA,
        "contrasts",
    )
    try:
        expected_differences = paired_differences(flat_rows)
    except ValueError as error:
        raise BundleValidationError("Project 1 paired inputs are invalid") from error
    if published_differences != expected_differences or len(published_differences) != manifest.get(
        "paired_difference_count"
    ):
        raise BundleValidationError("Project 1 paired differences are invalid")
    _validate_parquet_matches(
        bundle, "paired_differences.parquet", expected_differences, _PAIRED_DIFFERENCE_SCHEMA
    )


def validate_project1_analysis_bundle(bundle: Path) -> dict[str, Any]:
    """Validate Project 1 aggregate schemas, digests, and JSON/Parquet agreement."""

    bundle = Path(bundle)
    manifest = _validated_analysis_manifest(bundle)
    _validate_analysis_descriptors(bundle, manifest)
    flat_rows = _validated_outcome_rows(bundle, manifest)
    _validate_condition_summaries(bundle, manifest, flat_rows)
    _validate_paired_differences(bundle, manifest, flat_rows)
    return manifest
