from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def _dependency_name(specification: str) -> str:
    name = re.split(r"[<>=!~\[\s]", specification, maxsplit=1)[0]
    return name.lower().replace("_", "-")


def test_runtime_dependencies_exist_in_research_environment() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    environment = yaml.safe_load((ROOT / "environment.yml").read_text())

    runtime_names = {
        _dependency_name(specification)
        for specification in pyproject["project"]["dependencies"]
    }
    environment_names: set[str] = set()
    for dependency in environment["dependencies"]:
        if isinstance(dependency, str):
            environment_names.add(_dependency_name(dependency))
        elif "pip" in dependency:
            environment_names.update(_dependency_name(item) for item in dependency["pip"])

    assert runtime_names <= environment_names


def test_runtime_pins_supported_python_and_mesa_versions() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    environment = yaml.safe_load((ROOT / "environment.yml").read_text())

    assert pyproject["project"]["requires-python"] == ">=3.12,<3.13"
    assert "python=3.12" in environment["dependencies"]
    assert {"pip": ["mesa[rec]==3.5.1"]} in environment["dependencies"]
