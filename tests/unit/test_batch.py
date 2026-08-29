import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from social_cybernetics.artifact_io import sha256_file, write_json
from social_cybernetics.batch import execute_batch, validate_batch_bundle
from social_cybernetics.batch_config import load_batch_specification
from social_cybernetics.domain import InvariantViolationError
from social_cybernetics.persistence import BundleExistsError, BundleValidationError
from social_cybernetics.runtime.mesa import SugarscapeModel


def _write_specification(tmp_path: Path, runs: str) -> Path:
    (tmp_path / "base.yml").write_text("duration: 0\n", encoding="utf-8")
    specification = tmp_path / "batch.yml"
    specification.write_text(
        f"""schema_version: "0.1.0"
base_config: base.yml
runs:
{runs}""",
        encoding="utf-8",
    )
    return specification


def _tree_digests(path: Path) -> dict[str, str]:
    return {
        item.relative_to(path).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def test_batch_executes_in_declared_order_and_publishes_valid_indexes(tmp_path: Path) -> None:
    specification = _write_specification(
        tmp_path,
        """  - id: first-seed
    overrides: {seed: 12}
  - id: second-seed
    overrides: {seed: 4}
""",
    )
    destination = tmp_path / "batch-output"

    result = execute_batch(load_batch_specification(specification), destination)
    manifest = validate_batch_bundle(destination)
    index = json.loads((destination / "runs.json").read_text(encoding="utf-8"))
    parquet_rows = pq.read_table(destination / "runs.parquet").to_pylist()

    assert result.status == "completed"
    assert result.completed_runs == 2
    assert result.failed_runs == 0
    assert manifest["status"] == "completed"
    assert [row["run_id"] for row in index["runs"]] == ["first-seed", "second-seed"]
    assert [row["seed"] for row in index["runs"]] == [12, 4]
    assert [row["run_id"] for row in parquet_rows] == ["first-seed", "second-seed"]
    assert all(row["status"] == "completed" for row in parquet_rows)
    assert all(row["error_kind"] is None for row in parquet_rows)
    assert (destination / "runs/first-seed/manifest.json").is_file()
    assert (destination / "runs/second-seed/manifest.json").is_file()


def test_batch_continues_after_a_failed_run_without_a_partial_child_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specification = _write_specification(
        tmp_path,
        """  - id: expected-failure
    overrides: {seed: 1}
  - id: completed-after-failure
    overrides: {seed: 2}
""",
    )
    resolved = load_batch_specification(specification)
    destination = tmp_path / "batch-output"
    original_run = SugarscapeModel.run
    attempted: list[int] = []

    def selectively_fail(model: SugarscapeModel) -> None:
        attempted.append(model.config.seed)
        if model.config.seed == 1:
            raise RuntimeError("controlled test failure")
        original_run(model)

    monkeypatch.setattr("social_cybernetics.batch.SugarscapeModel.run", selectively_fail)

    result = execute_batch(resolved, destination)
    manifest = validate_batch_bundle(destination)
    index = json.loads((destination / "runs.json").read_text(encoding="utf-8"))["runs"]

    assert attempted == [1, 2]
    assert result.status == "completed_with_failures"
    assert result.completed_runs == 1
    assert result.failed_runs == 1
    assert manifest["status"] == "completed_with_failures"
    assert index[0]["status"] == "failed"
    assert index[0]["error"] == {
        "kind": "runtime_failure",
        "message": "controlled test failure",
    }
    assert index[0]["bundle_path"] is None
    assert index[1]["status"] == "completed"
    assert not (destination / "runs/expected-failure").exists()
    assert (destination / "runs/completed-after-failure/manifest.json").is_file()
    assert not tuple((destination / "runs").glob(".expected-failure.staging-*"))


def test_existing_batch_destination_is_refused_before_any_model_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specification = _write_specification(
        tmp_path,
        """  - id: first
    overrides: {seed: 1}
""",
    )
    destination = tmp_path / "batch-output"
    destination.mkdir()
    marker = destination / "owner.txt"
    marker.write_text("preserve", encoding="utf-8")

    def unexpected_run(_model: object) -> None:
        raise AssertionError("model must not execute")

    monkeypatch.setattr("social_cybernetics.batch.SugarscapeModel.run", unexpected_run)

    with pytest.raises(BundleExistsError, match="already exists"):
        execute_batch(load_batch_specification(specification), destination)

    assert marker.read_text(encoding="utf-8") == "preserve"
    assert not tuple(tmp_path.glob(".batch-output.staging-*"))


def test_identical_batch_reruns_produce_identical_complete_bundles(tmp_path: Path) -> None:
    specification = _write_specification(
        tmp_path,
        """  - id: repeated-a
    overrides: {seed: 8}
  - id: repeated-b
    overrides: {seed: 8}
""",
    )
    resolved = load_batch_specification(specification)
    first = tmp_path / "first"
    second = tmp_path / "second"

    execute_batch(resolved, first)
    execute_batch(resolved, second)

    assert _tree_digests(first) == _tree_digests(second)


def test_batch_validation_detects_index_tampering(tmp_path: Path) -> None:
    specification = _write_specification(
        tmp_path,
        """  - id: only-run
    overrides: {seed: 3}
""",
    )
    destination = tmp_path / "batch-output"
    execute_batch(load_batch_specification(specification), destination)
    index_path = destination / "runs.json"
    index_path.write_text(index_path.read_text(encoding="utf-8").replace("only-run", "evil-run"))

    with pytest.raises(BundleValidationError, match="digest mismatch"):
        validate_batch_bundle(destination)


def _rewrite_indexed_json(destination: Path, name: str, payload: dict[str, object]) -> None:
    path = destination / name
    write_json(path, payload)
    manifest_path = destination / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name]["byte_count"] = path.stat().st_size
    manifest["files"][name]["sha256"] = sha256_file(path)
    write_json(manifest_path, manifest)


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("normalized-schema", "normalized batch schema"),
        ("source-schema", "source batch schema"),
        ("base-source", "base configuration source"),
        ("empty-runs", "at least one run"),
        ("run-fields", "normalized run fields"),
        ("run-id", "identity or overrides"),
        ("run-order", "run order"),
        ("run-configuration", "resolved run configuration is invalid"),
        ("not-normalized", "run configuration is not normalized"),
        ("merge", "differs from its overrides"),
        ("configuration-digest", "configuration digest"),
        ("index-fields", "index record fields"),
        ("index-provenance", "index differs from normalized"),
        ("completed-shape", "completed batch index record"),
        ("summary-seed", "summary seed differs"),
        ("run-status", "run status is unsupported"),
        ("manifest-count", "manifest counts or status"),
        ("manifest-runs", "run descriptors are malformed"),
        ("run-descriptor", "descriptor differs from the batch index"),
        ("child-descriptor", "child run bundle differs"),
        ("extra-child", "child directory set"),
    ],
)
def test_batch_validation_rejects_cross_artifact_contract_violations(
    tmp_path: Path, case: str, message: str
) -> None:
    case_directory = tmp_path / case
    case_directory.mkdir()
    specification = _write_specification(
        case_directory,
        """  - id: only-run
    overrides: {seed: 3}
""",
    )
    destination = case_directory / "batch-output"
    execute_batch(load_batch_specification(specification), destination)

    specification_path = destination / "batch_specification.json"
    normalized = json.loads(specification_path.read_text(encoding="utf-8"))
    index_path = destination / "runs.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    manifest_path = destination / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if case == "normalized-schema":
        normalized["schema_version"] = "unknown"
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "source-schema":
        normalized["source_schema_version"] = "unknown"
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "base-source":
        normalized["base_config_source"] = 7
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "empty-runs":
        normalized["runs"] = []
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "run-fields":
        normalized["runs"][0].pop("configuration")
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "run-id":
        normalized["runs"][0]["run_id"] = "../unsafe"
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "run-order":
        normalized["runs"][0]["ordinal"] = 1
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "run-configuration":
        normalized["runs"][0]["configuration"]["seed"] = -1
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "not-normalized":
        normalized["runs"][0]["configuration"]["world"].pop("torus")
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "merge":
        normalized["runs"][0]["configuration"]["duration"] = 1
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "configuration-digest":
        normalized["runs"][0]["configuration_sha256"] = "0" * 64
        _rewrite_indexed_json(destination, specification_path.name, normalized)
    elif case == "index-fields":
        index["runs"][0].pop("seed")
        _rewrite_indexed_json(destination, index_path.name, index)
    elif case == "index-provenance":
        index["runs"][0]["seed"] = 4
        _rewrite_indexed_json(destination, index_path.name, index)
    elif case == "completed-shape":
        index["runs"][0]["bundle_path"] = None
        _rewrite_indexed_json(destination, index_path.name, index)
    elif case == "summary-seed":
        index["runs"][0]["summary"]["seed"] = 4
        _rewrite_indexed_json(destination, index_path.name, index)
    elif case == "run-status":
        index["runs"][0]["status"] = "unknown"
        _rewrite_indexed_json(destination, index_path.name, index)
    elif case == "manifest-count":
        manifest["completed_runs"] = 0
        write_json(manifest_path, manifest)
    elif case == "manifest-runs":
        manifest["runs"] = []
        write_json(manifest_path, manifest)
    elif case == "run-descriptor":
        manifest["runs"][0]["status"] = "failed"
        write_json(manifest_path, manifest)
    elif case == "child-descriptor":
        manifest["runs"][0]["run_bundle_schema_version"] = "unknown"
        write_json(manifest_path, manifest)
    elif case == "extra-child":
        (destination / "runs/extra-child").mkdir()

    with pytest.raises(BundleValidationError, match=message):
        validate_batch_bundle(destination)


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (InvariantViolationError("broken invariant"), "invariant_failure"),
        (BundleValidationError("broken output"), "output_failure"),
    ],
)
def test_batch_indexes_typed_invariant_and_output_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    kind: str,
) -> None:
    specification = _write_specification(
        tmp_path,
        """  - id: failed-run
    overrides: {seed: 3}
""",
    )
    destination = tmp_path / "batch-output"

    def fail_run(_model: object) -> None:
        raise error

    monkeypatch.setattr("social_cybernetics.batch.SugarscapeModel.run", fail_run)

    execute_batch(load_batch_specification(specification), destination)

    record = json.loads((destination / "runs.json").read_text(encoding="utf-8"))["runs"][0]
    assert record["error"]["kind"] == kind
