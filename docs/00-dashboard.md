# Social Cybernetics Sugarscape Dashboard

## Programme status

| Study | Specification | Implementation | Freeze gates |
| --- | --- | --- | --- |
| [[studies/project_1/specification|Project 1 — objective ecological opportunity]] | complete | complete | 7/7 frozen |
| [[studies/project_2/specification|Project 2 — private perception and action]] | complete | not started | 0/7 |
| [[studies/project_3/specification|Project 3 — social information and circulation]] | complete | not started | 0/7 |

Project 1 completed on 2026-08-31 with 140/140 canonical runs, 600/600 Morris sensitivity runs,
artifact-only analysis, bounded interpretation, 259 passing tests at 90.85% coverage, clean-lock and
browser verification. Exact evidence identities are in [[studies/project_1/validation]].

Projects 2 and 3 are deliberately fail-closed. Their complete documents define mechanisms,
experiments, measures, exclusions, and implementation order without claiming executable behavior.

## Canonical authority

- [[programme/overview|Programme overview]]
- [[model_specification|Canonical scientific specification (ODD+D)]]
- [[programme/shared_ontology|Shared ontology]]
- [[programme/causal_map|Cross-study causal map]]
- [[programme/interpretation_protocol|Interpretation protocol]]
- [[programme/claims_and_limits|Programme claims and limits]]
- [[architecture|Software architecture]]
- [[research_roadmap|Dependency-ordered three-study roadmap]]
- [[adr/README|Architecture decisions]]
- [[experiment_log|Experiment log]]

## Project 1 evidence

- [[studies/project_1/specification|Specification]]
- [[studies/project_1/theory|Theory]]
- [[studies/project_1/hypotheses|Hypotheses]]
- [[studies/project_1/experiments|Experiments]]
- [[studies/project_1/validation|Seven-gate validation register]]
- [[studies/project_1/analysis_plan|Analysis plan]]
- [[studies/project_1/interpretation|Frozen result interpretation]]
- [[studies/project_1/claims_and_limits|Claims and limits]]

## Active implementation queue

Project 1 has no open implementation tasks. Before Project 2 code begins, reopen its specification and
literature gates explicitly; do not add dormant Project 2/3 state to the shared Project 1 core.

- [[../tasks/plan|Implementation plan]]
- [[../tasks/todo|Verified task checklist]]
- [[refactor_crosswalk|Full-refactor requirements crosswalk]]

## Active reading queue

```dataview
TABLE status, model_family, year, citekey
FROM "docs/literature/items"
WHERE type = "literature-note"
SORT status ASC, year DESC
```

## Architecture decisions

```dataview
LIST
FROM "docs/adr"
SORT file.mtime DESC
```
