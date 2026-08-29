"""Canonical JSON and digest helpers shared by scientific output bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from social_cybernetics.persistence_errors import BundleValidationError


def canonical_json_bytes(payload: object) -> bytes:
    """Encode one canonical JSON document with its required trailing newline."""

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return f"{serialized}\n".encode()


def write_json(path: Path, payload: object) -> None:
    """Write canonical JSON bytes to a staged artifact."""

    path.write_bytes(canonical_json_bytes(payload))


def sha256_file(path: Path) -> str:
    """Return the streaming SHA-256 digest of one artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_payload_sha256(payload: object) -> str:
    """Identify a JSON-compatible value independent of whitespace or key order."""

    return hashlib.sha256(canonical_json_bytes(payload)[:-1]).hexdigest()


def file_descriptor(path: Path, *, schema_version: str) -> dict[str, object]:
    """Describe one staged artifact for a bundle manifest."""

    return {
        "schema_version": schema_version,
        "byte_count": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def read_json_object(path: Path, *, max_bytes: int) -> dict[str, Any]:
    """Read a size-bounded JSON object or raise the shared validation error."""

    try:
        if path.stat().st_size > max_bytes:
            raise BundleValidationError(f"JSON artifact exceeds {max_bytes} bytes: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BundleValidationError(f"invalid JSON artifact: {path.name}") from error
    if not isinstance(payload, dict):
        raise BundleValidationError(f"JSON artifact must contain an object: {path.name}")
    return payload
