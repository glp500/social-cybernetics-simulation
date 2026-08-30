import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from social_cybernetics.config import SimulationConfig
from social_cybernetics.domain import (
    ActionKind,
    AgentSnapshot,
    AgentTransitionRecord,
    CellDamageApplication,
    CohortRecord,
    DamageParameters,
    EventCellExposure,
    EventRecord,
    ModelRecord,
    ShockEventSnapshot,
    ShockEventStatus,
    ShockScope,
    ShockTerminationReason,
)
from social_cybernetics.persistence import (
    TABLE_SCHEMA_VERSIONS,
    BundleExistsError,
    BundleValidationError,
    RunBundleSession,
    RunRecords,
    build_record_tables,
    publish_directory_atomically,
    validate_run_bundle,
    write_run_bundle,
)


def _summary(*, seed: int = 42, completed_ticks: int = 0) -> dict[str, object]:
    return {
        "schema_version": "scs-run-summary/v0.1.0",
        "seed": seed,
        "completed_ticks": completed_ticks,
        "alive_count": 0,
        "dead_count": 0,
        "total_resources": 0.0,
        "cohort_mean_energy": 0.0,
        "total_harvest": 0.0,
        "unmet_need": 0.0,
        "inequality": {
            "energy_gini": 0.0,
            "harvest_gini": 0.0,
            "unmet_need_gini": 0.0,
        },
    }


def _rng_provenance() -> dict[str, str | tuple[int, ...]]:
    return {
        "bit_generator": "PCG64",
        "policy": (1,),
        "shock_initiation": (2, 1),
        "shock_location": (2, 2),
        "shock_transmission": (2, 3),
    }


