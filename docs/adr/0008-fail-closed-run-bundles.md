# ADR 0008: Publish validated run bundles atomically without overwrite

## Status

Accepted

## Date

2026-08-29

## Context

Version 0.2 needs persistent scientific records that can be distinguished from partial or corrupt
output. Directly writing the requested destination would expose incomplete files to analysis and
make a failed run look publishable. An existence check followed by an ordinary rename is also
insufficient: another process can create the destination between those operations, and POSIX rename
may replace an existing empty directory.

The persistent boundary must preserve the JSON-only CLI behavior when no destination is requested,
retain normalized immutable records rather than Mesa objects, and fail closed for every collision.

## Decision

An opt-in run bundle contains canonical JSON for normalized configuration, provenance, and the run
summary, plus six schema-versioned Parquet tables: model, cohort, agent events, shock-event snapshots,
shock exposures, and cell-damage applications. The manifest records the model and bundle schema
versions, seed, completed ticks, exact file set, byte counts, SHA-256 digests, table paths, table
schema versions, and row counts.

Build each bundle in a uniquely named sibling staging directory. Before publication, validate the
exact file set, JSON contracts, cross-artifact seed and tick agreement, software and RNG provenance,
digests, Arrow schemas, row counts, and Parquet value round trips. Publish with Linux
`renameat2(RENAME_NOREPLACE)`, which atomically renames only if the destination is still absent. If
that primitive is unavailable, publication fails rather than weakening the contract. Any build or
validation failure removes its staging directory. Existing files, directories, and broken symlinks
are refused and never overwritten.

The permanent RNG registry is part of provenance: policy `(1,)`, shock initiation `(2, 1)`, shock
location `(2, 2)`, and shock transmission `(2, 3)`. Required runtime package versions must be
present. Optional xarray and NetCDF4 versions are recorded when installed and as null otherwise.

NetCDF spatial history is not included until its temporal sampling and memory/streaming semantics are
selected. This does not weaken the Parquet bundle, which already persists all currently defined
immutable model, cohort, agent, shock, exposure, and damage records.

## Alternatives considered

### Write directly into the final destination

Rejected because interrupted writes would be indistinguishable from complete runs.

### Overwrite or add an implicit numeric suffix

Rejected because either behavior can hide an experiment-identity mistake. Callers must choose a new
destination explicitly.

### Check existence and use ordinary `os.rename`

Rejected because the check has a race and an ordinary rename can replace an existing empty directory
on the target platform.

### Stage in a system temporary directory

Rejected because a cross-filesystem rename is not atomic. The staging directory must be a sibling of
the destination.

### Persist framework objects or pandas indexes

Rejected because those formats would couple scientific evidence to Mesa or an analysis library. The
boundary consumes immutable domain records and emits explicit Arrow schemas.

## Consequences

- Readers see either no destination or a validated complete directory at publication time.
- Concurrent writers cannot overwrite the winner.
- The initial atomic publication implementation is Linux-specific and fails closed elsewhere.
- A process killed outside normal exception handling can leave a hidden sibling staging directory;
  it cannot leave a falsely published bundle.
- The manifest validates integrity, not authenticity; it is not a cryptographic signature.
- Remote object stores require a separate publication protocol.
- Spatial NetCDF design remains an explicit Phase D checkpoint.
