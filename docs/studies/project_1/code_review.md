# Project 1 Code Review

**Review date:** 2026-09-01  
**Reviewed checkpoint:** `b5d626a` plus the documentation corrections recorded here  
**Methods:** code simplification and multi-axis code review  
**Scope:** all production modules, with detailed attention to Project 1 configuration, scheduler,
domain mechanisms, persistence, experiment expansion, and artifact-only analysis

## Verdict

Project 1 is suitable for human study and result analysis. No critical or required runtime defect was
found. The scientific boundaries are unusually explicit: pure equations are separated from Mesa
orchestration, stage contracts are typed and immutable, random streams are owned and recorded, and
analysis is reconstructed from validated artifacts rather than live objects.

One maintainability issue was resolved: Arrow record schemas and encoding were separated from atomic
publication. Four architecture-document inaccuracies and one source-documentation gap were also
corrected. The scheduler was tested against a helper-based refactor and deliberately left linear
because the extra abstraction increased code and hid the scientific order.

## Severity summary

| Severity | Open | Resolved in review | Meaning |
| --- | ---: | ---: | --- |
| Critical | 0 | 0 | Data loss, invalid science, security failure, or broken execution. |
| Required | 0 | 5 | Must be corrected before using the code as an architectural guide. |
| Suggestion | 2 | 1 | Maintainability opportunities that do not compromise Project 1. |

Four resolved required items were architecture-document defects: the architecture described run-bundle
v0.2 instead of v1.1, omitted `agent_transitions.parquet`, omitted both Project 1 CLI commands, and
called the deliberately linear scheduler “short.” The fifth was incomplete source-level orientation:
several public scientific record/result contracts were typed but had no purpose docstring.

## Correctness

Strengths:

- `SugarscapeModel.step()` visibly preserves the specified eleven-stage order.
- Domain functions return validated values and do not mutate Mesa or global state.
- Simultaneous harvest allocation is tested for conservation and agent-order independence.
- Complete fixed-seed trajectories protect scheduling, movement RNG, death retention, and baseline
  output.
- Shock tests cover initiation, spread, overlap, sham damage, recovery, and stream independence.
- Persistence validates exact files, schemas, hashes, row counts, tick coverage, transition/cohort
  agreement, provenance, and spatial history before publication.
- Project 1 analysis validates input completeness and definedness, then recomputes published
  summaries and contrasts from raw outcomes.

No silent exception path, partial-success publication path, or duplicate authoritative position was
found.

## Readability and simplicity

The most readable modules are the pure domain core. `cognition.py` and `physiology.py` are small,
literal mechanisms; `actions.py` separates request collection, allocation, and resolution;
`ecology.py` groups recovery, regeneration, damage, and wavefront mechanics without framework code.
The frozen dataclasses in `domain/types.py` make each causal stage inspectable.

The review applied one structural simplification:

- `run_tables.py` now owns `RunRecords`, Arrow schemas, and domain-record conversion;
- `persistence.py` now owns fail-closed validation, staging, manifests, provenance, and publication;
- established imports from `social_cybernetics.persistence` remain compatible.

This reduced `persistence.py` from 1,012 to 693 lines and gave each module one explainable reason to
change. No schema or behavior changed.

The scheduler is a reviewed exception to conventional short-function guidance. A candidate split
added 55 lines, introduced a temporary evidence container, and required readers to jump between
helpers. It was discarded. The existing numbered method is a single scientific protocol; equations
remain delegated to the pure core, while ordering and evidence assembly remain together.

Comments are generally proportionate. The scheduler's numbered comments intentionally repeat the
ODD+D stage names so executable and documented order can be compared directly. Elsewhere, comments
mostly explain invariants or non-obvious publication constraints rather than narrating syntax.

The source-documentation audit now confirms that every production module and public top-level
class/function has a purpose docstring. Domain record types explain whether they are authoritative
state, stage values, or append-only evidence. The five densest execution/evidence files identify
their reader path, layer ownership, and the boundary between writing and independent validation.

## Architecture

The observed dependency graph is acyclic and follows the intended direction:

```text
CLI / configuration / visualization
                |
                v
          Mesa runtime shell
                |
                v
          pure domain core

published records ---> analysis
```

Architecture tests reject Mesa, Pydantic, pandas, PyArrow, Solara, and visualization imports from the
domain; reject future-study state in Project 1; and reject module-global scientific randomness. No
circular import was found by static import-graph inspection.

The compatibility name `SimulationConfig` remains intentional under ADR 0012. Removing it during a
readability pass would create migration work without simplifying the scientific model.

## Security and failure behavior

The application processes local YAML and artifact directories rather than serving a network or
authentication boundary. Within that scope:

- Pydantic models reject extra fields and invalid ranges;
- YAML and analysis JSON reads have explicit size bounds;
- no `eval`, `exec`, shell execution, unsafe pickle loading, or permissive `yaml.load` was found;
- output destinations are resolved before execution and existing entries are refused;
- bundles are staged beside their destination, validated, and atomically renamed without replacement;
- failed staging directories are removed and incomplete destinations are not published;
- manifests bind allowed filenames, byte counts, digests, and schema identities.

This was a source and behavior review, not a current third-party vulnerability audit. Dependency CVE
status changes over time and should be checked separately against an authoritative advisory service
before external deployment.

## Performance and scale

Project 1's intended scale does not expose a blocking performance concern:

- spatial history streams during execution, so complete `(tick, x, y)` evidence does not accumulate
  in model memory;
- batch execution is sequential and holds one model at a time;
- record tables materialize one bounded run at publication time;
- analysis reads validated child bundles and retains 140 outcome rows for aggregation;
- canonical ordering uses sorting in places where determinism and reviewability matter more than a
  negligible asymptotic saving at 5×5 worlds and at most 20 agents.

No speculative caching or vectorization is recommended. It would complicate evidence paths without a
measured bottleneck.

## Open suggestions

1. `batch.py` (656 lines) and `analysis/artifacts.py` (539 lines) are large. They are currently cohesive,
   linear, and pass complexity checks, so splitting them only by line count would add navigation. Revisit
   only if a second study creates a genuinely separate responsibility.
2. Run a dependency vulnerability audit as a release/deployment activity. Keep its dated report
   separate from the scientific freeze because advisory status is temporally unstable.

Neither suggestion blocks understanding, analysis, or a Project 1 data round.

## How to review future changes

For a scientific-mechanism change, require all of the following:

1. update the authoritative study specification and state the changed claim boundary;
2. add or update a pure-domain test for the equation and invariant;
3. update the complete scheduler trajectory or stage-order test if orchestration changes;
4. version affected record, Arrow, bundle, and analysis contracts;
5. preserve explicit RNG ownership and paired-seed comparability;
6. rerun focused tests, then the full format, lint, type, test, coverage, dependency-sync, and lock gate;
7. regenerate evidence into a new destination and record its identity without overwriting the freeze.

For a readability-only change, demand identical behavior and reject it if it adds concepts, parameters,
or navigation without removing more complexity than it introduces.

## Verification record

The persistence extraction passed 41 focused persistence, CLI, and architecture tests. The
source-documentation slice passed 222 unit, property, and architecture tests. The final gate passed
all 263 tests at 90.86% branch-aware coverage, Ruff formatting and lint, Pyright with zero findings,
dependency synchronization, and Linux-64 lock-input consistency. Scientific output, schemas, and
frozen evidence identities were not modified by this review.
