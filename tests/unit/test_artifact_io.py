from pathlib import Path

import pytest

from social_cybernetics.artifact_io import read_json_object
from social_cybernetics.persistence import BundleValidationError


def test_json_object_reader_rejects_oversized_artifacts(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    path.write_text('{"large":true}\n', encoding="utf-8")

    with pytest.raises(BundleValidationError, match="exceeds"):
        read_json_object(path, max_bytes=2)


def test_json_object_reader_rejects_non_object_roots(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(BundleValidationError, match="must contain an object"):
        read_json_object(path, max_bytes=100)
