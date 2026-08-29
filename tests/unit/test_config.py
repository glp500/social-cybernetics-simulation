from pathlib import Path

import pytest
from pydantic import ValidationError

from social_cybernetics.config import DamageShockConfig, SimulationConfig, load_config


def test_baseline_configuration_is_canonical() -> None:
    config = load_config(Path("configs/baseline.yml"))

    assert config.seed == 42
    assert config.duration == 100
    assert (config.world.width, config.world.height) == (5, 5)
    assert config.world.torus is True
    assert config.resources.kind == "uniform"
    assert config.resources.capacity == 10
    assert config.resources.initial_stock == 10
    assert config.resources.regeneration_rate == 0.1
    assert config.agents.initial_positions == ((2, 2),)
    assert config.policy.kind == "literal_local"
    assert config.shock.kind == "none"
    assert config.gate.kind == "allow_all"


@pytest.mark.parametrize(
    ("section", "value"),
    [
        ("policy", {"kind": "q_learning"}),
        ("shock", {"kind": "local"}),
        ("gate", {"kind": "members_only"}),
    ],
)
def test_roadmap_variants_are_rejected(section: str, value: dict[str, str]) -> None:
    payload: dict[str, object] = {section: value}

    with pytest.raises(ValidationError):
        SimulationConfig.model_validate(payload)


def test_resource_stock_cannot_exceed_capacity() -> None:
    with pytest.raises(ValidationError, match="initial_stock"):
        SimulationConfig.model_validate(
            {"resources": {"kind": "uniform", "initial_stock": 11, "capacity": 10}}
        )


def test_legacy_v01_resource_mapping_defaults_to_uniform() -> None:
    config = SimulationConfig.model_validate(
        {"resources": {"capacity": 10, "initial_stock": 5, "regeneration_rate": 0.1}}
    )

    assert config.schema_version == "0.1.0"
    assert config.resources.kind == "uniform"
    assert config.resources.initial_stock == 5


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_all_scientific_floats_must_be_finite(value: float) -> None:
    with pytest.raises(ValidationError, match="finite number"):
        SimulationConfig.model_validate({"agents": {"initial_energy": value}})


def test_v02_explicit_landscape_is_validated_with_xy_orientation() -> None:
    config = load_config(Path("configs/ecology-v0.2.yml"))

    assert config.schema_version == "0.2.0"
    assert config.resources.kind == "explicit"
    assert config.resources.capacity == ((4.0, 8.0), (6.0, 10.0), (2.0, 12.0))
    assert config.resources.initial_stock == ((2.0, 8.0), (3.0, 5.0), (1.0, 6.0))


@pytest.mark.parametrize("kind", ["independent", "system"])
def test_v02_nonspreading_shocks_require_and_preserve_explicit_parameters(kind: str) -> None:
    shock = {
        "kind": kind,
        "event_probability": 0.25,
        "stock_loss_fraction": 0.0,
        "capacity_loss_fraction": 0.4,
        "regeneration_suppression_fraction": 1.0,
        "recovery_ticks": 3,
    }

    config = SimulationConfig.model_validate({"schema_version": "0.2.0", "shock": shock})

    assert isinstance(config.shock, DamageShockConfig)
    assert config.shock.kind == kind
    assert config.shock.event_probability == 0.25
    assert config.shock.stock_loss_fraction == 0.0
    assert config.shock.capacity_loss_fraction == 0.4
    assert config.shock.regeneration_suppression_fraction == 1.0
    assert config.shock.recovery_ticks == 3


def test_v02_correlated_shock_requires_explicit_propagation_parameters() -> None:
    shock = {
        "kind": "correlated",
        "event_probability": 0.0,
        "stock_loss_fraction": 0.0,
        "capacity_loss_fraction": 0.0,
        "regeneration_suppression_fraction": 0.0,
        "recovery_ticks": 1,
        "spread_probability": 1.0,
        "max_spread_ticks": 0,
    }

    config = SimulationConfig.model_validate({"schema_version": "0.2.0", "shock": shock})

    assert config.shock.kind == "correlated"
    assert config.shock.spread_probability == 1.0
    assert config.shock.max_spread_ticks == 0


