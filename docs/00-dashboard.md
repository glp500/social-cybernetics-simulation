# Social Cybernetics Sugarscape Dashboard

## Canonical model documents

- [[model_specification|Scientific specification (ODD+D)]]
- [[architecture|Software architecture]]
- [[model_rules|Non-negotiable model rules]]
- [[assumptions|Assumptions and limitations]]
- [[research_roadmap|Dependency-ordered roadmap]]
- [[adr/README|Architecture decisions]]

## Version 0.1 implementation status

- [ ] Environment
- [ ] Agent state
- [ ] Observation and belief boundaries
- [ ] Action intents and simultaneous resolution
- [ ] Metabolism and mortality
- [ ] Mesa runtime
- [ ] CLI and in-memory records
- [ ] Debugging visualization
- [ ] Verification ladder

Later communication, cognitive-tool, institution, and economic layers are specified in the roadmap,
not counted as unfinished version 0.1 work.

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
