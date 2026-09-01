"""Fail-closed publication and persistent run-bundle serialization."""

from __future__ import annotations

import ctypes
import errno
import importlib.metadata
import math
import os
import platform
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping
from contextlib import suppress
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from numpy.typing import NDArray

from social_cybernetics.artifact_io import (
    file_descriptor,
    read_json_object,
    sha256_file,
    write_json,
)
from social_cybernetics.config import SimulationConfig
from social_cybernetics.domain import initialize_resources
from social_cybernetics.persistence_errors import (
    AtomicPublicationUnavailableError,
    BundleExistsError,
    BundleValidationError,
)
from social_cybernetics.persistence_errors import BundlePublicationError as BundlePublicationError
from social_cybernetics.run_tables import (
    _TABLE_SCHEMAS,
    TABLE_SCHEMA_VERSIONS,
    RunRecords,
    build_record_tables,
)
from social_cybernetics.spatial_output import (
    SPATIAL_SCHEMA_VERSION,
    SpatialHistoryWriter,
    validate_spatial_history,
)

_AT_FDCWD = -100
_RENAME_NOREPLACE = 1
_MAX_JSON_BYTES = 16 * 1024 * 1024

BUNDLE_SCHEMA_VERSION = "scs-run-bundle/v1.1.0"
CONFIGURATION_SCHEMA_VERSION = "scs-normalized-configuration/v0.1.0"
PROVENANCE_SCHEMA_VERSION = "scs-provenance/v0.1.0"
SUMMARY_SCHEMA_VERSION = "scs-run-summary/v0.1.0"

_SUMMARY_FIELDS = {
    "schema_version",
    "seed",
    "completed_ticks",
    "alive_count",
    "dead_count",
    "total_resources",
    "cohort_mean_energy",
    "total_harvest",
    "unmet_need",
    "inequality",
}
_SUMMARY_COUNTS = ("seed", "completed_ticks", "alive_count", "dead_count")
_SUMMARY_MEASURES = (
    "total_resources",
    "cohort_mean_energy",
    "total_harvest",
    "unmet_need",
)
_INEQUALITY_FIELDS = {"energy_gini", "harvest_gini", "unmet_need_gini"}
_RNG_STREAM_REGISTRY = {
    "policy": (1,),
    "shock_initiation": (2, 1),
    "shock_location": (2, 2),
    "shock_transmission": (2, 3),
}
_PROVENANCE_PACKAGES = {
    "social-cybernetics-sugarscape": True,
    "mesa": True,
    "numpy": True,
    "pydantic": True,
    "pyarrow": True,
    "xarray": False,
    "netCDF4": True,
}

type DirectoryBuilder = Callable[[Path], None]


def _validate_agent_transition_records(records: RunRecords, completed_ticks: int) -> None:
    """Cross-check transitions before serialization while records remain typed."""

    if not records.model:
        if completed_ticks == 0 and not records.cohort and not records.agent_transitions:
            return
        raise BundleValidationError("model records do not cover every completed tick")
    if [record.tick for record in records.model] != list(range(completed_ticks + 1)):
        raise BundleValidationError("model records do not cover every completed tick")
    expected_count = sum(record.alive_count for record in records.model[:-1])
    if len(records.agent_transitions) != expected_count:
        raise BundleValidationError("agent-transition count differs from active-agent history")

    transition_keys = [(record.tick, record.agent_id) for record in records.agent_transitions]
    if transition_keys != sorted(set(transition_keys)):
        raise BundleValidationError("agent transitions are duplicated or out of canonical order")
    cohort_by_key = {
        (record.tick, record.snapshot.agent_id): record.snapshot for record in records.cohort
    }
    for transition in records.agent_transitions:
        before = cohort_by_key.get((transition.tick - 1, transition.agent_id))
        after = cohort_by_key.get((transition.tick, transition.agent_id))
        if before is None or after is None or not before.alive:
            raise BundleValidationError("agent transition lacks an active cohort origin")
        if before.position != transition.origin or before.energy != transition.energy_before:
            raise BundleValidationError("agent-transition origin differs from cohort history")
        if (
            after.position != transition.final_position
            or after.energy != transition.energy_after
            or after.alive == transition.died
        ):
            raise BundleValidationError("agent-transition result differs from cohort history")


