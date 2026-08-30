"""Integration coverage for artifact-only Project 1 analysis."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from social_cybernetics.analysis import analyze_run_bundle
from social_cybernetics.cli import app
from social_cybernetics.persistence import BundleValidationError

runner = CliRunner()


def test_project1_outcome_is_reconstructed_only_from_a_published_bundle(tmp_path: Path) -> None:
    config = tmp_path / "tiny.yml"
    config.write_text("duration: 1\n", encoding="utf-8")
    bundle = tmp_path / "run"
    result = runner.invoke(app, ["run", "--config", str(config), "--output", str(bundle)])
    assert result.exit_code == 0

    outcome = analyze_run_bundle(bundle)
    payload = outcome.as_payload()

    assert payload["schema_version"] == "scs-project1-outcome/v1.0.0"
    assert payload["seed"] == 42
    assert payload["completed_ticks"] == 1
    assert payload["cohort_size"] == 1
    assert payload["aggregate_harvest"] == 2.0
    assert payload["survival_fraction"] == 1.0
    assert payload["mean_unmet_need"] == 0.0
    assert payload["subsistence"]["shortfall_frequency"] == 0.0  # type: ignore[index]
    assert payload["distribution"]["harvest_gini"] == 0.0  # type: ignore[index]
    assert payload["persistence"]["material_rank_autocorrelation"] == {  # type: ignore[index]
        "value": None,
        "reason": "fewer than two agents",
    }
    assert payload["ecology"]["resource_depletion"]["final"] == pytest.approx(0.008)  # type: ignore[index]
    assert payload["ecology"]["cumulative_recovery_deficit"] == 0.0  # type: ignore[index]
    json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def test_project1_analysis_rejects_an_unvalidated_directory(tmp_path: Path) -> None:
    bundle = tmp_path / "not-a-bundle"
    bundle.mkdir()

    with pytest.raises((BundleValidationError, FileNotFoundError)):
        analyze_run_bundle(bundle)
