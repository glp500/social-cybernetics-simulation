"""Sequential deterministic batch execution and validated aggregate bundles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pyarrow as pa
import pyarrow.parquet as pq

from social_cybernetics.artifact_io import (
    canonical_payload_sha256,
    file_descriptor,
    read_json_object,
    sha256_file,
    write_json,
)
from social_cybernetics.batch_config import (
    BatchRunSpecification,
    ResolvedBatchRun,
    ResolvedBatchSpecification,
    deep_merge_configuration,
)
from social_cybernetics.config import SimulationConfig
from social_cybernetics.domain import InvariantViolationError
from social_cybernetics.persistence import (
    BUNDLE_SCHEMA_VERSION,
    BundlePublicationError,
    RunBundleSession,
    RunRecords,
    publish_directory_atomically,
    validate_run_bundle,
    validate_summary_payload,
)
from social_cybernetics.persistence_errors import BundleValidationError
from social_cybernetics.runtime.mesa import SugarscapeModel

BATCH_BUNDLE_SCHEMA_VERSION = "scs-batch-bundle/v0.1.0"
NORMALIZED_BATCH_SCHEMA_VERSION = "scs-normalized-batch/v0.1.0"
BATCH_INDEX_SCHEMA_VERSION = "scs-batch-run-index/v0.1.0"
BATCH_SUMMARY_SCHEMA_VERSION = "scs-batch-summary/v0.1.0"
_MAX_JSON_BYTES = 64 * 1024 * 1024
_BATCH_ROOT_ENTRIES = {
    "batch_manifest.json",
    "batch_specification.json",
    "runs.json",
    "runs.parquet",
    "runs",
}
_BATCH_MANIFEST_FIELDS = {
    "schema_version",
    "status",
    "total_runs",
    "completed_runs",
    "failed_runs",
    "files",
    "runs",
}
_NORMALIZED_BATCH_FIELDS = {
    "schema_version",
    "source_schema_version",
    "base_config_source",
    "base_configuration",
    "runs",
}
_NORMALIZED_RUN_FIELDS = {
    "ordinal",
    "run_id",
    "overrides",
    "configuration_sha256",
    "configuration",
}
_INDEX_RECORD_FIELDS = {
    "ordinal",
    "run_id",
    "status",
    "seed",
    "configuration_sha256",
    "bundle_path",
    "summary",
    "error",
}
_RUN_DESCRIPTOR_FIELDS = {
    "ordinal",
    "run_id",
    "status",
    "bundle_path",
    "run_bundle_schema_version",
    "manifest_sha256",
}
_ARTIFACT_SCHEMAS = {
    "batch_specification.json": NORMALIZED_BATCH_SCHEMA_VERSION,
    "runs.json": BATCH_INDEX_SCHEMA_VERSION,
    "runs.parquet": BATCH_INDEX_SCHEMA_VERSION,
}

_INDEX_SCHEMA = pa.schema(
    [
        pa.field("ordinal", pa.int64(), nullable=False),
        pa.field("run_id", pa.string(), nullable=False),
        pa.field("status", pa.string(), nullable=False),
        pa.field("seed", pa.int64(), nullable=False),
        pa.field("configuration_sha256", pa.string(), nullable=False),
        pa.field("bundle_path", pa.string()),
        pa.field("error_kind", pa.string()),
        pa.field("error_message", pa.string()),
        pa.field("summary_schema_version", pa.string()),
        pa.field("completed_ticks", pa.int64()),
        pa.field("alive_count", pa.int64()),
        pa.field("dead_count", pa.int64()),
        pa.field("total_resources", pa.float64()),
        pa.field("cohort_mean_energy", pa.float64()),
        pa.field("total_harvest", pa.float64()),
        pa.field("unmet_need", pa.float64()),
        pa.field("energy_gini", pa.float64()),
        pa.field("harvest_gini", pa.float64()),
        pa.field("unmet_need_gini", pa.float64()),
    ],
    metadata={
        b"scs.table_name": b"batch_runs",
        b"scs.schema_version": BATCH_INDEX_SCHEMA_VERSION.encode(),
    },
)


@dataclass(frozen=True, slots=True)
class BatchExecutionResult:
    """Stable process result returned after a complete batch attempt is published."""

    status: Literal["completed", "completed_with_failures"]
    total_runs: int
    completed_runs: int
    failed_runs: int

    def summary(self) -> dict[str, object]:
        return {
            "schema_version": BATCH_SUMMARY_SCHEMA_VERSION,
            "status": self.status,
            "total_runs": self.total_runs,
            "completed_runs": self.completed_runs,
            "failed_runs": self.failed_runs,
        }


def _configuration_digest(configuration: Mapping[str, object]) -> str:
    return canonical_payload_sha256(configuration)


def _normalized_batch(specification: ResolvedBatchSpecification) -> dict[str, object]:
    return {
        "schema_version": NORMALIZED_BATCH_SCHEMA_VERSION,
        "source_schema_version": specification.source_schema_version,
        "base_config_source": specification.base_config_source,
        "base_configuration": specification.base_config.model_dump(mode="json"),
        "runs": [
            {
                "ordinal": run.ordinal,
                "run_id": run.run_id,
                "overrides": run.overrides,
                "configuration_sha256": run.configuration_sha256,
                "configuration": run.config.model_dump(mode="json"),
            }
            for run in specification.runs
        ],
    }


def _run_records(model: SugarscapeModel) -> RunRecords:
    return RunRecords(
        model=model.model_records,
        cohort=model.cohort_records,
        agent_transitions=model.agent_transitions,
        agent_events=model.event_records,
        shock_events=model.shock_event_snapshots,
        shock_exposures=model.shock_exposures,
        cell_damage=model.cell_damage_applications,
    )


def _completed_index_record(run: ResolvedBatchRun, summary: dict[str, Any]) -> dict[str, object]:
    return {
        "ordinal": run.ordinal,
        "run_id": run.run_id,
        "status": "completed",
        "seed": run.config.seed,
        "configuration_sha256": run.configuration_sha256,
        "bundle_path": f"runs/{run.run_id}",
        "summary": summary,
        "error": None,
    }


def _failed_index_record(run: ResolvedBatchRun, *, kind: str, message: str) -> dict[str, object]:
    return {
        "ordinal": run.ordinal,
        "run_id": run.run_id,
        "status": "failed",
        "seed": run.config.seed,
        "configuration_sha256": run.configuration_sha256,
        "bundle_path": None,
        "summary": None,
        "error": {"kind": kind, "message": message},
    }


def _execute_one(run: ResolvedBatchRun, destination: Path) -> dict[str, object]:
    try:
        with RunBundleSession(destination, run.config) as session:
            model = SugarscapeModel(run.config, spatial_sink=session)
            model.run()
            summary = model.summary()
            session.publish(
                summary=summary,
                records=_run_records(model),
                rng_provenance=model.rng_provenance,
            )
        return _completed_index_record(run, summary)
    except InvariantViolationError as error:
        return _failed_index_record(run, kind="invariant_failure", message=str(error))
    except (BundlePublicationError, OSError) as error:
        return _failed_index_record(run, kind="output_failure", message=str(error))
    except Exception as error:  # pragma: no cover - defensive scientific process boundary
        return _failed_index_record(run, kind="runtime_failure", message=str(error))


def _flatten_index_record(record: Mapping[str, object]) -> dict[str, object]:
    summary = record["summary"]
    error = record["error"]
    summary_mapping = summary if isinstance(summary, Mapping) else {}
    inequality = summary_mapping.get("inequality")
    inequality_mapping = inequality if isinstance(inequality, Mapping) else {}
    error_mapping = error if isinstance(error, Mapping) else {}
    return {
        "ordinal": record["ordinal"],
        "run_id": record["run_id"],
        "status": record["status"],
        "seed": record["seed"],
        "configuration_sha256": record["configuration_sha256"],
        "bundle_path": record["bundle_path"],
        "error_kind": error_mapping.get("kind"),
        "error_message": error_mapping.get("message"),
        "summary_schema_version": summary_mapping.get("schema_version"),
        "completed_ticks": summary_mapping.get("completed_ticks"),
        "alive_count": summary_mapping.get("alive_count"),
        "dead_count": summary_mapping.get("dead_count"),
        "total_resources": summary_mapping.get("total_resources"),
        "cohort_mean_energy": summary_mapping.get("cohort_mean_energy"),
        "total_harvest": summary_mapping.get("total_harvest"),
        "unmet_need": summary_mapping.get("unmet_need"),
        "energy_gini": inequality_mapping.get("energy_gini"),
        "harvest_gini": inequality_mapping.get("harvest_gini"),
        "unmet_need_gini": inequality_mapping.get("unmet_need_gini"),
    }


def _write_batch_artifacts(
    staging: Path,
    specification: ResolvedBatchSpecification,
    records: list[dict[str, object]],
) -> BatchExecutionResult:
    completed = sum(record["status"] == "completed" for record in records)
    failed = len(records) - completed
    status: Literal["completed", "completed_with_failures"] = (
        "completed" if failed == 0 else "completed_with_failures"
    )
    result = BatchExecutionResult(status, len(records), completed, failed)
    write_json(staging / "batch_specification.json", _normalized_batch(specification))
    write_json(
        staging / "runs.json",
        {"schema_version": BATCH_INDEX_SCHEMA_VERSION, "runs": records},
    )
    table = pa.Table.from_pylist(
        [_flatten_index_record(record) for record in records], _INDEX_SCHEMA
    )
    pq.write_table(
        table,
        staging / "runs.parquet",
        version="2.6",
        compression="zstd",
        write_page_checksum=True,
    )

    files = {
        "batch_specification.json": file_descriptor(
            staging / "batch_specification.json", schema_version=NORMALIZED_BATCH_SCHEMA_VERSION
        ),
        "runs.json": file_descriptor(
            staging / "runs.json", schema_version=BATCH_INDEX_SCHEMA_VERSION
        ),
        "runs.parquet": file_descriptor(
            staging / "runs.parquet", schema_version=BATCH_INDEX_SCHEMA_VERSION
        ),
    }
    run_descriptors: list[dict[str, object]] = []
    for record in records:
        bundle_path = record["bundle_path"]
        descriptor = {
            "ordinal": record["ordinal"],
            "run_id": record["run_id"],
            "status": record["status"],
            "bundle_path": bundle_path,
            "run_bundle_schema_version": None,
            "manifest_sha256": None,
        }
        if isinstance(bundle_path, str):
            child_manifest = staging / bundle_path / "manifest.json"
            descriptor["run_bundle_schema_version"] = BUNDLE_SCHEMA_VERSION
            descriptor["manifest_sha256"] = sha256_file(child_manifest)
        run_descriptors.append(descriptor)
    manifest = {
        "schema_version": BATCH_BUNDLE_SCHEMA_VERSION,
        "status": result.status,
        "total_runs": result.total_runs,
        "completed_runs": result.completed_runs,
        "failed_runs": result.failed_runs,
        "files": files,
        "runs": run_descriptors,
    }
    write_json(staging / "batch_manifest.json", manifest)
    validate_batch_bundle(staging)
    actual = pq.read_table(staging / "runs.parquet")
    if not actual.equals(table, check_metadata=True):
        raise BundleValidationError("batch Parquet round trip changed index values")
    return result


def execute_batch(
    specification: ResolvedBatchSpecification, destination: Path
) -> BatchExecutionResult:
    """Run every declared configuration sequentially and publish the complete attempt atomically."""

    outcome: list[BatchExecutionResult] = []

    def build(staging: Path) -> None:
        runs_directory = staging / "runs"
        runs_directory.mkdir()
        records = [_execute_one(run, runs_directory / run.run_id) for run in specification.runs]
        outcome.append(_write_batch_artifacts(staging, specification, records))

    publish_directory_atomically(destination, build)
    if len(outcome) != 1:  # pragma: no cover - internal publication invariant
        raise BundlePublicationError("batch publication did not produce one result")
    return outcome[0]


def _require_mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BundleValidationError(f"{name} must be an object")
    return value


def _validate_normalized_header(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if set(payload) != _NORMALIZED_BATCH_FIELDS:
        raise BundleValidationError("normalized batch fields differ from its schema")
    if payload.get("schema_version") != NORMALIZED_BATCH_SCHEMA_VERSION:
        raise BundleValidationError("normalized batch schema is unsupported")
    if payload.get("source_schema_version") != "0.1.0":
        raise BundleValidationError("source batch schema is unsupported")
    if not isinstance(payload.get("base_config_source"), str):
        raise BundleValidationError("base configuration source is malformed")
    base_mapping = _require_mapping(payload.get("base_configuration"), name="base configuration")
    try:
        base_config = SimulationConfig.model_validate(base_mapping)
    except ValueError as error:
        raise BundleValidationError("base configuration is invalid") from error
    if base_config.model_dump(mode="json") != base_mapping:
        raise BundleValidationError("base configuration is not normalized")
    return base_mapping


def _parse_normalized_run(
    item: object, *, ordinal: int, seen: set[str]
) -> tuple[Mapping[str, Any], BatchRunSpecification]:
    run = _require_mapping(item, name="normalized run")
    if set(run) != _NORMALIZED_RUN_FIELDS:
        raise BundleValidationError("normalized run fields differ from their schema")
    try:
        parsed = BatchRunSpecification.model_validate(
            {"id": run.get("run_id"), "overrides": run.get("overrides")}
        )
    except ValueError as error:
        raise BundleValidationError("normalized run identity or overrides are invalid") from error
    if parsed.id in seen:
        raise BundleValidationError("normalized run IDs are not unique")
    seen.add(parsed.id)
    if run.get("ordinal") != ordinal:
        raise BundleValidationError("normalized run order is not canonical")
    return run, parsed


def _validate_resolved_configuration(
    run: Mapping[str, Any],
    *,
    base_mapping: Mapping[str, Any],
    overrides: Mapping[str, Any],
) -> None:
    configuration = _require_mapping(run.get("configuration"), name="run configuration")
    try:
        config = SimulationConfig.model_validate(configuration)
    except ValueError as error:
        raise BundleValidationError("resolved run configuration is invalid") from error
    if config.model_dump(mode="json") != configuration:
        raise BundleValidationError("resolved run configuration is not normalized")
    if deep_merge_configuration(base_mapping, overrides) != configuration:
        raise BundleValidationError("resolved run configuration differs from its overrides")
    if run.get("configuration_sha256") != _configuration_digest(configuration):
        raise BundleValidationError("resolved run configuration digest differs")


def _validate_normalized_batch(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    base_mapping = _validate_normalized_header(payload)

    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise BundleValidationError("normalized batch requires at least one run")
    seen: set[str] = set()
    validated_runs: list[Mapping[str, Any]] = []
    for ordinal, item in enumerate(runs):
        run, parsed = _parse_normalized_run(item, ordinal=ordinal, seen=seen)
        _validate_resolved_configuration(
            run,
            base_mapping=base_mapping,
            overrides=parsed.overrides,
        )
        validated_runs.append(run)
    return validated_runs


def _validate_index_record(record: Mapping[str, Any], normalized: Mapping[str, Any]) -> None:
    if set(record) != _INDEX_RECORD_FIELDS:
        raise BundleValidationError("batch index record fields differ from their schema")
    configuration = _require_mapping(normalized.get("configuration"), name="run configuration")
    if (
        record.get("ordinal") != normalized.get("ordinal")
        or record.get("run_id") != normalized.get("run_id")
        or record.get("seed") != configuration.get("seed")
        or record.get("configuration_sha256") != normalized.get("configuration_sha256")
    ):
        raise BundleValidationError("batch index differs from normalized run provenance")
    status = record.get("status")
    run_id = record.get("run_id")
    if status == "completed":
        if record.get("bundle_path") != f"runs/{run_id}" or record.get("error") is not None:
            raise BundleValidationError("completed batch index record is malformed")
        _validate_summary(record.get("summary"), expected_seed=record.get("seed"))
    elif status == "failed":
        error = _require_mapping(record.get("error"), name="run error")
        if (
            record.get("bundle_path") is not None
            or record.get("summary") is not None
            or set(error) != {"kind", "message"}
            or error.get("kind")
            not in {
                "invariant_failure",
                "output_failure",
                "runtime_failure",
            }
            or not isinstance(error.get("message"), str)
        ):
            raise BundleValidationError("failed batch index record is malformed")
    else:
        raise BundleValidationError("batch run status is unsupported")


def _validate_summary(summary: object, *, expected_seed: object) -> None:
    value = _require_mapping(summary, name="run summary")
    validate_summary_payload(value)
    if value.get("seed") != expected_seed:
        raise BundleValidationError("indexed run summary seed differs")


def _validate_batch_root(bundle: Path) -> Path:
    if not bundle.is_dir():
        raise BundleValidationError(f"batch bundle is not a directory: {bundle}")
    for path in bundle.rglob("*"):
        if path.is_symlink():
            raise BundleValidationError(f"batch bundle cannot contain symbolic links: {path.name}")
    if {path.name for path in bundle.iterdir()} != _BATCH_ROOT_ENTRIES:
        raise BundleValidationError("batch bundle root entries differ from its schema")
    runs_directory = bundle / "runs"
    if not runs_directory.is_dir():
        raise BundleValidationError("batch runs entry must be a directory")
    return runs_directory


def _read_batch_manifest(bundle: Path) -> dict[str, Any]:
    manifest = read_json_object(bundle / "batch_manifest.json", max_bytes=_MAX_JSON_BYTES)
    if (
        set(manifest) != _BATCH_MANIFEST_FIELDS
        or manifest.get("schema_version") != BATCH_BUNDLE_SCHEMA_VERSION
    ):
        raise BundleValidationError("batch manifest differs from its schema")
    return manifest


def _validate_manifest_files(bundle: Path, manifest: Mapping[str, Any]) -> None:
    files = _require_mapping(manifest.get("files"), name="batch manifest files")
    if set(files) != set(_ARTIFACT_SCHEMAS):
        raise BundleValidationError("batch manifest file set is incomplete or unknown")
    for relative_path, schema_version in _ARTIFACT_SCHEMAS.items():
        descriptor = _require_mapping(files[relative_path], name="batch file descriptor")
        if set(descriptor) != {"schema_version", "byte_count", "sha256"}:
            raise BundleValidationError(f"artifact descriptor is malformed: {relative_path}")
        path = bundle / relative_path
        if descriptor.get("schema_version") != schema_version:
            raise BundleValidationError(f"artifact schema version is invalid: {relative_path}")
        if path.stat().st_size != descriptor.get("byte_count"):
            raise BundleValidationError(f"byte-count mismatch for {relative_path}")
        if sha256_file(path) != descriptor.get("sha256"):
            raise BundleValidationError(f"digest mismatch for {relative_path}")


def _read_index_records(
    bundle: Path, normalized_runs: list[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    index_payload = read_json_object(bundle / "runs.json", max_bytes=_MAX_JSON_BYTES)
    if (
        set(index_payload) != {"schema_version", "runs"}
        or index_payload.get("schema_version") != BATCH_INDEX_SCHEMA_VERSION
    ):
        raise BundleValidationError("batch JSON index differs from its schema")
    index_runs = index_payload.get("runs")
    if not isinstance(index_runs, list) or len(index_runs) != len(normalized_runs):
        raise BundleValidationError("batch index run count differs from normalized provenance")
    typed_index: list[Mapping[str, Any]] = []
    for record, normalized in zip(index_runs, normalized_runs, strict=True):
        mapping = _require_mapping(record, name="batch index record")
        _validate_index_record(mapping, normalized)
        typed_index.append(mapping)
    return typed_index


def _validate_parquet_index(bundle: Path, typed_index: list[Mapping[str, Any]]) -> None:
    try:
        table = pq.read_table(bundle / "runs.parquet")
    except Exception as error:
        raise BundleValidationError("cannot read batch Parquet index") from error
    if not table.schema.equals(_INDEX_SCHEMA, check_metadata=True):
        raise BundleValidationError("batch Parquet schema differs from its contract")
    expected_table = pa.Table.from_pylist(
        [_flatten_index_record(record) for record in typed_index], _INDEX_SCHEMA
    )
    if not table.equals(expected_table, check_metadata=True):
        raise BundleValidationError("JSON and Parquet batch indexes differ")


def _validate_manifest_counts(
    manifest: Mapping[str, Any], typed_index: list[Mapping[str, Any]]
) -> None:
    completed = sum(record["status"] == "completed" for record in typed_index)
    failed = len(typed_index) - completed
    expected_status = "completed" if failed == 0 else "completed_with_failures"
    if (
        manifest.get("status") != expected_status
        or manifest.get("total_runs") != len(typed_index)
        or manifest.get("completed_runs") != completed
        or manifest.get("failed_runs") != failed
    ):
        raise BundleValidationError("batch manifest counts or status differ from indexes")


def _validate_completed_child(
    bundle: Path,
    descriptor: Mapping[str, Any],
    record: Mapping[str, Any],
    normalized: Mapping[str, Any],
) -> str:
    run_id = record["run_id"]
    if not isinstance(run_id, str):
        raise BundleValidationError("completed run ID is malformed")
    child = bundle / "runs" / run_id
    child_manifest = validate_run_bundle(child)
    child_configuration = read_json_object(
        child / "configuration.json", max_bytes=_MAX_JSON_BYTES
    ).get("configuration")
    if (
        descriptor.get("run_bundle_schema_version") != BUNDLE_SCHEMA_VERSION
        or descriptor.get("manifest_sha256") != sha256_file(child / "manifest.json")
        or child_manifest.get("seed") != record.get("seed")
        or child_configuration != normalized.get("configuration")
        or read_json_object(child / "summary.json", max_bytes=_MAX_JSON_BYTES)
        != record.get("summary")
    ):
        raise BundleValidationError("child run bundle differs from its batch index")
    return run_id


def _validate_run_descriptor(
    bundle: Path,
    descriptor_value: object,
    record: Mapping[str, Any],
    normalized: Mapping[str, Any],
) -> str | None:
    descriptor = _require_mapping(descriptor_value, name="run bundle descriptor")
    identity_fields = ("ordinal", "run_id", "status", "bundle_path")
    if set(descriptor) != _RUN_DESCRIPTOR_FIELDS or any(
        descriptor.get(name) != record.get(name) for name in identity_fields
    ):
        raise BundleValidationError("run bundle descriptor differs from the batch index")
    if record["status"] == "completed":
        return _validate_completed_child(bundle, descriptor, record, normalized)
    if (
        descriptor.get("run_bundle_schema_version") is not None
        or descriptor.get("manifest_sha256") is not None
    ):
        raise BundleValidationError("failed run cannot declare a child bundle")
    return None


def _validate_child_bundles(
    bundle: Path,
    runs_directory: Path,
    manifest: Mapping[str, Any],
    typed_index: list[Mapping[str, Any]],
    normalized_runs: list[Mapping[str, Any]],
) -> None:
    descriptors = manifest.get("runs")
    if not isinstance(descriptors, list) or len(descriptors) != len(typed_index):
        raise BundleValidationError("batch manifest run descriptors are malformed")
    completed_ids: set[str] = set()
    for descriptor_value, record, normalized in zip(
        descriptors, typed_index, normalized_runs, strict=True
    ):
        run_id = _validate_run_descriptor(bundle, descriptor_value, record, normalized)
        if run_id is not None:
            completed_ids.add(run_id)
    actual_ids = {path.name for path in runs_directory.iterdir()}
    if actual_ids != completed_ids or any(
        not (bundle / "runs" / run_id).is_dir() for run_id in actual_ids
    ):
        raise BundleValidationError("batch child directory set differs from completed runs")


def validate_batch_bundle(bundle: Path) -> dict[str, Any]:
    """Validate aggregate schemas, digests, indexes, provenance, and child run bundles."""

    bundle = Path(bundle)
    runs_directory = _validate_batch_root(bundle)
    manifest = _read_batch_manifest(bundle)
    _validate_manifest_files(bundle, manifest)
    normalized_runs = _validate_normalized_batch(
        read_json_object(bundle / "batch_specification.json", max_bytes=_MAX_JSON_BYTES)
    )
    typed_index = _read_index_records(bundle, normalized_runs)
    _validate_parquet_index(bundle, typed_index)
    _validate_manifest_counts(manifest, typed_index)
    _validate_child_bundles(
        bundle,
        runs_directory,
        manifest,
        typed_index,
        normalized_runs,
    )
    return manifest
