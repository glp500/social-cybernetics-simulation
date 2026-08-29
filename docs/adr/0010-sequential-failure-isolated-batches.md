# ADR 0010: Publish sequential failure-isolated batch attempts

## Status

Accepted

## Date

2026-08-29

## Context

Version 0.2 needs repeatable multi-run experiments before sensitivity designs can depend on them. A
batch must preserve declared run order and complete configuration provenance, allow intentional seed
replication, and distinguish a failed model run from a corrupt aggregate output. Publishing only the
successful subset would hide attempted conditions; aborting after the first failure would make later
conditions depend on earlier success.

Batch output also inherits ADR 0008's fail-closed requirement. Directly creating a final batch
directory would expose partial experiments, while independently publishing each child to a final
location would leave no atomic statement of the complete attempt.

## Decision

A batch YAML uses schema `0.1.0`, names one base model configuration, and contains a non-empty ordered
list of unique, lowercase kebab-case run IDs. Each run supplies a recursive override mapping with an
explicit top-level non-negative integer `seed`; duplicate seed values are valid. Mappings merge
recursively, while scalars and lists replace their base values completely. The batch loader resolves
the base path relative to the batch file, normalizes the validated base configuration, applies every
override, and validates every resulting `SimulationConfig` before output staging or model execution.

Runs execute sequentially in declared order. Each successful run is a complete ADR 0008/0009 child
bundle. Invariant, runtime, and child-output failures become typed index records, leave no partial
child directory, and do not prevent later runs. Aggregate serialization or validation failure is not
a run failure: it aborts the entire unpublished batch.

The complete batch attempt is constructed in one hidden sibling staging directory. It contains the
normalized base and resolved-run provenance, an ordered JSON index, an equivalent explicitly typed
Parquet index, and child bundles only for successful runs. The batch manifest records status and
counts, artifact digests, and successful child-manifest digests. Validation checks JSON/Parquet
agreement, recursive override reconstruction, configuration hashes, child bundles, summaries, and
the exact directory set before atomic no-replace publication.

`scs batch --spec ... --output ...` exits 0 when all runs complete. It publishes the complete attempt
and exits 1 when one or more runs fail. An invalid batch or resolved model configuration exits 2 and
does not stage output. Existing destinations are refused before any model executes.

## Alternatives considered

### Stop on the first failed run

Rejected because declared later conditions would be silently unattempted and failure location would
change the evidence collected for the same batch specification.

### Publish only successful runs

Rejected because absence would be ambiguous between failure, filtering, and a condition that was
never attempted.

### Publish child bundles directly, then create an index

Rejected because a crash could expose an apparently usable subset without an authoritative batch
attempt.

### Allow inherited seeds

Rejected because a copied run block could accidentally duplicate the base seed without making that
scientific choice visible.

### Add process-level parallelism immediately

Deferred until sequential record ordering, failure behavior, and deterministic bundle equality are
the stable comparison contract.

## Consequences

- Batch attempts remain inspectable even when some runs fail.
- A published failed-run record has no corresponding child bundle.
- Batch memory is bounded by one active model and its in-memory immutable records, not by all runs.
- Full resolved configurations and their SHA-256 identities are retained in addition to overrides.
- Existing batch destinations and concurrent publication winners are never overwritten.
- Batch execution is intentionally sequential; performance-oriented parallelism is a later decision.
