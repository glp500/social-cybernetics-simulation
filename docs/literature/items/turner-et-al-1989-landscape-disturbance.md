---
type: literature-note
citekey: turnerEtAl1989LandscapeDisturbance
title: Predicting the Spread of Disturbance across Heterogeneous Landscapes
authors: Turner; Gardner; Dale; O'Neill
year: 1989
status: reviewed
model_family:
  - landscape-ecology
mechanisms:
  - disturbance initiation probability
  - spatially correlated disturbance
  - heterogeneous landscape response
implementation_links:
  - src/social_cybernetics/domain/ecology.py
  - tasks/plan.md
tags:
  - literature
  - disturbance
  - spatial-ecology
---

# Predicting the Spread of Disturbance across Heterogeneous Landscapes

## Citation

Turner, M. G., Gardner, R. H., Dale, V. H., & O'Neill, R. V. (1989). Predicting the
spread of disturbance across heterogeneous landscapes. *Oikos, 55*(1), 121–129.
<https://doi.org/10.2307/3565881>

Related evidence: Massie, T., Weithoff, G., Kuckländer, N., Gaedke, U., & Blasius, B. (2015).
Enhanced Moran effect by spatial variation in environmental autocorrelation. *Nature
Communications, 6*, 5993. <https://doi.org/10.1038/ncomms6993>

Bender, E. A., Case, T. J., & Gilpin, M. E. (1984). Perturbation experiments in community ecology:
theory and practice. *Ecology, 65*, 1–13. <https://doi.org/10.2307/1939452>

Moreno-Mateos, D., Barbier, E. B., Jones, P. C., et al. (2017). Anthropogenic ecosystem disturbance
and the recovery debt. *Nature Communications, 8*, 14163.
<https://doi.org/10.1038/ncomms14163>

## Why this belongs

The v0.2 control must distinguish local independent stress, spatially correlated disturbance, and
system-wide forcing before agent information or institutions vary. Turner et al. provide a direct
landscape-model precedent for separating disturbance initiation frequency, spread intensity, and
landscape structure. Massie et al. provide experimental and theoretical evidence that correlated
environmental stochasticity can synchronize otherwise independent local populations.

## Supporting evidence

The effect and propagation of disturbance depend jointly on landscape structure, initiation
frequency, and spread intensity. Spatial correlation in environmental forcing is itself capable of
changing population-level dynamics without direct coupling between populations.

Turner et al. initiate disturbances probabilistically and allow them to spread through susceptible
habitat, producing spatially connected affected regions. Their outcome measures include affected
area and changes to landscape pattern. Massie et al. manipulate autocorrelated stochastic forcing
across independent populations and compare environmental correlation with population synchrony.
Bender et al. distinguish short pulse perturbations followed by relaxation from sustained press
perturbations. Moreno-Mateos et al. show that recovering ecosystems can retain substantial functional
deficits during the recovery interval.

## Counterevidence and boundary conditions

Neither paper implies that every disturbance is an instantaneous proportional loss of a renewable
stock. Turner et al. model spreading disturbance through susceptible landscape types, while Massie
et al. study correlated stochastic forcing and population synchrony rather than resource removal.
An event footprint, environmental autocorrelation, system-wide forcing, and ecological recovery are
scientifically related but not interchangeable mechanisms. The sources do not establish one linear
recovery clock shared by resource capacity and productivity.

## Justified commitment

The papers support treating event probability, connected spread, spatial correlation, and recovery
as separate ecological mechanisms while retaining affected-cell evidence. Independent, correlated,
and system-wide variants are useful controlled comparisons if their operational meanings remain
explicit.

## Project choices, not literature calibration

The papers do **not** uniquely imply multiplicative damage, a Bernoulli clock, Von Neumann
transmission, or finite linear recovery. The approved v0.2 semantics remain project choices:

- separate stock, effective-capacity, and effective-regeneration damage fractions;
- cell-local linear recovery restarted by compound hits;
- independent per-cell, correlated event-level, and system event-level Bernoulli hazards;
- concurrent synchronous correlated wavefronts with independent per-edge transmission;
- an explicit maximum number of outward propagation rounds.

These choices make mechanisms independently ablatable and auditable, but must not be described as
empirically calibrated. They can later be compared with press disturbances, nonlinear recovery, or
continuous random-field variants.

## Verification target

- [x] environment-rule target specified
- [x] identical seeds reproduce event, exposure, damage, and recovery records
- [x] zero probability and zero damage recover physical and policy controls
- [x] wavefronts remain connected and satisfy torus-aware Von Neumann geometry
- [x] simultaneous damage is order-independent and cannot exceed physical bounds
- [x] every cell returns exactly to baseline effective state after its latest recovery clock

## Sources

- [Turner Lab publication list](https://turnerlab.ibio.wisc.edu/publications/)
- [Massie et al. primary article](https://www.nature.com/articles/ncomms6993)
- [Bender et al. primary article](https://esajournals.onlinelibrary.wiley.com/doi/10.2307/1939452)
- [Moreno-Mateos et al. primary article](https://www.nature.com/articles/ncomms14163)
- Related decision: [[../../adr/0007-stochastic-ecological-variants|ADR 0007]]
