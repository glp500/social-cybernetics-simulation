# Social Cybernetics Sugarscape Dashboard

## Current implementation status

- [ ] Environment
- [ ] Agent state
- [ ] Movement policy
- [ ] Mesa wrapper
- [ ] Baseline experiment
- [ ] Visualization
- [ ] Communication layer
- [ ] Cognitive tool layer
- [ ] Particle/statistical-physics toy model

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
FROM "docs/implementation"
SORT file.mtime DESC
```