def _path_exists(path: Path) -> bool:
    """Include broken symlinks when enforcing the no-overwrite contract."""

    return os.path.lexists(path)


def require_available_output(destination: Path) -> None:
    """Fail fast unless a bundle can be staged beside an absent destination."""

    destination = Path(destination)
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"output parent directory does not exist: {destination.parent}")
    if _path_exists(destination):
        raise BundleExistsError(f"output destination already exists: {destination}")


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically rename one directory without replacing any destination entry."""

    source_text = os.fspath(source)
    destination_text = os.fspath(destination)
    if "\0" in source_text or "\0" in destination_text:
        raise ValueError("publication paths cannot contain null bytes")

    library = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = library.renameat2
    except AttributeError as error:
        raise AtomicPublicationUnavailableError(
            "this platform does not provide atomic no-overwrite directory publication"
        ) from error

    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(
        _AT_FDCWD,
        os.fsencode(source_text),
        _AT_FDCWD,
        os.fsencode(destination_text),
        _RENAME_NOREPLACE,
    )
    if result == 0:
        return

    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        raise BundleExistsError(f"output destination already exists: {destination}")
    raise OSError(error_number, os.strerror(error_number), destination_text)


def publish_directory_atomically(destination: Path, build: DirectoryBuilder) -> Path:
    """Build in a sibling staging directory and atomically publish without overwrite."""

    destination = Path(destination)
    require_available_output(destination)
    parent = destination.parent

    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=parent))
    try:
        build(staging)
        _rename_noreplace(staging, destination)
    except Exception:
        if _path_exists(staging):
            shutil.rmtree(staging)
        raise
    return destination


def _software_provenance() -> dict[str, object]:
    packages: dict[str, str | None] = {}
    for name, required in _PROVENANCE_PACKAGES.items():
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            if required:
                raise BundleValidationError(
                    f"required package metadata is unavailable: {name}"
                ) from None
            packages[name] = None
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "byte_order": sys.byteorder,
        "packages": packages,
    }


def _provenance_payload(
    *,
    seed: int,
    rng_provenance: Mapping[str, str | tuple[int, ...]],
) -> dict[str, object]:
    bit_generator = rng_provenance.get("bit_generator")
    if not isinstance(bit_generator, str):
        raise BundleValidationError("RNG provenance requires a bit_generator name")
    if set(rng_provenance) != {"bit_generator", *_RNG_STREAM_REGISTRY}:
        raise BundleValidationError("RNG stream registry is incomplete or unknown")
    streams: dict[str, list[int]] = {}
    for name, expected in _RNG_STREAM_REGISTRY.items():
        value = rng_provenance[name]
        if value != expected:
            raise BundleValidationError(f"RNG stream registry differs at {name!r}")
        streams[name] = list(expected)
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "seed": seed,
        "rng": {
            "derivation": "numpy.random.SeedSequence(run_seed, spawn_key=stream_key)",
            "bit_generator": bit_generator,
            "streams": dict(sorted(streams.items())),
        },
        "software": _software_provenance(),
    }


def validate_summary_payload(summary: Mapping[str, object]) -> None:
    if set(summary) != _SUMMARY_FIELDS:
        raise BundleValidationError("run summary fields differ from its schema")
    if summary.get("schema_version") != SUMMARY_SCHEMA_VERSION:
        raise BundleValidationError("summary schema is unsupported")
    for name in _SUMMARY_COUNTS:
        value = summary.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise BundleValidationError(f"summary field must be a nonnegative integer: {name}")
    for name in _SUMMARY_MEASURES:
        value = summary.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise BundleValidationError(f"summary field must be finite and nonnegative: {name}")
    inequality = summary.get("inequality")
    if not isinstance(inequality, Mapping) or set(inequality) != _INEQUALITY_FIELDS:
        raise BundleValidationError("summary inequality fields differ from its schema")
    for name, value in inequality.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0 <= value <= 1
        ):
            raise BundleValidationError(f"summary inequality must be within [0, 1]: {name}")


def _validate_file_set(bundle: Path, declared_files: set[str]) -> None:
    for path in bundle.rglob("*"):
        if path.is_symlink():
            raise BundleValidationError(f"bundle cannot contain symbolic links: {path.name}")
    actual_files = {
        path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if path.is_file()
    }
    if actual_files != declared_files | {"manifest.json"}:
        raise BundleValidationError("bundle file set does not match its manifest")


def _manifest_sections(
    bundle: Path, manifest: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    files = manifest.get("files")
    tables = manifest.get("tables")
    spatial = manifest.get("spatial")
    if not isinstance(files, dict) or not isinstance(tables, dict) or not isinstance(spatial, dict):
        raise BundleValidationError("manifest files, tables, and spatial metadata must be objects")
    if set(tables) != set(TABLE_SCHEMA_VERSIONS):
        raise BundleValidationError("manifest table set is incomplete or unknown")
    expected_file_names = {
        "configuration.json",
        "provenance.json",
        "summary.json",
        "spatial.nc",
        *(f"tables/{name}.parquet" for name in TABLE_SCHEMA_VERSIONS),
    }
    if set(files) != expected_file_names:
        raise BundleValidationError("manifest file set is incomplete or unknown")
    _validate_file_set(bundle, expected_file_names)
    return files, tables, spatial


def _validate_artifact_descriptors(bundle: Path, files: Mapping[str, Any]) -> None:
    expected_schemas = {
        "configuration.json": CONFIGURATION_SCHEMA_VERSION,
        "provenance.json": PROVENANCE_SCHEMA_VERSION,
        "summary.json": SUMMARY_SCHEMA_VERSION,
        "spatial.nc": SPATIAL_SCHEMA_VERSION,
        **{
            f"tables/{name}.parquet": schema_version
            for name, schema_version in TABLE_SCHEMA_VERSIONS.items()
        },
    }
    for relative_path, descriptor in files.items():
        if not isinstance(relative_path, str) or not isinstance(descriptor, dict):
            raise BundleValidationError("manifest file descriptors are malformed")
        if descriptor.get("schema_version") != expected_schemas[relative_path]:
            raise BundleValidationError(f"artifact schema version is invalid: {relative_path}")
        path = bundle / relative_path
        if path.stat().st_size != descriptor.get("byte_count"):
            raise BundleValidationError(f"byte-count mismatch for {relative_path}")
        if sha256_file(path) != descriptor.get("sha256"):
            raise BundleValidationError(f"digest mismatch for {relative_path}")


def _validated_core_artifacts(
    bundle: Path, manifest: Mapping[str, Any]
) -> tuple[SimulationConfig, dict[str, Any], int]:
    configuration = read_json_object(bundle / "configuration.json", max_bytes=_MAX_JSON_BYTES)
    provenance = read_json_object(bundle / "provenance.json", max_bytes=_MAX_JSON_BYTES)
    summary = read_json_object(bundle / "summary.json", max_bytes=_MAX_JSON_BYTES)
    if configuration.get("schema_version") != CONFIGURATION_SCHEMA_VERSION:
        raise BundleValidationError("normalized configuration schema is unsupported")
    if provenance.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
        raise BundleValidationError("provenance schema is unsupported")
    validate_summary_payload(summary)
    seed = manifest.get("seed")
    configured = configuration.get("configuration")
    if not isinstance(configured, dict):
        raise BundleValidationError("normalized configuration payload is malformed")
    try:
        validated_config = SimulationConfig.model_validate(configured)
    except ValueError as error:
        raise BundleValidationError("normalized configuration is invalid") from error
    if validated_config.model_dump(mode="json") != configured:
        raise BundleValidationError("configuration payload is not normalized")
    if configured.get("schema_version") != manifest.get("model_schema_version"):
        raise BundleValidationError("model schema differs across bundle artifacts")
    if summary.get("completed_ticks") != manifest.get("completed_ticks"):
        raise BundleValidationError("completed tick count differs across bundle artifacts")
    if (
        configured.get("seed") != seed
        or provenance.get("seed") != seed
        or summary.get("seed") != seed
    ):
        raise BundleValidationError("seed differs across bundle artifacts")
    completed_ticks = summary["completed_ticks"]
    if not isinstance(completed_ticks, int):  # guarded by validate_summary_payload
        raise BundleValidationError("completed tick count is malformed")
    return validated_config, provenance, completed_ticks


def _validate_spatial_contract(
    bundle: Path,
    spatial: Mapping[str, Any],
    *,
    config: SimulationConfig,
    completed_ticks: int,
) -> None:
    if spatial != {
        "path": "spatial.nc",
        "schema_version": SPATIAL_SCHEMA_VERSION,
        "snapshot_count": completed_ticks + 1,
        "dimensions": ["tick", "x", "y"],
        "dynamic_variables": [
            "resource_stock",
            "effective_capacity",
            "effective_regeneration",
            "recovery_remaining",
        ],
        "static_variables": ["baseline_capacity", "baseline_regeneration"],
    }:
        raise BundleValidationError("spatial manifest metadata differs from contract")
    validate_spatial_history(
        bundle / "spatial.nc",
        config=config,
        completed_ticks=completed_ticks,
    )


def _validate_provenance_contract(provenance: Mapping[str, Any]) -> None:
    software = provenance.get("software")
    packages = software.get("packages") if isinstance(software, dict) else None
    if not isinstance(packages, dict) or set(packages) != set(_PROVENANCE_PACKAGES):
        raise BundleValidationError("software package provenance is malformed")
    for name, required in _PROVENANCE_PACKAGES.items():
        version = packages[name]
        if not isinstance(version, str) and not (version is None and not required):
            raise BundleValidationError(f"software package provenance is malformed: {name}")
    rng = provenance.get("rng")
    if not isinstance(rng, dict) or rng.get("derivation") != (
        "numpy.random.SeedSequence(run_seed, spawn_key=stream_key)"
    ):
        raise BundleValidationError("RNG derivation provenance is malformed")
    if not isinstance(rng.get("bit_generator"), str) or rng.get("streams") != {
        name: list(key) for name, key in sorted(_RNG_STREAM_REGISTRY.items())
    }:
        raise BundleValidationError("RNG stream registry provenance is malformed")


def _validate_table_contracts(bundle: Path, tables: Mapping[str, Any]) -> None:
    for name, schema_version in TABLE_SCHEMA_VERSIONS.items():
        descriptor = tables[name]
        if not isinstance(descriptor, dict):
            raise BundleValidationError(f"table descriptor is malformed: {name}")
        relative_path = f"tables/{name}.parquet"
        if descriptor.get("path") != relative_path:
            raise BundleValidationError(f"table path is invalid: {name}")
        if descriptor.get("schema_version") != schema_version:
            raise BundleValidationError(f"table schema version is invalid: {name}")
        try:
            parquet = pq.ParquetFile(bundle / relative_path)
        except Exception as error:
            raise BundleValidationError(f"cannot read Parquet table: {name}") from error
        if not parquet.schema_arrow.equals(_TABLE_SCHEMAS[name], check_metadata=True):
            raise BundleValidationError(f"Parquet schema differs from contract: {name}")
        if parquet.metadata.num_rows != descriptor.get("row_count"):
            raise BundleValidationError(f"Parquet row count differs from manifest: {name}")


def validate_run_bundle(bundle: Path) -> dict[str, Any]:
    """Validate schemas, digests, row counts, and cross-artifact provenance."""

    bundle = Path(bundle)
    if not bundle.is_dir():
        raise BundleValidationError(f"run bundle is not a directory: {bundle}")
    manifest = read_json_object(bundle / "manifest.json", max_bytes=_MAX_JSON_BYTES)
    if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise BundleValidationError("unsupported run-bundle schema version")
    files, tables, spatial = _manifest_sections(bundle, manifest)
    _validate_artifact_descriptors(bundle, files)
    config, provenance, completed_ticks = _validated_core_artifacts(bundle, manifest)
    _validate_spatial_contract(
        bundle,
        spatial,
        config=config,
        completed_ticks=completed_ticks,
    )
    _validate_provenance_contract(provenance)
    _validate_table_contracts(bundle, tables)
    return manifest


def _write_staged_bundle(
    staging: Path,
    *,
    config: SimulationConfig,
    summary: Mapping[str, object],
    records: RunRecords,
    rng_provenance: Mapping[str, str | tuple[int, ...]],
) -> None:
    """Finalize non-spatial artifacts beside an already closed spatial stream."""

    configuration = {
        "schema_version": CONFIGURATION_SCHEMA_VERSION,
        "configuration": config.model_dump(mode="json"),
    }
    summary_payload = dict(summary)
    validate_summary_payload(summary_payload)
    if summary_payload["seed"] != config.seed:
        raise BundleValidationError("summary seed differs from normalized configuration")
    completed_value = summary_payload["completed_ticks"]
    if not isinstance(completed_value, int):
        raise BundleValidationError("completed tick count is invalid")
    completed_ticks = completed_value
    _validate_agent_transition_records(records, completed_ticks)
    record_tables = build_record_tables(records)
    provenance = _provenance_payload(seed=config.seed, rng_provenance=rng_provenance)
    tables_directory = staging / "tables"
    tables_directory.mkdir()
    write_json(staging / "configuration.json", configuration)
    write_json(staging / "provenance.json", provenance)
    write_json(staging / "summary.json", summary_payload)
    for name, table in record_tables.items():
        pq.write_table(
            table,
            tables_directory / f"{name}.parquet",
            version="2.6",
            compression="zstd",
            write_page_checksum=True,
        )

    files: dict[str, dict[str, object]] = {}
    artifact_schemas = {
        "configuration.json": CONFIGURATION_SCHEMA_VERSION,
        "provenance.json": PROVENANCE_SCHEMA_VERSION,
        "summary.json": SUMMARY_SCHEMA_VERSION,
        "spatial.nc": SPATIAL_SCHEMA_VERSION,
    }
    for relative_path, schema_version in artifact_schemas.items():
        files[relative_path] = file_descriptor(
            staging / relative_path,
            schema_version=schema_version,
        )
    for name, schema_version in TABLE_SCHEMA_VERSIONS.items():
        relative_path = f"tables/{name}.parquet"
        files[relative_path] = file_descriptor(
            staging / relative_path,
            schema_version=schema_version,
        )
    manifest = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "model_schema_version": config.schema_version,
        "seed": config.seed,
        "completed_ticks": completed_ticks,
        "files": dict(sorted(files.items())),
        "tables": {
            name: {
                "path": f"tables/{name}.parquet",
                "schema_version": TABLE_SCHEMA_VERSIONS[name],
                "row_count": record_tables[name].num_rows,
            }
            for name in TABLE_SCHEMA_VERSIONS
        },
        "spatial": {
            "path": "spatial.nc",
            "schema_version": SPATIAL_SCHEMA_VERSION,
            "snapshot_count": completed_ticks + 1,
            "dimensions": ["tick", "x", "y"],
            "dynamic_variables": [
                "resource_stock",
                "effective_capacity",
                "effective_regeneration",
                "recovery_remaining",
            ],
            "static_variables": ["baseline_capacity", "baseline_regeneration"],
        },
    }
    write_json(staging / "manifest.json", manifest)
    validate_run_bundle(staging)
    for name, expected in record_tables.items():
        actual = pq.read_table(staging / f"tables/{name}.parquet")
        if not actual.equals(expected, check_metadata=True):
            raise BundleValidationError(f"Parquet round trip changed table values: {name}")


class RunBundleSession:
    """Own one staged spatial stream until validated atomic publication or cleanup."""

    def __init__(self, destination: Path, config: SimulationConfig) -> None:
        self.destination = Path(destination)
        self.config = config
        require_available_output(self.destination)
        self._staging = Path(
            tempfile.mkdtemp(
                prefix=f".{self.destination.name}.staging-",
                dir=self.destination.parent,
            )
        )
        self._published = False
        try:
            self._spatial = SpatialHistoryWriter(self._staging / "spatial.nc", config)
        except Exception as error:
            shutil.rmtree(self._staging)
            if isinstance(error, BundlePublicationError):
                raise
            raise BundlePublicationError("cannot initialize spatial output stream") from error

    def record_spatial_snapshot(
        self,
        *,
        tick: int,
        resource_stock: NDArray[Any],
        effective_capacity: NDArray[Any],
        effective_regeneration: NDArray[Any],
        recovery_remaining: NDArray[Any],
        baseline_capacity: NDArray[Any],
        baseline_regeneration: NDArray[Any],
    ) -> None:
        """Append one validated spatial snapshot to the staged NetCDF stream."""

        try:
            self._spatial.record(
                tick=tick,
                resource_stock=resource_stock,
                effective_capacity=effective_capacity,
                effective_regeneration=effective_regeneration,
                recovery_remaining=recovery_remaining,
                baseline_capacity=baseline_capacity,
                baseline_regeneration=baseline_regeneration,
            )
        except BundlePublicationError:
            raise
        except Exception as error:
            raise BundlePublicationError("cannot append spatial output snapshot") from error

    def publish(
        self,
        *,
        summary: Mapping[str, object],
        records: RunRecords,
        rng_provenance: Mapping[str, str | tuple[int, ...]],
    ) -> Path:
        """Close, validate, and atomically publish the complete staged bundle."""

        if self._published:
            raise BundlePublicationError("run bundle session has already been published")
        try:
            self._spatial.close()
            _write_staged_bundle(
                self._staging,
                config=self.config,
                summary=summary,
                records=records,
                rng_provenance=rng_provenance,
            )
            _rename_noreplace(self._staging, self.destination)
        except BundlePublicationError:
            self.abort()
            raise
        except Exception as error:
            self.abort()
            raise BundlePublicationError("cannot finalize run bundle") from error
        self._published = True
        return self.destination

    def abort(self) -> None:
        """Close the stream and remove unpublished staging artifacts."""

        with suppress(Exception):
            self._spatial.close()
        if _path_exists(self._staging):
            shutil.rmtree(self._staging)

    def __enter__(self) -> RunBundleSession:
        return self

    def __exit__(self, *_exc: object) -> None:
        if not self._published:
            self.abort()


def write_run_bundle(
    destination: Path,
    *,
    config: SimulationConfig,
    summary: Mapping[str, object],
    records: RunRecords,
    rng_provenance: Mapping[str, str | tuple[int, ...]],
) -> Path:
    """Publish a complete zero-duration bundle; streaming runs use `RunBundleSession`."""

    if summary.get("completed_ticks") != 0:
        raise BundleValidationError("nonzero-duration bundles require a streaming RunBundleSession")
    stock, capacity = initialize_resources(
        (config.world.width, config.world.height),
        initial_stock=config.resources.initial_stock,
        capacity=config.resources.capacity,
    )
    regeneration = np.full(
        capacity.shape,
        config.resources.regeneration_rate,
        dtype=np.float64,
    )
    with RunBundleSession(destination, config) as session:
        session.record_spatial_snapshot(
            tick=0,
            resource_stock=stock,
            effective_capacity=capacity,
            effective_regeneration=regeneration,
            recovery_remaining=np.zeros(capacity.shape, dtype=np.int64),
            baseline_capacity=capacity,
            baseline_regeneration=regeneration,
        )
        return session.publish(
            summary=summary,
            records=records,
            rng_provenance=rng_provenance,
        )
