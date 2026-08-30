# ADR 0012: Organize the Programme by Independent Studies

- **Status:** Accepted
- **Date:** 2026-08-30
- **Supersedes:** the active version-driven configuration framing in ADR 0007; ADR 0007 remains the
  authoritative history of stochastic ecological semantics.

## Context

The pre-refactor repository used schema versions 0.1 and 0.2 to express an expanding model roadmap.
The revised scientific programme instead requires three independently interpretable studies:
objective ecological opportunity, privately actionable opportunity, and socially accessible
opportunity. A continually widened agent/configuration risks leaking speculative economic and social
state into controls and makes it difficult to identify which transformation causes a result.

The verified v0.2 mechanics already implement Project 1's environmental boundary. They should be
preserved rather than rewritten for naming alone.

## Decision

1. The canonical executable configuration is named `Study01Config` and carries an explicit Project 1
   study identity.
2. `SimulationConfig` remains a compatibility alias for one migration period. A single documented
   normalization path accepts historical v0.1/v0.2 YAML and resolves it to the equivalent Project 1
   configuration before model construction.
3. Canonical repository YAML migrates to the study contract. Baseline mechanics and JSON output remain
   regression-compatible under equivalent inputs.
4. `Study02Config` and `Study03Config` are names reserved by their scientific specifications. They are
   not accepted by the executable loader until their studies are separately authorized and
   implemented.
5. Shared agent state contains only material/physiological fields required by all executable studies.
   Observation/learning state and network/circulation state are composed in their respective studies.
6. Scientific study identity, configuration schema, run-bundle schema, table schema, and software
   package version are separate version axes. Changing one does not silently change the others.
7. Analysis consumes immutable records through study-specific pure modules; it does not widen runtime
   state or introduce alternate simulation transitions.

## Compatibility policy

Legacy normalization is explicit, tested, and one-way. Published Project 1 bundles store the canonical
normalized configuration, not the spelling of legacy input. Unknown study IDs and future fields fail
closed. The compatibility alias can be removed only through a later deprecation ADR with a migration
window and release evidence.

## Consequences

### Positive

- each study has a stable mechanical control and claims boundary;
- future state cannot contaminate Project 1 records;
- cross-study analysis compares named transformations instead of one opaque mega-model;
- legacy ecological fixtures remain scientifically useful;
- configuration and artifact migrations become explicit and independently versioned.

### Costs

- loaders and tests temporarily support one legacy normalization path;
- later studies must compose and persist their own records instead of reusing dormant fields;
- cross-study orchestration requires explicit configuration/artifact references;
- documentation must distinguish specification completeness from executable completeness.

## Rejected alternatives

- **Continue one `SimulationConfig` with increasing schema numbers:** hides study identity and
  encourages shared speculative state.
- **Rewrite the verified ecology engine behind an entirely new API:** creates regression risk without
  scientific benefit.
- **Define executable placeholder Study 02/03 models:** violates fail-closed configuration and makes
  unimplemented science appear supported.
- **Build one integrated model now:** prevents clean attribution of material, private-information, and
  social-information transformations.
