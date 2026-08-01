# Model Decisions

## 2026-08-01 — Start with metrics before agents

I implemented the Gini coefficient before building agents or the Mesa model. The reason is that the project depends on observing inequality, welfare, and collective outcomes. Starting with metrics makes later changes measurable instead of purely visual or intuitive.

Files added:
- `src/social_cybernetics/metrics.py`
- `tests/test_metrics.py`

Current status:
- Gini works for equal, unequal, empty, and invalid negative inputs.
