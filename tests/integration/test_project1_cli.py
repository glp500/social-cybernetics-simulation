import json
from pathlib import Path

import pyarrow.parquet as pq
from typer.testing import CliRunner

from social_cybernetics.analysis import validate_project1_analysis_bundle
from social_cybernetics.batch import validate_batch_bundle
from social_cybernetics.cli import app

runner = CliRunner()
BASELINE = Path("configs/baseline.yml").resolve()


def _write_tiny_plan(path: Path, *, seed: int = 101) -> None:
    path.write_text(
        f"""\
study: project_1
schema_version: "1.0.0"
base_config: {BASELINE}
seeds: [{seed}]
expected_runs: 1
max_runs: 1
groups:
  - id: p1-a
    duration: 1
    conditions:
      - id: control
        agent_count: 1
""",
        encoding="utf-8",
    )


def test_project1_cli_executes_then_analyzes_only_published_evidence(tmp_path: Path) -> None:
    plan = tmp_path / "project-1.yml"
    _write_tiny_plan(plan)
    batch = tmp_path / "batch"
    execution = runner.invoke(app, ["project1-run", "--spec", str(plan), "--output", str(batch)])

    assert execution.exit_code == 0
    assert json.loads(execution.stdout) == {
        "completed_runs": 1,
        "failed_runs": 0,
        "schema_version": "scs-batch-summary/v0.1.0",
        "status": "completed",
        "total_runs": 1,
    }
    assert validate_batch_bundle(batch)["completed_runs"] == 1

    output = tmp_path / "analysis"
    analysis = runner.invoke(
        app,
        [
            "project1-analyze",
            "--spec",
            str(plan),
            "--batch",
            str(batch),
            "--output",
            str(output),
        ],
    )

    assert analysis.exit_code == 0
    assert json.loads(analysis.stdout) == {
        "run_count": 1,
        "schema_version": "scs-project1-analysis-summary/v1.0.0",
        "status": "completed",
    }
    assert validate_project1_analysis_bundle(output)["run_count"] == 1
    payload = json.loads((output / "outcomes.json").read_text(encoding="utf-8"))
    record = payload["runs"][0]
    assert record["experiment_id"] == "p1-a"
    assert record["condition_id"] == "control"
    assert record["seed"] == 101
    assert record["outcome"]["schema_version"] == "scs-project1-outcome/v1.0.0"
    table = pq.read_table(output / "outcomes.parquet")
    assert table.column("aggregate_harvest").to_pylist() == [2.0]


def test_project1_analysis_rejects_mismatched_design_and_existing_output(tmp_path: Path) -> None:
    plan = tmp_path / "project-1.yml"
    _write_tiny_plan(plan)
    batch = tmp_path / "batch"
    assert (
        runner.invoke(app, ["project1-run", "--spec", str(plan), "--output", str(batch)]).exit_code
        == 0
    )

    mismatched = tmp_path / "mismatched.yml"
    _write_tiny_plan(mismatched, seed=202)
    rejected = runner.invoke(
        app,
        [
            "project1-analyze",
            "--spec",
            str(mismatched),
            "--batch",
            str(batch),
            "--output",
            str(tmp_path / "rejected"),
        ],
    )
    assert rejected.exit_code == 2
    assert json.loads(rejected.stderr)["error"] == "invalid_project1_evidence"
    assert not (tmp_path / "rejected").exists()

    output = tmp_path / "existing"
    output.mkdir()
    refused = runner.invoke(
        app,
        [
            "project1-analyze",
            "--spec",
            str(plan),
            "--batch",
            str(batch),
            "--output",
            str(output),
        ],
    )
    assert refused.exit_code == 1
    assert json.loads(refused.stderr)["error"] == "output_failure"
