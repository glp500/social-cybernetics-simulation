# Dependency-Ordered Three-Study Roadmap

Calendar dates and old `v0.x` labels do not control this roadmap. A project becomes executable only
after its specification and literature gates are accepted, and it becomes complete only after all
seven evidence gates freeze.

## Programme sequence

```text
objective ecological opportunity
    -> private perception and adaptive action
        -> social information and bounded circulation
```

## Project 1 — Ecology, provisioning, and inequality

**Scientific status:** complete; all seven gates frozen.

**Implemented:** renewable homogeneous/explicit landscapes, literal local action, simultaneous
competition, metabolism/mortality, independent/correlated/system recoverable shocks, isolated RNG
streams, immutable transition/shock evidence, complete Parquet/NetCDF bundles, batches, Morris
sensitivity, artifact-only outcomes, canonical P1-A–E execution, and bounded interpretation.

**Frozen evidence:** 140/140 canonical runs and 600/600 sensitivity runs completed. Exact identities,
environment, commands, results, and limitations are in `docs/studies/project_1/validation.md` and
`docs/studies/project_1/interpretation.md`.

Project 1 mechanics must remain stable as the control for later projects. A change requires a new
study/schema version and reopening affected gates.

## Project 2 — Private perception and action

**Specification status:** complete.

**Implementation status:** not started; configuration remains fail-closed.

Dependency order:

1. freeze Project 1 control fixtures for every Project 2 comparison;
2. implement composed Project 2 agent state and sensing channel `C=(radius, noise, delay)`;
3. validate observation/belief histories and dedicated RNG streams;
4. implement fixed-policy information-access comparisons;
5. implement tabular Q-learning and matched fixed-policy controls;
6. publish Project 2 evidence without migrating Project 1 tables silently;
7. execute P2-A/P2-B experiments and freeze all seven gates.

Project 2 excludes reports, networks, trust, diffusion, circulation, institutions, exchange, and
demographics. Its exact mechanisms, experiments, analysis, boundaries, and implementation order are
specified under `docs/studies/project_2/`.

## Project 3 — Social information and bounded circulation

**Specification status:** complete.

**Implementation status:** not started; configuration remains fail-closed.

Dependency order:

1. select and freeze accepted Project 2 control regimes;
2. implement report and source-provenance contracts;
3. add trust feedback and separately controlled network rewiring;
4. add complete-profile capability diffusion with frozen-network/fixed-access controls;
5. verify relational accessibility, concentration, segregation, and diffusion measures;
6. add D0–D3 bounded circulation probes with conserved physical material and conserved credit;
7. execute the planned 330 runs and freeze all seven gates.

Project 3 credit is not money or debt. The study excludes institutions, governance, firms, wage
labour, capital ownership, general markets, and demographic reproduction. Its exact mechanisms,
experiments, accounting invariants, analysis, boundaries, and implementation order are specified
under `docs/studies/project_3/`.

## Protected extensions outside the active programme

The following ideas are intentionally neither Project 2 nor Project 3 backlog items:

- norm diffusion, costly enforcement, bounded institutions, or polycentric governance;
- stored asset ownership, firms, wage labour, prices, markets, loans, or debt ledgers;
- births, inheritance, demographic turnover, or intergenerational reproduction;
- productivity-changing physical tools;
- LLM-controlled agents;
- composite welfare or institutional-regime scores.

They require a new programme decision, their own ontology and mechanism evidence, and a fresh
specification. Archived source ideas and the reason for exclusion remain traceable in
`docs/refactor_crosswalk.md`; they do not silently widen current code.

## Seven gates per project

1. **Specification:** equations, ordering, state, edge cases, and exclusions are authoritative.
2. **Literature:** supporting evidence, counterevidence/boundaries, and project choices are explicit.
3. **Verification:** mechanism examples, invariants, properties, regressions, and architecture pass.
4. **Sensitivity:** influential controls and non-identifiable regions are documented.
5. **Experiment:** preregistered designs execute into validated immutable evidence.
6. **Analysis:** artifact-only raw outcomes, summaries, contrasts, and definedness are frozen.
7. **Interpretation:** claims, alternatives, missing mechanisms, and prohibited conclusions are frozen.

A successful software build does not complete a scientific project. Conversely, a complete future
specification does not make a mechanism executable.
