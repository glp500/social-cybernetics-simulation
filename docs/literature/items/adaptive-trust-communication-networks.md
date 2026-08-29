---
type: literature-note
citekey: bendtsenEtAl2016ExpertGame
title: Adaptive trust and communication networks
authors: Holme; Newman; Bendtsen; Uekermann; Haerter
year: 2016
status: reviewed
model_family:
  - adaptive-networks
  - experimental-networks
mechanisms:
  - network-state coevolution
  - preferential communication
  - relational trust
implementation_links:
  - docs/model_specification.md
tags:
  - literature
  - networks
  - trust
  - communication
---

# Adaptive trust and communication networks

## Citations

- Holme, P., & Newman, M. E. J. (2006). Nonequilibrium phase transition in the coevolution of
  networks and opinions. *Physical Review E, 74*, 056108.
  <https://doi.org/10.1103/PhysRevE.74.056108>
- Bendtsen, K. M., Uekermann, F., & Haerter, J. O. (2016). Expert Game experiment predicts
  emergence of trust in professional communication networks. *Proceedings of the National Academy
  of Sciences, 113*, 12099–12104. <https://doi.org/10.1073/pnas.1511273113>

## Why this belongs

Information capability can only have a network-mediated effect if who communicates with whom can
be represented independently of physical proximity. The roadmap additionally requires the
communication graph and relational assessments to change with experience.

## Supporting evidence

Holme and Newman provide a foundational model in which node states and network connections
coevolve, showing that adoption and rewiring can jointly change macroscopic regimes. Bendtsen et al.
observe reciprocal communication preferences and increased information flow emerging through
repeated attributed interactions in a controlled experiment, and fit a behavioral network model to
those dynamics.

## Counterevidence and boundary conditions

Holme and Newman's rewiring follows opinion similarity, not verified information usefulness.
Bendtsen et al. study 32 participants in a professional-information game; their result does not
calibrate ecological advice, deliberate misinformation, tie decay, or local-contact exploration.
Preferential communication may also create exclusion or epistemic segregation rather than only
improving information quality.

## Justified commitment

Communication topology, relational trust, message evidence, and physical position may be modeled as
distinct state. Static-network and fixed-trust controls are required before interpreting effects as
the consequence of coevolution.

## Project choices, not literature calibration

- the trust increase for useful information and decrease for misleading information;
- the definition and delay of usefulness feedback;
- unused-tie decay, pruning threshold, and new-contact exploration rate;
- whether trust is directed, message-specific, or aggregated;
- initial topology and restrictions on geographically local exploration.

These choices require a dedicated network-design decision before implementation.

## Verification target

- [ ] trust updates are attributable to immutable message/outcome evidence
- [ ] static-network and fixed-trust controls share all non-network mechanisms
- [ ] unused ties decay only under the selected clock and cannot become invalid weights
- [ ] graph draws use the model-owned generator and reproduce under a fixed seed

