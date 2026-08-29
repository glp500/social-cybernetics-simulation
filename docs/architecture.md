# Software Architecture

## Boundary

The scientific specification is independent of any simulation framework. Executable code follows a
functional-core/runtime-shell design:

```text
CLI / configuration / visualisation
                 |
                 v
          Mesa runtime adapter
                 |
                 v
           pure domain core

analysis <--- immutable records
```

Dependencies only point downward. The domain may import the Python standard library and NumPy. It may
not import Mesa, Pydantic, pandas, PyArrow, Solara, or presentation code.

## Authoritative state

- Typed domain records own non-spatial agent state.
- Mesa cells own position; immutable `AgentSnapshot` values combine cell coordinates and domain state
  at stage boundaries. There is no second mutable location field.
- Mesa property layers own environmental arrays. Pure ecology functions accept arrays and return
  validated arrays; they do not know about Mesa layers.
- Dead-agent state moves to a cohort archive before removal from Mesa activation.

## Contracts

The domain defines:

- `AgentState` and `AgentSnapshot`;
- `CellObservation`, `Observation`, and `BeliefState`;
- `ActionIntent`, `GateDecision`, and `ActionResolution`;
- model, cohort, and event records;
- protocols for observation, belief update, decision policy, institutional gate, and physical
  resolution.

Initial implementations are direct observation, copied belief, literal local decision policy,
allow-all gating, simultaneous harvest allocation, and unrestricted movement.

## Runtime orchestration

The Mesa model owns the run seed and all random generators. Its `step()` method is intentionally a
short, readable transcription of the documented scheduler. Agent methods do not mutate environment
layers or other agents; they produce observations, beliefs, and intents for model-level resolution.

Mesa-specific APIs are contained under `social_cybernetics.runtime.mesa`. A future Mesa migration must
not change domain contracts or scientific equations.

## Configuration boundary

YAML is untrusted input. Pydantic validates it before model construction. Configuration uses
discriminated variants:

- `policy.kind: literal_local`;
- `resources.kind: uniform | explicit` in version 0.2;
- `shock.kind: none | independent | correlated | system` in version 0.2;
- `gate.kind: allow_all`.

Schema version 0.1 continues to accept only the uniform/no-shock control. Schema version 0.2 accepts
only implemented ecological variants; version/variant mismatches and unknown names fail closed.
Dimensions, matrix shapes, duration, seed, stocks, capacities, rates, probabilities, damage
fractions, recovery/spread ticks, costs, efficiency, thresholds, positions, and agent counts are
range-checked. Shock-enabled variants require every applicable scientific field explicitly.

Landscape configuration becomes validated NumPy arrays at the runtime boundary. Baseline capacity
and regeneration arrays remain immutable scientific inputs; runtime property layers own stock and
effective ecological arrays. Pure domain functions advance recovery, signed relaxation, event
propagation, and simultaneous damage. Mesa orders those functions and stores their immutable outputs;
it does not contain their equations.

The runtime derives stable NumPy generators with `SeedSequence(run_seed, spawn_key=...)`. Permanent
keys are policy `(1,)`, shock initiation `(2, 1)`, shock location `(2, 2)`, and shock transmission
`(2, 3)`. The registry and bit-generator name are provenance. Random draws never use module-global
state.

Active correlated events are runtime orchestration state composed only of domain values. Analysis
consumes append-only `ShockEventSnapshot`, `EventCellExposure`, and `CellDamageApplication` records.
Multiple event hits are grouped by cell before a pure damage transition, so record iteration order
cannot change physical state.

## Public interfaces

```text
scs validate --config configs/baseline.yml
scs run --config configs/baseline.yml
scs run --config configs/baseline.yml --output results/run-001
scs batch --spec configs/batch-v0.2.yml --output results/batch-v0.2
scs sensitivity --spec configs/sensitivity-v0.2.yml --output results/sensitivity-v0.2
just viz
```

`scs run` writes a deterministic JSON summary to standard output. Invalid configuration exits 2;
scientific invariant, runtime, or persistent-output failure exits 1. `--output` adds an opt-in run
bundle without changing standard output or the no-output path. The destination's parent must exist;
any existing filesystem entry is refused before model execution.

