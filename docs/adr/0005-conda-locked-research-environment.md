# ADR 0005: Use a Conda-locked Research Environment

## Status

Accepted — 2026-08-28

## Context

Scientific runs need reproducible Python and compiled numerical dependencies. The project also needs
valid installable-package metadata.

## Decision

Use Python 3.12. Declare runtime requirements in `pyproject.toml`, the complete research/development
environment in `environment.yml`, and lock Linux-64 with conda-lock. An automated check compares the
overlapping direct dependency names to prevent drift.

## Alternatives considered

- **Conda metadata only:** rejected because editable package installation would omit runtime needs.
- **Pyproject/uv only:** valid technically, but not the selected research-environment workflow.

## Consequences

Two human-readable manifests exist and require a synchronisation test. The generated lockfile is
committed and never hand-edited. CI installs from the lock rather than resolving afresh.