def test_atomic_publication_exposes_only_the_completed_bundle(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"
    observed_during_build: list[bool] = []

    def build(staging: Path) -> None:
        observed_during_build.append(destination.exists())
        (staging / "manifest.json").write_text("complete", encoding="utf-8")

    published = publish_directory_atomically(destination, build)

    assert observed_during_build == [False]
    assert published == destination
    assert destination.is_dir()
    assert (destination / "manifest.json").read_text(encoding="utf-8") == "complete"
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


def test_existing_destination_is_refused_before_staging_or_build(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"
    destination.mkdir()
    (destination / "owner.txt").write_text("preserve", encoding="utf-8")
    build_called = False

    def build(_staging: Path) -> None:
        nonlocal build_called
        build_called = True

    with pytest.raises(BundleExistsError, match="already exists"):
        publish_directory_atomically(destination, build)

    assert build_called is False
    assert (destination / "owner.txt").read_text(encoding="utf-8") == "preserve"
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


def test_concurrent_destination_collision_is_refused_without_overwrite(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"

    def build(staging: Path) -> None:
        (staging / "manifest.json").write_text("candidate", encoding="utf-8")
        destination.mkdir()
        (destination / "owner.txt").write_text("winner", encoding="utf-8")

    with pytest.raises(BundleExistsError, match="already exists"):
        publish_directory_atomically(destination, build)

    assert (destination / "owner.txt").read_text(encoding="utf-8") == "winner"
    assert not (destination / "manifest.json").exists()
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


def test_failed_build_removes_staging_and_leaves_destination_absent(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"

    def build(staging: Path) -> None:
        (staging / "partial.txt").write_text("partial", encoding="utf-8")
        raise RuntimeError("validation failed")

    with pytest.raises(RuntimeError, match="validation failed"):
        publish_directory_atomically(destination, build)

    assert not destination.exists()
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


def test_publication_requires_an_existing_parent_directory(tmp_path: Path) -> None:
    destination = tmp_path / "missing" / "run-001"

    with pytest.raises(FileNotFoundError, match="parent directory"):
        publish_directory_atomically(destination, lambda _staging: None)

    assert not destination.parent.exists()


def test_broken_symlink_destination_is_treated_as_existing(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"
    os.symlink("missing-target", destination)

    with pytest.raises(BundleExistsError, match="already exists"):
        publish_directory_atomically(destination, lambda _staging: None)

    assert destination.is_symlink()


def test_record_tables_have_explicit_versioned_schemas_and_normalized_values() -> None:
    damage = DamageParameters(0.1, 0.2, 0.3, 4)
    records = RunRecords(
        model=(ModelRecord(1, 9.0, 1, 8.0, 2.0, 2.0, 0.0),),
        cohort=(
            CohortRecord(
                1,
                AgentSnapshot(
                    tick=1,
                    agent_id=7,
                    position=(2, 3),
                    energy=8.0,
                    alive=True,
                ),
            ),
        ),
        agent_transitions=(
            AgentTransitionRecord(
                tick=1,
                agent_id=7,
                origin=(2, 3),
                observed_stock=4.0,
                believed_stock=4.0,
                intent_kind=ActionKind.MOVE,
                requested_amount=0.0,
                intended_destination=(2, 2),
                gate_allowed=True,
                harvested=0.0,
                moved=True,
                final_position=(2, 2),
                energy_before=9.25,
                energy_after=8.0,
                shortfall=2.0,
                died=False,
            ),
        ),
        agent_events=(EventRecord(1, "move", 7, position=(2, 3)),),
        shock_events=(
            ShockEventSnapshot(
                tick=1,
                event_id=2,
                scope=ShockScope.CORRELATED,
                initiation_tick=0,
                epicenter=(1, 1),
                age=1,
                status=ShockEventStatus.TERMINATED,
                frontier=((1, 2), (2, 1)),
                affected_count=3,
                event_probability=0.4,
                damage=damage,
                spread_probability=0.5,
                max_spread_ticks=1,
                termination_reason=ShockTerminationReason.MAX_SPREAD_TICKS,
            ),
        ),
        shock_exposures=(
            EventCellExposure(
                tick=1,
                event_id=2,
                position=(2, 1),
                exposing_neighbors=((1, 1), (2, 0)),
                successful_neighbors=((1, 1),),
            ),
        ),
        cell_damage=(
            CellDamageApplication(
                tick=1,
                position=(2, 1),
                event_ids=(2, 3),
                combined_stock_multiplier=0.81,
                combined_capacity_multiplier=0.64,
                combined_regeneration_multiplier=0.49,
                pre_stock=10.0,
                post_stock=8.1,
                pre_effective_capacity=10.0,
                post_effective_capacity=6.4,
                pre_effective_regeneration=0.1,
                post_effective_regeneration=0.049,
                recovery_completion_tick=5,
            ),
        ),
    )

    tables = build_record_tables(records)

    assert tuple(tables) == tuple(TABLE_SCHEMA_VERSIONS)
    for name, table in tables.items():
        assert table.num_rows == 1
        assert table.schema.metadata is not None
        assert table.schema.metadata[b"scs.schema_version"].decode() == TABLE_SCHEMA_VERSIONS[name]

    assert tables["cohort"].to_pylist()[0] == {
        "tick": 1,
        "agent_id": 7,
        "position_x": 2,
        "position_y": 3,
        "energy": 8.0,
        "alive": True,
    }
    assert tables["agent_transitions"].to_pylist()[0] == {
        "tick": 1,
        "agent_id": 7,
        "origin_x": 2,
        "origin_y": 3,
        "observed_stock": 4.0,
        "believed_stock": 4.0,
        "intent_kind": "move",
        "requested_amount": 0.0,
        "intended_destination_x": 2,
        "intended_destination_y": 2,
        "gate_allowed": True,
        "harvested": 0.0,
        "moved": True,
        "final_position_x": 2,
        "final_position_y": 2,
        "energy_before": 9.25,
        "energy_after": 8.0,
        "shortfall": 2.0,
        "died": False,
    }
    assert tables["shock_events"].to_pylist()[0]["frontier"] == [
        {"x": 1, "y": 2},
        {"x": 2, "y": 1},
    ]
    assert tables["shock_exposures"].to_pylist()[0]["transmitted"] is True
    assert tables["cell_damage"].to_pylist()[0]["event_ids"] == [2, 3]


def test_empty_record_tables_retain_complete_schemas() -> None:
    tables = build_record_tables(RunRecords())

    assert tuple(tables) == tuple(TABLE_SCHEMA_VERSIONS)
    assert all(table.num_rows == 0 for table in tables.values())
    assert all(table.num_columns > 0 for table in tables.values())


def test_transition_count_must_match_active_agent_history(tmp_path: Path) -> None:
    transition = AgentTransitionRecord(
        tick=1,
        agent_id=0,
        origin=(2, 2),
        observed_stock=10.0,
        believed_stock=10.0,
        intent_kind=ActionKind.HARVEST,
        requested_amount=2.0,
        intended_destination=None,
        gate_allowed=True,
        harvested=2.0,
        moved=False,
        final_position=(2, 2),
        energy_before=10.0,
        energy_after=11.0,
        shortfall=0.0,
        died=False,
    )
    records = RunRecords(
        model=(ModelRecord(0, 250.0, 1, 10.0, 0.0, 0.0, 0.0),),
        cohort=(CohortRecord(0, AgentSnapshot(0, 0, (2, 2), 10.0, True)),),
        agent_transitions=(transition,),
    )

    with pytest.raises(BundleValidationError, match="transition count"):
        write_run_bundle(
            tmp_path / "invalid",
            config=SimulationConfig(duration=0),
            summary=_summary(),
            records=records,
            rng_provenance=_rng_provenance(),
        )

    assert not (tmp_path / "invalid").exists()


def test_run_bundle_round_trips_configuration_provenance_summary_and_tables(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "run-001"
    config = SimulationConfig(seed=9, duration=0)
    summary = _summary(seed=9)
    records = RunRecords(model=(ModelRecord(0, 250.0, 1, 10.0, 0.0, 0.0, 0.0),))
    rng_provenance = _rng_provenance()

    published = write_run_bundle(
        destination,
        config=config,
        summary=summary,
        records=records,
        rng_provenance=rng_provenance,
    )
    manifest = validate_run_bundle(published)

    assert published == destination
    assert manifest["schema_version"] == "scs-run-bundle/v1.1.0"
    assert manifest["seed"] == 9
    assert manifest["tables"]["model"]["row_count"] == 1
    assert manifest["tables"]["cohort"]["row_count"] == 0
    assert set(manifest["files"]) == {
        "configuration.json",
        "provenance.json",
        "summary.json",
        "spatial.nc",
        "tables/agent_events.parquet",
        "tables/agent_transitions.parquet",
        "tables/cell_damage.parquet",
        "tables/cohort.parquet",
        "tables/model.parquet",
        "tables/shock_events.parquet",
        "tables/shock_exposures.parquet",
    }

    configuration = json.loads((destination / "configuration.json").read_text())
    provenance = json.loads((destination / "provenance.json").read_text())
    persisted_summary = json.loads((destination / "summary.json").read_text())
    assert configuration == {
        "schema_version": "scs-normalized-configuration/v0.1.0",
        "configuration": config.model_dump(mode="json"),
    }
    assert provenance["schema_version"] == "scs-provenance/v0.1.0"
    assert provenance["seed"] == 9
    assert provenance["rng"]["streams"]["policy"] == [1]
    assert provenance["software"]["packages"]["mesa"] == "3.5.1"
    assert persisted_summary == summary

    model_table = pq.read_table(destination / "tables/model.parquet")
    assert model_table.to_pylist() == build_record_tables(records)["model"].to_pylist()
    assert (
        model_table.schema.metadata[b"scs.schema_version"].decode()
        == TABLE_SCHEMA_VERSIONS["model"]
    )


def test_bundle_validation_detects_post_publication_tampering(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"
    write_run_bundle(
        destination,
        config=SimulationConfig(duration=0),
        summary=_summary(),
        records=RunRecords(),
        rng_provenance=_rng_provenance(),
    )
    summary_path = destination / "summary.json"
    tampered = bytearray(summary_path.read_bytes())
    tampered[tampered.index(ord("4"))] = ord("9")
    summary_path.write_bytes(tampered)

    with pytest.raises(BundleValidationError, match="digest mismatch"):
        validate_run_bundle(destination)


def test_bundle_validation_rejects_manifest_schema_tampering(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"
    write_run_bundle(
        destination,
        config=SimulationConfig(duration=0),
        summary=_summary(),
        records=RunRecords(),
        rng_provenance=_rng_provenance(),
    )
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["summary.json"]["schema_version"] = "unknown"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(BundleValidationError, match="artifact schema version"):
        validate_run_bundle(destination)


def test_identical_inputs_produce_identical_manifests_and_file_digests(tmp_path: Path) -> None:
    config = SimulationConfig(duration=0)
    summary = _summary()
    arguments = {
        "config": config,
        "summary": summary,
        "records": RunRecords(),
        "rng_provenance": _rng_provenance(),
    }

    first = write_run_bundle(tmp_path / "first", **arguments)
    second = write_run_bundle(tmp_path / "second", **arguments)

    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()


def test_bundle_writer_rejects_an_incomplete_summary_without_creating_output(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "run-001"

    with pytest.raises(BundleValidationError, match="summary fields"):
        write_run_bundle(
            destination,
            config=SimulationConfig(duration=0),
            summary={
                "schema_version": "scs-run-summary/v0.1.0",
                "seed": 42,
                "completed_ticks": 0,
            },
            records=RunRecords(),
            rng_provenance=_rng_provenance(),
        )

    assert not destination.exists()


def test_bundle_validation_wraps_a_missing_manifest_as_a_contract_error(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "incomplete"
    bundle.mkdir()

    with pytest.raises(BundleValidationError, match="invalid JSON artifact"):
        validate_run_bundle(bundle)


def test_bundle_writer_rejects_rng_registry_drift(tmp_path: Path) -> None:
    provenance = _rng_provenance()
    provenance["shock_transmission"] = (2, 99)

    with pytest.raises(BundleValidationError, match="RNG stream registry"):
        write_run_bundle(
            tmp_path / "run-001",
            config=SimulationConfig(duration=0),
            summary=_summary(),
            records=RunRecords(),
            rng_provenance=provenance,
        )


def test_required_netcdf_package_must_be_present_for_a_spatial_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from importlib.metadata import PackageNotFoundError

    import social_cybernetics.persistence as persistence

    real_version = persistence.importlib.metadata.version

    def version_or_missing(name: str) -> str:
        if name == "netCDF4":
            raise PackageNotFoundError(name)
        return real_version(name)

    monkeypatch.setattr(persistence.importlib.metadata, "version", version_or_missing)
    with pytest.raises(BundleValidationError, match="required package metadata.*netCDF4"):
        write_run_bundle(
            tmp_path / "run-001",
            config=SimulationConfig(duration=0),
            summary=_summary(),
            records=RunRecords(),
            rng_provenance=_rng_provenance(),
        )


def test_run_bundle_session_cleans_an_unpublished_spatial_stream(tmp_path: Path) -> None:
    destination = tmp_path / "run-001"
    config = SimulationConfig(duration=0)

    with (
        pytest.raises(RuntimeError, match="model failed"),
        RunBundleSession(destination, config) as session,
    ):
        session.record_spatial_snapshot(
            tick=0,
            resource_stock=np.full((5, 5), 10.0),
            effective_capacity=np.full((5, 5), 10.0),
            effective_regeneration=np.full((5, 5), 0.1),
            recovery_remaining=np.zeros((5, 5), dtype=np.int64),
            baseline_capacity=np.full((5, 5), 10.0),
            baseline_regeneration=np.full((5, 5), 0.1),
        )
        raise RuntimeError("model failed")

    assert not destination.exists()
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


def test_bundle_validation_revalidates_the_normalized_configuration(tmp_path: Path) -> None:
    destination = write_run_bundle(
        tmp_path / "run-001",
        config=SimulationConfig(duration=0),
        summary=_summary(),
        records=RunRecords(),
        rng_provenance=_rng_provenance(),
    )
    configuration_path = destination / "configuration.json"
    configuration = json.loads(configuration_path.read_text())
    configuration["configuration"]["duration"] = -1
    configuration_path.write_text(
        json.dumps(configuration, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    descriptor = manifest["files"]["configuration.json"]
    contents = configuration_path.read_bytes()
    descriptor["byte_count"] = len(contents)
    descriptor["sha256"] = hashlib.sha256(contents).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(BundleValidationError, match="normalized configuration is invalid"):
        validate_run_bundle(destination)


def test_bundle_validation_does_not_materialize_parquet_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = write_run_bundle(
        tmp_path / "run-001",
        config=SimulationConfig(duration=0),
        summary=_summary(),
        records=RunRecords(model=(ModelRecord(0, 0.0, 0, 0.0, 0.0, 0.0, 0.0),)),
        rng_provenance=_rng_provenance(),
    )

    def unexpected_read(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("bundle validation must use Parquet metadata")

    monkeypatch.setattr("social_cybernetics.persistence.pq.read_table", unexpected_read)

    validate_run_bundle(destination)
