from pathlib import Path

import pytest

from social_cybernetics.batch_config import (
    BatchSpecification,
    load_batch_specification,
    resolve_batch_specification,
)


def _write_base(path: Path) -> None:
    path.write_text(
        """schema_version: "0.2.0"
duration: 2
world:
  width: 3
  height: 2
agents:
  count: 2
  initial_positions:
    - [0, 0]
    - [1, 1]
shock:
  kind: none
""",
        encoding="utf-8",
    )


def test_batch_spec_resolves_ordered_recursive_overrides_relative_to_its_file(
    tmp_path: Path,
) -> None:
    _write_base(tmp_path / "base.yml")
    batch = tmp_path / "batch.yml"
    batch.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: control-seed-7
    overrides:
      seed: 7
      world:
        width: 4
      agents:
        initial_positions:
          - [3, 1]
          - [2, 0]
  - id: sham-seed-7
    overrides:
      seed: 7
      shock:
        kind: system
        event_probability: 1.0
        stock_loss_fraction: 0.0
        capacity_loss_fraction: 0.0
        regeneration_suppression_fraction: 0.0
        recovery_ticks: 2
""",
        encoding="utf-8",
    )

    resolved = load_batch_specification(batch)

    assert resolved.base_config_source == "base.yml"
    assert resolved.base_config_path == (tmp_path / "base.yml").resolve()
    assert [run.run_id for run in resolved.runs] == ["control-seed-7", "sham-seed-7"]
    assert [run.ordinal for run in resolved.runs] == [0, 1]
    assert [run.config.seed for run in resolved.runs] == [7, 7]
    assert resolved.runs[0].config.world.width == 4
    assert resolved.runs[0].config.world.height == 2
    assert resolved.runs[0].config.agents.initial_positions == ((3, 1), (2, 0))
    assert resolved.runs[1].config.shock.kind == "system"
    assert len(resolved.runs[0].configuration_sha256) == 64


def test_batch_spec_can_be_resolved_from_an_already_validated_contract(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    specification = BatchSpecification.model_validate(
        {
            "schema_version": "0.1.0",
            "base_config": "base.yml",
            "runs": [{"id": "generated-run", "overrides": {"seed": 9}}],
        }
    )

    resolved = resolve_batch_specification(specification, source_directory=tmp_path)

    assert resolved.base_config_path == (tmp_path / "base.yml").resolve()
    assert resolved.runs[0].run_id == "generated-run"
    assert resolved.runs[0].config.seed == 9


def test_batch_spec_requires_an_explicit_integer_seed_in_every_override(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    batch = tmp_path / "batch.yml"
    batch.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: inherited-seed
    overrides:
      duration: 1
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="explicit top-level integer seed"):
        load_batch_specification(batch)


@pytest.mark.parametrize("seed", [True, 1.5, "7"])
def test_batch_spec_rejects_noninteger_explicit_seeds(tmp_path: Path, seed: object) -> None:
    _write_base(tmp_path / "base.yml")
    batch = tmp_path / "batch.yml"
    encoded_seed = f'"{seed}"' if isinstance(seed, str) else str(seed).lower()
    batch.write_text(
        f"""schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: invalid-seed
    overrides:
      seed: {encoded_seed}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="explicit top-level integer seed"):
        load_batch_specification(batch)


def test_batch_spec_rejects_duplicate_or_unsafe_run_ids(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    duplicate = tmp_path / "duplicate.yml"
    duplicate.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: same-id
    overrides: {seed: 1}
  - id: same-id
    overrides: {seed: 2}
""",
        encoding="utf-8",
    )
    unsafe = tmp_path / "unsafe.yml"
    unsafe.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: ../outside
    overrides: {seed: 1}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="run IDs must be unique"):
        load_batch_specification(duplicate)
    with pytest.raises(ValueError, match="kebab-case"):
        load_batch_specification(unsafe)


def test_batch_spec_rejects_unknown_overrides_before_execution(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    batch = tmp_path / "batch.yml"
    batch.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
runs:
  - id: misspelled
    overrides:
      seed: 1
      duraton: 1
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duraton"):
        load_batch_specification(batch)


def test_batch_spec_requires_at_least_one_run_and_rejects_unknown_fields(tmp_path: Path) -> None:
    _write_base(tmp_path / "base.yml")
    empty = tmp_path / "empty.yml"
    empty.write_text(
        'schema_version: "0.1.0"\nbase_config: base.yml\nruns: []\n',
        encoding="utf-8",
    )
    unknown = tmp_path / "unknown.yml"
    unknown.write_text(
        """schema_version: "0.1.0"
base_config: base.yml
parallel: true
runs:
  - id: one
    overrides: {seed: 1}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="at least 1"):
        load_batch_specification(empty)
    with pytest.raises(ValueError, match="parallel"):
        load_batch_specification(unknown)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("- not-a-mapping\n", "root must be a mapping"),
        (
            'schema_version: "0.1.0"\nbase_config: base.yml\nruns:\n'
            "  - id: date-value\n    overrides: {seed: 1, duration: 2026-08-29}\n",
            "unsupported YAML value",
        ),
        (
            'schema_version: "0.1.0"\nbase_config: base.yml\nruns:\n'
            "  - id: nonfinite\n    overrides: {seed: 1, duration: .inf}\n",
            "finite numbers",
        ),
    ],
)
def test_batch_spec_rejects_nonportable_yaml_values(
    tmp_path: Path, content: str, message: str
) -> None:
    _write_base(tmp_path / "base.yml")
    batch = tmp_path / "batch.yml"
    batch.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_batch_specification(batch)


def test_batch_spec_enforces_its_input_size_limit(tmp_path: Path) -> None:
    batch = tmp_path / "batch.yml"
    batch.write_bytes(b" " * 1_048_577)

    with pytest.raises(ValueError, match="exceeds"):
        load_batch_specification(batch)
