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
- `shock.kind: none`;
- `gate.kind: allow_all`.

Version 0.1 rejects other variant names rather than silently falling back. Dimensions, duration, seed,
stock, capacity, rates, costs, efficiency, thresholds, positions, and agent counts are range-checked.

## Public interfaces

```text
scs validate --config configs/baseline.yml
scs run --config configs/baseline.yml
just viz
```

`scs run` writes only a deterministic JSON summary to standard output. Invalid configuration exits 2;
scientific invariant or runtime failure exits 1. Full run bundles are deliberately deferred.

The compatibility import `social_cybernetics.metrics.gini` remains available.

## Measurement

The runtime records tick 0 and every completed transition. Cohort records include living and dead
members. Event records describe movement, harvest, and death. A run summary is derived from records,
not from transient UI state.

## Visualisation

SolaraViz is a debugging adapter. It reads the same property layers and records as the CLI and cannot
invoke alternative model transitions. It shows resource intensity, living agents, energy, total
resources, alive population, and cohort mean energy. It is not an analytical evidence pipeline.

## Package layout

```text
src/social_cybernetics/
  config.py                 validated external configuration
  cli.py                    command-line boundary
  metrics.py                pure public metrics
  domain/                   framework-independent state and mechanisms
  runtime/mesa/             Mesa model, agents, collection, and visualisation
```

Future modules are added only when their version is implemented; the repository does not contain
empty speculative packages.

