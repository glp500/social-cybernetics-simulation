# Project 3 Validation and Freeze Gates

**Status:** all gates open; implementation is not authorized by the current Project 1 phase.

| Gate | Freeze requirement |
| --- | --- |
| specification | report timing/content, fusion, trust, rewiring, diffusion, circulation, accounting, and scheduler are complete |
| literature | paired evidence covers network learning, trust, complex diffusion, embeddedness, reciprocity/risk-pooling boundaries, and debt/obligation limits |
| verification | exact network/report/fusion/trust/diffusion/credit/claim examples and invariants pass |
| sensitivity | trust, rewiring, diffusion, cost, and due-delay parameters are screened within mechanism-specific designs |
| experiment | P3-A–C publish before D; D0–D3 publish only after earlier gates pass |
| analysis | relational, dependency, circulation, obligation, resilience, and material metrics are frozen |
| interpretation | every result distinguishes concentration/dependency from power and credits/claims from money/debt generally |

## Required invariants

- every report identifies a realized sender→receiver relation at send tick;
- source tick never exceeds send tick and content matches the sender's recorded private information;
- fixed-network controls do not mutate topology or trust;
- trust stays in `[0,1]`, updates only on specified evidence, and unused decay is deterministic;
- rewiring removes/adds at most one relation per eligible agent-tick and cannot self-link or duplicate;
- reinforced adoption uses distinct sources within the declared window;
- adopted profiles are complete, immutable values and persist;
- D1–D3 charge the identical sender cost per delivered report;
- D2 never delivers without an existing transferred credit;
- D3 creates at most one claim per deferred report and settlement transfers an existing credit;
- total information credits are exactly conserved in D2/D3; outstanding claims are excluded from that
  stock identity;
- default closes a claim without changing credits and blocks only the specified creditor relation;
- all Project 1 and 2 material/information invariants continue to hold.

## Integration ladder

- N0: no-report control reproduces the matched Project 2 trajectory;
- N1: two-agent fixed network yields a hand-calculated fused belief;
- N2: report validation produces exact trust increase/decrease/decay;
- N3: small topology yields exact fixed and adaptive rewiring traces;
- N4: simple and two-source reinforced diffusion diverge on a controlled exposure sequence;
- N5: D0–D3 hand ledgers prove sender costs, credit conservation, settlement, default, and exclusion;
- N6: artifact-only counterfactual source removal reproduces dependency metrics.
