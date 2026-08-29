import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest
from netCDF4 import Dataset
from typer.testing import CliRunner

from social_cybernetics.batch import execute_batch, validate_batch_bundle
from social_cybernetics.batch_config import load_batch_specification
from social_cybernetics.cli import app
from social_cybernetics.domain import InvariantViolationError
from social_cybernetics.persistence import validate_run_bundle
from social_cybernetics.runtime.mesa import SugarscapeModel

runner = CliRunner()
BASELINE = Path("configs/baseline.yml")
ECOLOGY_V02 = Path("configs/ecology-v0.2.yml")
VERIFICATION_V02 = Path("configs/verification-v0.2.yml")


def test_validate_reports_a_schema_versioned_success() -> None:
    result = runner.invoke(app, ["validate", "--config", str(BASELINE)])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"schema_version": "0.1.0", "status": "valid"}


def test_validate_accepts_the_v02_explicit_landscape_fixture() -> None:
    result = runner.invoke(app, ["validate", "--config", str(ECOLOGY_V02)])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"schema_version": "0.2.0", "status": "valid"}


def test_invalid_configuration_has_stable_exit_code(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text("policy:\n  kind: q_learning\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--config", str(path)])

    assert result.exit_code == 2
    assert json.loads(result.stderr)["error"] == "invalid_configuration"


def test_run_is_deterministic_and_matches_the_checked_in_regression() -> None:
    first = runner.invoke(app, ["run", "--config", str(BASELINE)])
    second = runner.invoke(app, ["run", "--config", str(BASELINE)])
    expected = Path("tests/fixtures/baseline_summary.json").read_text(encoding="utf-8")

    assert first.exit_code == 0
    assert first.stdout == second.stdout == expected
    summary = json.loads(first.stdout)
    assert summary["seed"] == 42
    assert summary["completed_ticks"] == 100
    assert summary["alive_count"] + summary["dead_count"] == 1


def test_v02_explicit_ecology_run_matches_the_checked_in_regression() -> None:
    first = runner.invoke(app, ["run", "--config", str(ECOLOGY_V02)])
    second = runner.invoke(app, ["run", "--config", str(ECOLOGY_V02)])
    expected = Path("tests/fixtures/ecology_v0.2_summary.json").read_text(encoding="utf-8")

    assert first.exit_code == 0
    assert first.stdout == second.stdout == expected
    summary = json.loads(first.stdout)
    assert summary["completed_ticks"] == 100
    assert summary["total_resources"] == pytest.approx(31.99968126321335)


def test_run_output_publishes_a_valid_bundle_without_changing_stdout(tmp_path: Path) -> None:
    config = tmp_path / "tiny.yml"
    config.write_text("duration: 1\n", encoding="utf-8")
    destination = tmp_path / "run-001"

    result = runner.invoke(
        app,
        ["run", "--config", str(config), "--output", str(destination)],
    )
    manifest = validate_run_bundle(destination)

    assert result.exit_code == 0
    assert json.loads(result.stdout)["completed_ticks"] == 1
    assert manifest["completed_ticks"] == 1
    assert manifest["tables"]["model"]["row_count"] == 2
    assert manifest["tables"]["cohort"]["row_count"] == 2
    assert manifest["spatial"]["snapshot_count"] == 2
    assert json.loads((destination / "summary.json").read_text()) == json.loads(result.stdout)
    with Dataset(destination / "spatial.nc", "r") as spatial:
        np.testing.assert_array_equal(spatial.variables["tick"][:], [0, 1])
        assert spatial.variables["resource_stock"].shape == (2, 5, 5)


def test_run_output_persists_runtime_shock_and_damage_records(tmp_path: Path) -> None:
    config = tmp_path / "system-shock.yml"
    config.write_text(
        """schema_version: "0.2.0"
duration: 1
world:
  width: 2
  height: 1
agents:
  count: 0
  initial_positions: []
shock:
  kind: system
  event_probability: 1.0
  stock_loss_fraction: 0.1
  capacity_loss_fraction: 0.2
  regeneration_suppression_fraction: 0.3
  recovery_ticks: 4
""",
        encoding="utf-8",
    )
    destination = tmp_path / "shock-run"

    result = runner.invoke(
        app,
        ["run", "--config", str(config), "--output", str(destination)],
    )
    manifest = validate_run_bundle(destination)

    assert result.exit_code == 0
    assert manifest["tables"]["shock_events"]["row_count"] == 1
    assert manifest["tables"]["shock_exposures"]["row_count"] == 0
    assert manifest["tables"]["cell_damage"]["row_count"] == 2

    shock = pq.read_table(destination / "tables/shock_events.parquet").to_pylist()[0]
    damage = pq.read_table(destination / "tables/cell_damage.parquet").to_pylist()
    assert shock["scope"] == "system"
    assert shock["affected_count"] == 2
    assert [record["event_ids"] for record in damage] == [[1], [1]]
    with Dataset(destination / "spatial.nc", "r") as spatial:
        np.testing.assert_allclose(spatial.variables["resource_stock"][0, :, :], 10.0)
        np.testing.assert_allclose(spatial.variables["resource_stock"][1, :, :], 9.0)
        np.testing.assert_allclose(spatial.variables["effective_capacity"][1, :, :], 8.0)
        np.testing.assert_allclose(spatial.variables["effective_regeneration"][1, :, :], 0.07)
        np.testing.assert_array_equal(spatial.variables["recovery_remaining"][1, :, :], 4)