@pytest.mark.parametrize(
    "shock",
    [
        {"kind": "independent"},
        {
            "kind": "correlated",
            "event_probability": 0.1,
            "stock_loss_fraction": 0.1,
            "capacity_loss_fraction": 0.1,
            "regeneration_suppression_fraction": 0.1,
            "recovery_ticks": 2,
        },
        {
            "kind": "system",
            "event_probability": 0.1,
            "stock_loss_fraction": 0.1,
            "capacity_loss_fraction": 0.1,
            "regeneration_suppression_fraction": 0.1,
            "recovery_ticks": 2,
            "spread_probability": 0.5,
        },
    ],
)
def test_enabled_shocks_reject_missing_or_inapplicable_fields(shock: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SimulationConfig.model_validate({"schema_version": "0.2.0", "shock": shock})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_probability", -0.1),
        ("event_probability", 1.1),
        ("stock_loss_fraction", 1.1),
        ("capacity_loss_fraction", -0.1),
        ("regeneration_suppression_fraction", float("nan")),
        ("recovery_ticks", 0),
    ],
)
def test_shock_common_parameters_are_range_checked(field: str, value: object) -> None:
    shock: dict[str, object] = {
        "kind": "system",
        "event_probability": 0.1,
        "stock_loss_fraction": 0.1,
        "capacity_loss_fraction": 0.1,
        "regeneration_suppression_fraction": 0.1,
        "recovery_ticks": 2,
    }
    shock[field] = value

    with pytest.raises(ValidationError):
        SimulationConfig.model_validate({"schema_version": "0.2.0", "shock": shock})


def test_enabled_shocks_require_schema_v02() -> None:
    shock = {
        "kind": "independent",
        "event_probability": 0.1,
        "stock_loss_fraction": 0.1,
        "capacity_loss_fraction": 0.1,
        "regeneration_suppression_fraction": 0.1,
        "recovery_ticks": 2,
    }

    with pytest.raises(ValidationError, match="schema version 0.2.0"):
        SimulationConfig.model_validate({"schema_version": "0.1.0", "shock": shock})


@pytest.mark.parametrize(
    ("version", "capacity", "stock", "message"),
    [
        ("0.1.0", [[1.0]], [[1.0]], "schema version 0.2.0"),
        ("0.2.0", [[1.0], [2.0]], [[1.0], [2.0]], "world shape"),
        ("0.2.0", [[1.0, 2.0]], [[1.0]], "same shape"),
        ("0.2.0", [[1.0, 2.0]], [[1.0, 3.0]], "cannot exceed capacity"),
        ("0.2.0", [[1.0, float("nan")]], [[1.0, 1.0]], "finite"),
    ],
)
def test_explicit_landscape_rejects_version_shape_and_value_errors(
    version: str,
    capacity: list[list[float]],
    stock: list[list[float]],
    message: str,
) -> None:
    payload = {
        "schema_version": version,
        "world": {"width": 1, "height": 2},
        "agents": {"count": 0, "initial_positions": []},
        "resources": {
            "kind": "explicit",
            "capacity": capacity,
            "initial_stock": stock,
            "regeneration_rate": 0.1,
        },
    }

    with pytest.raises(ValidationError, match=message):
        SimulationConfig.model_validate(payload)


def test_agent_positions_must_match_count_and_fit_world() -> None:
    with pytest.raises(ValidationError, match="initial_positions"):
        SimulationConfig.model_validate({"agents": {"count": 2, "initial_positions": [[0, 0]]}})

    with pytest.raises(ValidationError, match="outside"):
        SimulationConfig.model_validate({"agents": {"initial_positions": [[5, 0]]}})


def test_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SimulationConfig.model_validate({"surprise": True})


def test_config_file_must_be_a_mapping(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        load_config(path)


def test_config_file_has_a_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "too-large.yml"
    path.write_text("#" * 1_048_577, encoding="utf-8")

    with pytest.raises(ValueError, match="exceeds"):
        load_config(path)
