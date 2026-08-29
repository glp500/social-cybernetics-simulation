# Social Cybernetics Sugarscape Dashboard

## Canonical model documents

- [[model_specification|Scientific specification (ODD+D)]]
- [[architecture|Software architecture]]
- [[model_rules|Non-negotiable model rules]]
- [[assumptions|Assumptions and limitations]]
- [[research_roadmap|Dependency-ordered roadmap]]
- [[adr/README|Architecture decisions]]

## Version 0.1 implementation status

- [x] Environment
- [x] Agent state
- [x] Observation and belief boundaries
- [x] Action intents and simultaneous resolution
- [x] Metabolism and mortality
- [x] Mesa runtime
- [x] CLI and in-memory records
- [x] Debugging visualization
- [x] Verification ladder

Version 0.1 implementation and reconciliation completed on 2026-08-29. The exact evidence and known
limitations are recorded in [[experiment_log|the experiment log]].

Later communication, cognitive-tool, institution, and economic layers are specified in the roadmap,
not counted as unfinished version 0.1 work.

## Active version 0.2 phase

- [x] Explicit heterogeneous landscape configuration
- [x] Select shock semantics after reviewing alternatives and tradeoffs
- [x] Pure independent, correlated, and system shocks under the selected semantics
- [x] Runtime shock evidence and fixed-seed regressions
- [x] Provenance-rich fail-closed Parquet bundles
- [x] Complete streamed NetCDF spatial history
- [x] Deterministic batch execution
- [ ] Seeded sensitivity workflow
- [ ] Visualization and release reconciliation

Work is dependency-ordered in [[../tasks/plan|tasks/plan.md]] and tracked in
[[../tasks/todo|tasks/todo.md]]. The shock literature, design, implementation, and runtime gates are
complete; persistent Parquet and streamed NetCDF output are also implemented. Deterministic,
failure-isolated batch publication is complete; seeded sensitivity design is next.

## Active reading queue

```dataview
TABLE status, model_family, year, citekey
FROM "docs/literature/items"
WHERE type = "literature-note"
SORT status ASC, year DESC
```

## Mechanism backlog

```dataview
TABLE mechanisms, model_family, implementation_links
FROM "docs/literature/items"
WHERE type = "literature-note"
SORT file.mtime DESC
```

## Model decision notes

```dataview
LIST
FROM "docs/adr"
SORT file.mtime DESC
```
