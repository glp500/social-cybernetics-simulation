from collections import Counter
from pathlib import Path

import pytest

from social_cybernetics.config import IndependentShockConfig
from social_cybernetics.sensitivity import load_sensitivity_design

CHECKED_SENSITIVITY = Path("configs/sensitivity-v0.2.yml")


def _write_base(path: Path) -> None:
    path.write_text(
        """schema_version: "0.2.0"
duration: 0
world:
  width: 1
  height: 1
agents:
  count: 0
  initial_positions: []
shock:
  kind: none
""",
        encoding="utf-8",
    )


def _independent_spec(*, factor: str = "shock.event_probability", max_runs: int = 8) -> str:
    return f"""schema_version: "0.1.0"
base_config: base.yml
design:
  kind: morris
  seed: 42
  num_levels: 4
  candidate_trajectories: 4
  selected_trajectories: 2
  local_optimization: true
model_seeds: [11, 22]
max_runs: {max_runs}
scopes:
  - kind: independent
    fixed_overrides:
      shock:
        kind: independent
        event_probability: 0.5
        stock_loss_fraction: 0.5
        capacity_loss_fraction: 0.5
        regeneration_suppression_fraction: 0.5
        recovery_ticks: 4
    factors:
      - path: {factor}
        kind: float
        lower: 0.0
        upper: 1.0
"""


def test_sensitivity_design_is_deterministic_ordered_and_seed_paired(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    path = tmp_path / "sensitivity.yml"
    path.write_text(_independent_spec(), encoding="utf-8")

    first = load_sensitivity_design(path)
    second = load_sensitivity_design(path)

    assert first.batch == second.batch
    assert len(first.batch.runs) == 8
    assert [run.run_id for run in first.batch.runs[:4]] == [
        "independent-p000-r00",
        "independent-p000-r01",
        "independent-p001-r00",
        "independent-p001-r01",
    ]
    assert [run.config.seed for run in first.batch.runs] == [11, 22] * 4
    for point in range(4):
        paired = first.batch.runs[point * 2 : point * 2 + 2]
        assert isinstance(paired[0].config.shock, IndependentShockConfig)
        assert isinstance(paired[1].config.shock, IndependentShockConfig)
        assert paired[0].config.shock.event_probability == paired[1].config.shock.event_probability


def test_sensitivity_design_preserves_exact_integer_grid_values(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    path = tmp_path / "sensitivity.yml"
    path.write_text(
        _independent_spec(factor="shock.recovery_ticks").replace(
            "kind: float\n        lower: 0.0\n        upper: 1.0",
            "kind: integer\n        lower: 1\n        upper: 10",
        ),
        encoding="utf-8",
    )

    design = load_sensitivity_design(path)

    shocks = [run.config.shock for run in design.batch.runs]
    assert all(isinstance(shock, IndependentShockConfig) for shock in shocks)
    values = {shock.recovery_ticks for shock in shocks if isinstance(shock, IndependentShockConfig)}
    assert values <= {1, 4, 7, 10}
    assert all(isinstance(value, int) for value in values)


@pytest.mark.parametrize(
    ("factor", "message"),
    [
        ("shock.missing", "does not exist"),
        ("shock.kind", "numeric scalar"),
        ("seed", "shock parameter"),
    ],
)
def test_sensitivity_design_rejects_unknown_categorical_or_nonscientific_paths(
    tmp_path: Path, factor: str, message: str
) -> None:
    _write_base(tmp_path / "base.yml")
    path = tmp_path / "sensitivity.yml"
    path.write_text(_independent_spec(factor=factor), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_sensitivity_design(path)


def test_sensitivity_design_rejects_duplicate_model_seeds_and_factor_paths(
    tmp_path: Path,
) -> None:
    _write_base(tmp_path / "base.yml")
    duplicate_seeds = tmp_path / "duplicate-seeds.yml"
    duplicate_seeds.write_text(
        _independent_spec().replace("model_seeds: [11, 22]", "model_seeds: [11, 11]"),
        encoding="utf-8",
    )
    duplicate_factors = tmp_path / "duplicate-factors.yml"
    duplicate_factors.write_text(
        _independent_spec().replace(
            "        upper: 1.0\n",
            "        upper: 1.0\n"
            "      - path: shock.event_probability\n"
            "        kind: float\n"
            "        lower: 0.0\n"
            "        upper: 1.0\n",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="model seeds must be unique"):
        load_sensitivity_design(duplicate_seeds)
    with pytest.raises(ValueError, match="factor paths must be unique"):
        load_sensitivity_design(duplicate_factors)


@pytest.mark.parametrize("model_seeds", ["[true]", "[1.5]", '["11"]', "[-1]"])
def test_sensitivity_design_requires_explicit_nonnegative_integer_model_seeds(
    tmp_path: Path, model_seeds: str
) -> None:
    _write_base(tmp_path / "base.yml")
    path = tmp_path / "sensitivity.yml"
    path.write_text(
        _independent_spec().replace("model_seeds: [11, 22]", f"model_seeds: {model_seeds}"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-negative integers"):
        load_sensitivity_design(path)


def test_sensitivity_design_fails_closed_when_run_budget_is_exceeded(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    path = tmp_path / "sensitivity.yml"
    path.write_text(_independent_spec(max_runs=7), encoding="utf-8")

    with pytest.raises(ValueError, match="exceeds max_runs"):
        load_sensitivity_design(path)


def test_sensitivity_design_rejects_scope_kind_that_differs_from_fixed_configuration(
    tmp_path: Path,
) -> None:
    _write_base(tmp_path / "base.yml")
    path = tmp_path / "sensitivity.yml"
    path.write_text(
        _independent_spec().replace(
            "kind: independent\n        event", "kind: system\n        event"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must activate independent shock"):
        load_sensitivity_design(path)


def test_checked_sensitivity_design_has_the_accepted_scope_coverage_and_run_budget() -> None:
    design = load_sensitivity_design(CHECKED_SENSITIVITY)

    assert [scope.kind for scope in design.specification.scopes] == [
        "independent",
        "correlated",
        "system",
    ]
    assert design.specification.model_seeds == (101, 202, 303)
    assert design.specification.max_runs == 600
    assert len(design.batch.runs) == 600
    counts = Counter(run.run_id.split("-", maxsplit=1)[0] for run in design.batch.runs)
    assert counts == {"independent": 180, "correlated": 240, "system": 180}
