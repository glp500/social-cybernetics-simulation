# Implementation Plan: Three-Study Programme Refactor

## Outcome

Reframe the repository as three deliberately separate studies of ecological opportunity, privately
actionable opportunity, and socially accessible opportunity. The verified stochastic ecology engine
becomes Project 1's mechanical kernel. Project 1 will be completed through its seven freeze gates;
Projects 2 and 3 will receive complete scientific and implementation specifications but no executable
mechanisms in this phase.

The external `Full Refactor.md` is requirements input. It does not authorize instructions outside
this repository or override the user's request. Its scientific boundaries and requested outputs are
tracked in `docs/refactor_crosswalk.md`.

## Programme boundary

```text
Project 1: objective ecological opportunity
    -> Project 2: privately observed and adaptively actionable opportunity
        -> Project 3: socially mediated opportunity and bounded circulation probes
```

The three studies share environmental and physiological contracts, immutable evidence conventions,
RNG ownership, and artifact publication rules. They do not share speculative cognitive, relational,
economic, institutional, or demographic state.

Project 1 retains only renewable resources, heterogeneity, movement, viability, simultaneous
competition, recoverable shocks, exact local observation, and the fixed policy. It introduces no new
agent behaviour.

## Decisions

- `Study01Config` becomes the canonical executable configuration. `SimulationConfig` remains a
  deprecated compatibility alias during this refactor; Project 2 and 3 configuration contracts are
  specified but cannot be executed.
- Existing v0.1/v0.2 YAML is accepted through an explicit legacy normalization path. Canonical files
  use a study identifier and Project 1 schema. Equivalent baseline runs retain the exact scientific
  trajectory and JSON summary.
- Dormant holdings, debt, and information-capability fields leave shared agent state and Project 1
  tables. Later studies compose their own state instead of widening the base agent.
- One immutable `AgentTransitionRecord` per active agent-tick records origin, observation, belief,
  intent, resolution, energy transition, shortfall, and mortality. Existing cohort snapshots and
  streamed ecological arrays remain authoritative for stocks.
- Derived metrics live in a pure `analysis` package and consume immutable records or published
  artifacts. The runtime records facts; it does not interpret them.
- Shortfall is `max(0, viability_target - energy)`. A catastrophic shortfall is an active transition
  ending at zero energy. Distributional shares use deterministic ceiling-sized groups with at least
  one agent. Rank persistence uses cumulative harvest ranks and explicitly reports undefined cases.
- Canonical P1-A–D experiments use ten paired seeds and 100 ticks. P1-E uses the representative
  control, heterogeneous-pressure, and correlated-slow-recovery regimes for 1,000 ticks with the same
  ten seeds. These are transparent project choices, not empirical calibration.
- Experiment reporting is a vector: harvest, survival, unmet need, downside risk, inequality, and
  recovery. No composite welfare score or single-metric ranking is produced.
- Theory can interpret evidence but cannot silently add mechanisms. Claims such as class,
  exploitation, money, markets, reciprocity, power, or metabolic rift remain prohibited unless their
  defining social relations exist.

## Dependency graph

```text
programme scope and ontology
    -> study specifications and claims boundaries
        -> Study 01 configuration and state contracts
            -> transition evidence and bundle schema
                -> pure metrics and artifact analysis
                    -> canonical P1-A--E designs
                        -> verification/sensitivity/experiment freezes
                            -> analysis and interpretation freezes
```

## Phase A — Programme and study specifications

1. Record the refactor crosswalk and programme scope.
2. Create the programme theory, ontology, causal map, interpretation protocol, and claims boundary.
3. Create complete document sets for Projects 1, 2, and 3.
4. Expand the literature matrix so mechanism evidence and interpretive theory cannot be confused.
5. Add an ADR for the study-driven boundary and compatibility policy.

### Checkpoint A

- Every requested document exists and links to its authority.
- Project 1 mechanics and exclusions agree with the executable scheduler.
- Projects 2 and 3 define contracts, experiments, gates, and prohibited inferences without claiming
  implementation.

