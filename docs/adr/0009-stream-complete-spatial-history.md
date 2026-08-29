# ADR 0009: Stream complete spatial history into staged run bundles

## Status

Accepted

## Date

2026-08-29

## Context

ADR 0008 established validated sibling staging and atomic no-overwrite publication, but deliberately
left NetCDF temporal sampling and memory behavior unresolved. Sparse shock and damage records explain
discrete disturbance events; they do not reconstruct ordinary regeneration, temporary capacity and
regeneration trajectories, or spatial inequality on every tick.

Buffering every ecological array until a run ends would scale in memory as
`ticks × width × height × variables`, competing directly with batch and sensitivity workflows. Initial
and final snapshots would be cheaper but would discard the recovery trajectory that version 0.2 is
designed to study.

## Decision

Every persistent bundle uses schema `scs-run-bundle/v0.2.0` and requires `spatial.nc` with spatial
schema `scs-spatial-history/v0.1.0`. The artifact uses dimensions `(tick, x, y)`, preserving the
documented NumPy/Mesa coordinate order.

Record tick zero immediately before the first transition and one snapshot after every completed
measurement. Stream these dynamic variables as each snapshot occurs:

- resource stock;
- effective capacity;
- effective regeneration;
- recovery ticks remaining.

Record baseline capacity and baseline regeneration once as static `(x, y)` variables. Coordinates are
canonical consecutive integers. Floating values use float64 and recovery/tick coordinates use int64.
Dynamic variables use one-tick, spatially bounded compressed chunks and the writer synchronizes after
each snapshot, keeping Python memory independent of run duration.

The persistence layer owns the NetCDF writer and its staging directory. Mesa accepts only a typed
synchronous snapshot-sink protocol and does not import persistence or NetCDF. Tick-zero emission is
deferred until `run()` or the first `step()` so a validated pre-run verification fixture can still
become the authoritative initial state.

The stream closes before manifest construction. Bundle validation checks its digest, schema and model
schema versions, unlimited tick dimension, exact variable/dimension/dtype contracts, canonical
coordinates, snapshot count `completed_ticks + 1`, and static baselines against normalized
configuration. Only then does ADR 0008's atomic no-replace publication occur. Any model, stream,
serialization, validation, or collision failure removes the unpublished staging directory.

NetCDF4 becomes a runtime dependency. Xarray remains a research/analysis dependency and is not
imported by the writer or scientific core.

## Alternatives considered

### Buffer complete history in memory

Rejected because memory would grow with duration and undermine batch scalability.

### Persist only initial and final spatial state

Rejected because intermediate shock propagation, regeneration, recovery, and spatial inequality
could not be reconstructed.

### Defer NetCDF until batch execution

Rejected because batch indexes should point to a stable complete run-bundle contract rather than
requiring a later bundle migration.

### Let Mesa write NetCDF directly

Rejected because it would couple runtime orchestration to a persistence library and weaken the
functional-core/runtime-shell boundary.

## Consequences

- Persistent runs retain complete ecological trajectories with bounded Python memory.
- Output incurs compression and synchronization I/O once per tick.
- A persistent run opens its staging directory before model construction instead of serializing only
  after execution.
- The JSON-only no-output path remains unchanged and creates no spatial writer.
- Bundle schema v0.2 is intentionally incompatible with the earlier pre-spatial draft schema v0.1.
- ADR 0008 remains authoritative for atomic publication; this ADR supersedes only its deferred
  bundle-content decision.
