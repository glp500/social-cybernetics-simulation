from pathlib import Path

import pytest
from pydantic import ValidationError

from social_cybernetics.config import SimulationConfig, load_config


def test_baseline_configuration_is_canonical() -> None:
    config = load_config(Path("configs/baseline.yml"))

    assert config.seed == 42
    assert config.duration == 100
    assert (config.world.width, config.world.height) == (5, 5)
    assert config.world.torus is True
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
            {"resources": {"initial_stock": 11, "capacity": 10}}
        )


def test_agent_positions_must_match_count_and_fit_world() -> None:
    with pytest.raises(ValidationError, match="initial_positions"):
        SimulationConfig.model_validate(
            {"agents": {"count": 2, "initial_positions": [[0, 0]]}}
        )

    with pytest.raises(ValidationError, match="outside"):
        SimulationConfig.model_validate(
            {"agents": {"initial_positions": [[5, 0]]}}
        )


def test_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SimulationConfig.model_validate({"surprise": True})


def test_config_file_must_be_a_mapping(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        load_config(path)
