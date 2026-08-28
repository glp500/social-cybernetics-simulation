# Deterministic Core Task List

- [x] Write canonical scientific specification and architecture documents.
  - Acceptance: ODD+D concerns, assumptions, roadmap, and non-negotiable rules are explicit.
  - Verify: every approved design-source concept is mapped in `docs/source_synthesis.md`.
- [x] Record architecture decisions.
  - Acceptance: model/runtime, Mesa, schedule, RNG, environment, and competition choices have ADRs.
  - Verify: ADR index links resolve.
- [ ] Reconcile environment and package tooling.
  - Acceptance: Python/Mesa pins, full research environment, CLI entry points, Just recipes, and CI agree.
  - Verify: dependency-sync and lockfile checks pass.
- [ ] Implement validated configuration.
  - Acceptance: baseline validates and malformed/unsupported variants fail.
  - Verify: focused configuration tests and `scs validate` pass.
- [ ] Implement pure ecology and state contracts.
  - Acceptance: regeneration bounds/convergence and immutable stage records are proven.
  - Verify: unit and Hypothesis tests pass.
- [ ] Implement cognition, action, gate, and physical resolution.
  - Acceptance: agents cannot bypass interfaces; scarce harvest is proportional and order-independent.
  - Verify: unit, property, and architecture tests pass.
- [ ] Implement metabolism, mortality, records, and metrics.
  - Acceptance: energy accounting is finite; dead agents remain in cohort/event records.
  - Verify: mortality and survivor-bias tests pass.
- [ ] Implement Mesa runtime and explicit schedule.
  - Acceptance: V0–V4 scenarios and fixed-seed traces pass with documented stage order.
  - Verify: integration and regression tests pass without deprecation warnings.
- [ ] Implement CLI and JSON summary.
  - Acceptance: validation exits 0/2 correctly; run output is deterministic and schema-versioned.
  - Verify: CLI integration and byte-for-byte regression tests pass.
- [ ] Implement and verify minimal SolaraViz debugger.
  - Acceptance: resources, agents, energy, and core metrics render and update through normal model steps.
  - Verify: import smoke test and isolated-browser verification pass with a clean console.
- [ ] Run final quality and documentation gate.
  - Acceptance: at least 90% coverage, clean Ruff/Pyright/tests, dependency sync, lock consistency, and ODD
    reconciliation.
  - Verify: `just check` succeeds from the locked environment.