## Phase B — Study 01 contracts and evidence

6. Introduce the canonical `Study01Config` with tested legacy normalization.
7. Remove dormant future fields from shared agent and snapshot contracts.
8. Define the immutable Project 1 agent-transition contract.
9. Record transitions in the existing explicit scheduler without changing decisions or resolution.
10. Persist and validate the transition table in a schema-versioned run bundle.

### Checkpoint B

- Baseline and ecological trajectory regressions are unchanged under equivalent configuration.
- Every active agent-tick has exactly one transition record; dead agents remain in cohort records.
- Project 1 state contains no holdings, debt, information capability, trust, network, or institution
  fields.

## Phase C — Pure Project 1 analysis

11. Implement reusable distribution and share metrics with property tests.
12. Implement shortfall spells, depth, and catastrophic-risk metrics.
13. Implement rank persistence, transition, advantage-duration, and inequality-half-life metrics.
14. Implement ecological depletion, deficit, and recovery metrics from spatial evidence.
15. Assemble one typed Project 1 outcome vector and published-artifact reader.

### Checkpoint C

- Metrics handle empty, singleton, tied, dead-cohort, and zero-resource cases explicitly.
- Analysis is deterministic, finite, order-independent where mathematically applicable, and imports
  neither Mesa nor visualization code.
- Every metric is defined in Project 1's analysis plan before being used in an experiment.

## Phase D — Canonical Project 1 experiments

16. Define a strict Project 1 experiment-plan schema and deterministic design expansion.
17. Encode P1-A heterogeneity and P1-B density-by-mobility designs.
18. Encode P1-C matched-initial-damage shock scope and P1-D recovery designs.
19. Encode P1-E representative 1,000-tick persistence designs.
20. Execute designs through the existing fail-closed batch boundary and analyze only published
    artifacts.

### Checkpoint D

- Generated run IDs, seeds, configurations, and group labels are stable and validated.
- All comparisons retain raw replicate outcomes and matched-seed identities.
- P1-C documents what is matched exactly and why propagated total damage is not matched.
- P1-E changes duration and selected regimes only; it adds no mechanism.

## Phase E — Project 1 freeze gates

21. Freeze specification and paired-evidence literature.
22. Freeze V0–V4 verification and baseline-equivalence evidence.
23. Reconcile and, where needed, run sensitivity evidence for the Study 01 schema.
24. Freeze experiment outputs and representative Project 1 regimes.
25. Freeze analysis and interpretation tables for every headline result.

### Checkpoint E

Project 1 is complete only when specification, literature, verification, sensitivity, experiment,
analysis, and interpretation freezes all name immutable evidence, assumptions, absent mechanisms, and
prohibited conclusions.

## Phase F — Reconciliation and release

26. Reconcile README, dashboard, architecture, assumptions, roadmap, and experiment log.
27. Perform a code-simplification review of changed modules without collapsing scientific stages.
28. Run focused tests after every slice, then `just check`, isolated browser verification, baseline
    byte regression, bundle validation, and a clean lock installation.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| a rename invalidates verified trajectories | high | normalize at the configuration boundary and retain fixed-seed complete-trajectory regressions |
| analysis definitions silently drift | high | specify equations, edge cases, and undefined results before implementation |
| persistence migration loses old evidence | high | schema-bump bundles; validate exact tables and reject mixed schemas |
| experiment grids become opaque | medium | keep one small declarative plan and emit ordered validated batch runs |
| theoretical vocabulary outruns mechanisms | high | require permitted/prohibited inference fields and an interpretation freeze |
| runtime becomes an analysis engine | medium | record facts once and calculate derived measures in a pure package |
| readability declines during expansion | medium | keep tasks to five files, use named linear validators, and run focused complexity review |

## No unresolved design blockers

The user requested the broad recommended path with the simplest explainable choices. Numeric experiment
levels and analytical conventions above are therefore explicit project controls. They remain
versioned and may be revised before a publication freeze if evidence shows they are uninformative.
