---
type: literature-note
citekey: morris1991FactorialSampling
title: Morris Screening for Stochastic Simulation Experiments
authors: Morris; Campolongo; Cariboni; Saltelli; Stout; Goldie
year: 1991
status: reviewed
model_family:
  - sensitivity-analysis
  - stochastic-simulation
mechanisms:
  - elementary-effects screening
  - optimized trajectories
  - common random numbers
implementation_links:
  - tasks/plan.md
  - docs/adr/0011-scope-stratified-morris-screening.md
tags:
  - literature
  - sensitivity
  - experiment-design
---

# Morris Screening for Stochastic Simulation Experiments

## Citations

Morris, M. D. (1991). Factorial sampling plans for preliminary computational experiments.
*Technometrics, 33*(2), 161–174. <https://doi.org/10.1080/00401706.1991.10484804>

Campolongo, F., Cariboni, J., & Saltelli, A. (2007). An effective screening design for sensitivity
analysis of large models. *Environmental Modelling & Software, 22*(10), 1509–1518.
<https://doi.org/10.1016/j.envsoft.2006.10.004>

Stout, N. K., Goldie, S. J., et al. (2009). Keeping the noise down: common random numbers for disease
simulation modeling. *Health Care Management Science, 12*, 399–406.
<https://doi.org/10.1007/s10729-009-9107-7>

## Why this belongs

The v0.2 ecological model has five common shock inputs and two additional propagation inputs. A
screening design is needed before more expensive variance decomposition is defensible. Because the
model is stochastic, comparisons also need to distinguish parameter changes from variation caused
by shock and movement draws.

## Supporting evidence

Morris defines randomized one-factor-at-a-time trajectories and elementary effects for screening
moderate-to-large input sets without assuming monotonicity, sparsity, or a low-order response
surface. Campolongo et al. improve the method through the absolute mean elementary effect and by
selecting trajectories that cover the input space more effectively. This supports an optimized
Morris screen as a first, economical ranking step rather than a final attribution analysis.

Stout et al. describe common random numbers as a variance-reduction method: alternative conditions
reuse coordinated random streams so comparisons are less obscured by simulation noise. The project's
permanent mechanism-specific substreams make paired run seeds an inspectable implementation of that
principle.

## Counterevidence and boundary conditions

The original Morris method addresses deterministic computational models. In a stochastic ABM, one
elementary effect from one realization can mix input influence with intrinsic variance. Pairing seeds
improves within-seed comparisons but does not eliminate stochastic uncertainty, and the resulting
observations are not independent across parameter points. Replicated seed blocks and seed-stratified
analysis remain necessary.

Morris is a screening method. Its `mu_star` and dispersion statistics do not provide variance shares,
causal effects, or calibrated policy thresholds. Strong dispersion can reflect nonlinearity,
interactions, stochastic noise, or a combination of them. Important factors should be followed by a
narrower replication or variance-based study.

The three shock scopes have different event semantics and different active parameter sets. Treating
`shock.kind` as a numeric factor would invent an ordering among categorical mechanisms and would
create inactive propagation inputs for independent and system shocks.

## Justified commitment

Use separate Morris designs for independent, correlated, and system shocks. Reuse the same explicit
replicate seeds at every point within and across scopes. Retain scope, design-point order, factor
values, model seed, resolved configuration, and raw continuous model outputs. Analyze scopes
separately before making cross-scope comparisons.

## Project choices, not literature calibration

The following choices make the first screen broad, finite, and easy to inspect; the papers do not
calibrate them:

- four Morris levels;
- 100 candidate trajectories and 10 locally optimized selected trajectories per scope;
- design seed 42;
- explicit paired model seeds 101, 202, and 303;
- `[0, 1]` bounds for event probability and all damage/spread fractions;
- `[1, 10]` for integer recovery ticks and `[0, 3]` for integer propagation rounds;
- a fail-closed maximum of 600 generated runs.

At four levels the integer bounds yield exact grids of `1, 4, 7, 10` and `0, 1, 2, 3`. The design
contains 60 points for each five-factor scope and 80 for the seven-factor correlated scope. Three
paired seeds therefore produce `180 + 240 + 180 = 600` model runs.

## Verification target

- [ ] identical sensitivity specification and design seed reproduce ordered points byte-for-byte
- [ ] every factor value lies on its declared grid and validates through `SimulationConfig`
- [ ] each design point is repeated with the same ordered seed block
- [ ] categorical, unknown, inactive, non-scalar, and non-integral factor paths fail before execution
- [ ] generated runs execute only through the existing batch publication boundary
- [ ] analysis retains raw outcomes and reports replicate-seed variation

## Sources

- [Morris primary article](https://doi.org/10.1080/00401706.1991.10484804)
- [Campolongo et al. primary article](https://doi.org/10.1016/j.envsoft.2006.10.004)
- [Stout et al. primary article](https://doi.org/10.1007/s10729-009-9107-7)
- [SALib Morris implementation documentation](https://salib.readthedocs.io/en/latest/_modules/SALib/sample/morris/morris.html)
- Related decision: [[../../adr/0011-scope-stratified-morris-screening|ADR 0011]]
