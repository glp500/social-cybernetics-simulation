# Implementation Plan: Scientific Specification and Deterministic Core

## Architecture decisions

- Scientific specification and pure domain logic are independent of Mesa.
- Mesa 3.5.1 supplies discrete space, lifecycle, collection, and visual debugging.
- Configuration is validated at the boundary; unsupported model variants fail closed.
- Competition is simultaneous and all stochasticity derives from the model-owned seed.

## Dependency order

1. Canonical documentation and ADRs.
2. Environment, package metadata, CI, and validated baseline configuration.
3. Domain state and ecology.
4. Cognition, intents, gating, resolution, physiology, and metrics.
5. Mesa orchestration and records.
6. CLI, regression traces, and visual debugging.
7. Full quality gate and documentation reconciliation.

## Checkpoints

- **Foundation:** clean installation metadata, dependency-sync test, baseline config validates.
- **Domain:** unit/property tests prove equations, conservation, ordering independence, and mortality.
- **Runtime:** V0–V4 integration ladder and fixed-seed traces pass.
- **Complete:** CLI JSON is stable; SolaraViz is browser-verified; lint, types, coverage, lock, and docs
  reconciliation pass.

## Principal risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Mesa discrete-space/visualisation API evolution | contain it in one adapter and treat warnings as errors |
| hidden scheduler semantics | record and regression-test every completed stage |
| survivor bias | preserve original-cohort records after agent removal |
| duplicated dependency declarations | enforce a manifest synchronisation test |
| lost early design material | inventory and synthesise every approved source before deletion |