def test_existing_output_fails_before_model_execution_and_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "run-001"
    destination.mkdir()
    marker = destination / "owner.txt"
    marker.write_text("preserve", encoding="utf-8")

    def unexpected_run(_model: object) -> None:
        raise AssertionError("model must not run for an unavailable output destination")

    monkeypatch.setattr("social_cybernetics.cli.SugarscapeModel.run", unexpected_run)
    result = runner.invoke(
        app,
        ["run", "--config", str(BASELINE), "--output", str(destination)],
    )

    assert result.exit_code == 1
    assert json.loads(result.stderr)["error"] == "output_failure"
    assert marker.read_text(encoding="utf-8") == "preserve"
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


@pytest.mark.parametrize(
    ("error", "error_name"),
    [
        (InvariantViolationError("broken invariant"), "invariant_failure"),
        (ValueError("broken value"), "runtime_failure"),
        (RuntimeError("broken runtime"), "runtime_failure"),
    ],
)
def test_run_failures_have_stable_exit_behavior(
    monkeypatch: pytest.MonkeyPatch, error: Exception, error_name: str
) -> None:
    def fail_run(_model: object) -> None:
        raise error

    monkeypatch.setattr("social_cybernetics.cli.SugarscapeModel.run", fail_run)

    result = runner.invoke(app, ["run", "--config", str(BASELINE)])

    assert result.exit_code == 1
    assert json.loads(result.stderr)["error"] == error_name


def test_runtime_failure_removes_the_streaming_output_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "run-001"

    def fail_run(_model: object) -> None:
        raise RuntimeError("broken runtime")

    monkeypatch.setattr("social_cybernetics.cli.SugarscapeModel.run", fail_run)

    result = runner.invoke(
        app,
        ["run", "--config", str(BASELINE), "--output", str(destination)],
    )

    assert result.exit_code == 1
    assert json.loads(result.stderr)["error"] == "runtime_failure"
    assert not destination.exists()
    assert not tuple(tmp_path.glob(".run-001.staging-*"))


def test_batch_command_publishes_a_complete_attempt_and_stable_summary(tmp_path: Path) -> None:
    base = tmp_path / "base.yml"
    base.write_text("duration: 0\n", encoding="utf-8")
    specification = tmp_path / "batch.yml"
    specification.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: seed-one
    overrides: {seed: 1}
  - id: seed-two
    overrides: {seed: 2}
""",
        encoding="utf-8",
    )
    destination = tmp_path / "batch-output"

    result = runner.invoke(
        app,
        ["batch", "--spec", str(specification), "--output", str(destination)],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "schema_version": "scs-batch-summary/v0.1.0",
        "status": "completed",
        "total_runs": 2,
        "completed_runs": 2,
        "failed_runs": 0,
    }
    assert validate_batch_bundle(destination)["completed_runs"] == 2


def test_batch_command_publishes_failures_continues_and_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "base.yml"
    base.write_text("duration: 0\n", encoding="utf-8")
    specification = tmp_path / "batch.yml"
    specification.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: failed
    overrides: {seed: 1}
  - id: completed
    overrides: {seed: 2}
""",
        encoding="utf-8",
    )
    destination = tmp_path / "batch-output"
    original_run = SugarscapeModel.run

    def selectively_fail(model: SugarscapeModel) -> None:
        if model.config.seed == 1:
            raise RuntimeError("controlled failure")
        original_run(model)

    monkeypatch.setattr("social_cybernetics.batch.SugarscapeModel.run", selectively_fail)

    result = runner.invoke(
        app,
        ["batch", "--spec", str(specification), "--output", str(destination)],
    )

    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] == "completed_with_failures"
    assert json.loads(result.stdout)["failed_runs"] == 1
    assert validate_batch_bundle(destination)["completed_runs"] == 1