`scs batch` first validates the batch schema, base configuration, recursive overrides, and every
resolved run configuration. Invalid input exits 2. It then executes in declared order and stages the
entire attempt beside an absent destination. Individual invariant, runtime, or child-output failures
are retained in the aggregate index without a partial child directory; later runs continue. The
validated batch is published even with run failures and the command exits 1. Aggregate-output failure
publishes nothing and also exits 1.

`scs sensitivity` validates a seeded Morris specification, resolves every numeric factor path against
an active shock configuration, generates stable point/replicate IDs, and validates every realized
configuration before execution. Invalid design input exits 2. The command then calls the same batch
executor, so ordering, failure isolation, child bundles, aggregate indexes, and atomic publication do
not have a sensitivity-specific implementation.

## Persistent-output boundary

`social_cybernetics.persistence` consumes validated configuration, the deterministic JSON summary,
immutable domain records, and the runtime's recorded RNG registry. It does not depend on Mesa or
analysis data frames. Run-bundle schema v0.2 has this exact layout:

```text
run-001/
  manifest.json
  configuration.json
  provenance.json
  summary.json
  spatial.nc
  tables/
    model.parquet
    cohort.parquet
    agent_events.parquet
    shock_events.parquet
    shock_exposures.parquet
    cell_damage.parquet
```

Every table has an explicit Arrow schema and embedded schema version, including when it has zero
rows. `spatial.nc` uses `(tick, x, y)` dimensions. It streams stock, effective capacity, effective
regeneration, and recovery remaining at tick zero and after every completed measurement; baseline
capacity and regeneration are static `(x, y)` variables. The manifest fixes the allowed files and
records byte counts, SHA-256 digests, schema versions, table row counts, and spatial snapshot count.
Validation also checks cross-artifact seed and completed-tick agreement and the exact permanent RNG
registry.

Publication follows ADR 0008: construct and validate in a sibling staging directory, then use an
atomic no-replace rename. Collisions, unsupported atomic primitives, serialization errors, and
validation failures leave the requested destination unpublished. A persistence-owned
`RunBundleSession` opens the spatial stream inside staging before model construction. Mesa sees only a
typed synchronous snapshot sink, preserving the downward dependency direction.

`social_cybernetics.batch_config` owns the external batch contract and pure recursive merge at the
application boundary. `social_cybernetics.batch` executes one model at a time and composes existing run
bundles; neither module enters the domain core. A batch bundle has this layout:

```text
batch-v0.2/
  batch_manifest.json
  batch_specification.json
  runs.json
  runs.parquet
  runs/
    <successful-run-id>/
      <complete run bundle>
```

The normalized batch artifact retains the base configuration, ordered explicit overrides, resolved
configurations, and their canonical SHA-256 identities. JSON and Parquet indexes contain one row per
attempt in declared order and retain raw summary measures. Failed rows contain a typed error and no
bundle path. The outer directory uses the same sibling-stage and atomic no-replace primitive as a run
bundle; validation recursively verifies successful children before publication.

The compatibility import `social_cybernetics.metrics.gini` remains available.

## Measurement

The runtime records tick 0 and every completed transition. Cohort records include living and dead
members. Agent event records describe movement, harvest, and death; ecological records describe
shock-event snapshots, attempted/successful exposure, and authoritative cell damage. A run summary is
derived from records, not from transient UI state.

## Visualisation

SolaraViz is a debugging adapter. It reads the same property layers and records as the CLI and cannot
invoke alternative model transitions. It shows resource intensity, living agents, energy, total
resources, alive population, and cohort mean energy. It is not an analytical evidence pipeline.

## Package layout

```text
src/social_cybernetics/
  config.py                 validated external configuration
  batch_config.py           ordered batch schema, recursive overrides, and resolution
  batch.py                  sequential execution, aggregate indexes, and batch validation
  sensitivity.py            Morris specification, factor validation, and batch generation
  cli.py                    command-line boundary
  metrics.py                pure public metrics
  persistence.py            run-bundle staging, manifests, Parquet, and atomic publication
  persistence_errors.py     shared fail-closed output errors
  spatial_output.py         incremental NetCDF spatial writer and validator
  domain/                   framework-independent state and mechanisms
  runtime/mesa/             Mesa model, agents, collection, and visualisation
```

Future modules are added only when their version is implemented; the repository does not contain
empty speculative packages.