def test_batch_command_rejects_invalid_specification_before_creating_output(
    tmp_path: Path,
) -> None:
    specification = tmp_path / "invalid.yml"
    specification.write_text(
        """schema_version: "0.1.0"
base_config: missing.yml
runs:
  - id: no-seed
    overrides: {duration: 0}
""",
        encoding="utf-8",
    )
    destination = tmp_path / "batch-output"

    result = runner.invoke(
        app,
        ["batch", "--spec", str(specification), "--output", str(destination)],
    )

    assert result.exit_code == 2
    assert json.loads(result.stderr)["error"] == "invalid_batch_specification"
    assert not destination.exists()


def test_sensitivity_command_executes_generated_runs_through_batch_boundary(
    tmp_path: Path,
) -> None:
    base = tmp_path / "base.yml"
    base.write_text(
        """schema_version: "0.2.0"
duration: 0
world: {width: 1, height: 1}
agents: {count: 0, initial_positions: []}
shock: {kind: none}
""",
        encoding="utf-8",
    )
    specification = tmp_path / "sensitivity.yml"
    specification.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
design:
  kind: morris
  seed: 42
  num_levels: 4
  candidate_trajectories: 4
  selected_trajectories: 2
  local_optimization: true
model_seeds: [11]
max_runs: 4
scopes:
  - kind: independent
    fixed_overrides:
      shock:
        kind: independent
        event_probability: 0.5
        stock_loss_fraction: 0.0
        capacity_loss_fraction: 0.0
        regeneration_suppression_fraction: 0.0
        recovery_ticks: 1
    factors:
      - path: shock.event_probability
        kind: float
        lower: 0.0
        upper: 1.0
""",
        encoding="utf-8",
    )
    destination = tmp_path / "sensitivity-output"

    result = runner.invoke(
        app,
        ["sensitivity", "--spec", str(specification), "--output", str(destination)],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "schema_version": "scs-batch-summary/v0.1.0",
        "status": "completed",
        "total_runs": 4,
        "completed_runs": 4,
        "failed_runs": 0,
    }
    assert validate_batch_bundle(destination)["completed_runs"] == 4


def test_sensitivity_command_rejects_invalid_design_before_creating_output(
    tmp_path: Path,
) -> None:
    specification = tmp_path / "invalid-sensitivity.yml"
    specification.write_text(
        """schema_version: "0.1.0"
base_config: missing.yml
design:
  kind: morris
  seed: 42
  num_levels: 3
  candidate_trajectories: 4
  selected_trajectories: 2
  local_optimization: true
model_seeds: [11]
max_runs: 4
scopes: []
""",
        encoding="utf-8",
    )
    destination = tmp_path / "sensitivity-output"

    result = runner.invoke(
        app,
        ["sensitivity", "--spec", str(specification), "--output", str(destination)],
    )

    assert result.exit_code == 2
    assert json.loads(result.stderr)["error"] == "invalid_sensitivity_specification"
    assert not destination.exists()


def test_checked_verification_batch_reproduces_controls_from_published_artifacts(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "verification-output"

    result = execute_batch(load_batch_specification(VERIFICATION_V02), destination)
    manifest = validate_batch_bundle(destination)
    rows = pq.read_table(destination / "runs.parquet").to_pylist()
    by_id = {row["run_id"]: row for row in rows}

    assert result.failed_runs == 0
    assert manifest["completed_runs"] == 12
    assert len(rows) == 12
    assert by_id["no-shock-r00"]["total_resources"] == by_id["sham-shock-r00"]["total_resources"]
    assert (
        by_id["no-shock-r00"]["cohort_mean_energy"] == by_id["sham-shock-r00"]["cohort_mean_energy"]
    )
    assert by_id["scarcity-r00"]["alive_count"] == 0
    assert by_id["scarcity-r00"]["dead_count"] == 1

    for scope in ("independent", "correlated", "system"):
        scope_rows = [by_id[f"{scope}-r{replicate:02d}"] for replicate in range(3)]
        assert [row["seed"] for row in scope_rows] == [101, 202, 303]
        assert all(row["total_resources"] is not None for row in scope_rows)

    expected_scope_resources = {
        "independent-r00": 8.715809716438953,
        "independent-r01": 7.073722154063787,
        "independent-r02": 4.539701105364262,
        "correlated-r00": 6.276785011574074,
        "correlated-r01": 4.9083322916666665,
        "correlated-r02": 7.2462439597800925,
        "system-r00": 2.66325649911386,
        "system-r01": 4.84471103515625,
        "system-r02": 2.4621169144241897,
    }
    assert {
        run_id: by_id[run_id]["total_resources"] for run_id in expected_scope_resources
    } == expected_scope_resources

    with Dataset(destination / "runs/correlated-r00/spatial.nc", "r") as spatial:
        np.testing.assert_array_equal(spatial.variables["tick"][:], np.arange(6))
        assert spatial.variables["resource_stock"].shape == (6, 3, 2)
