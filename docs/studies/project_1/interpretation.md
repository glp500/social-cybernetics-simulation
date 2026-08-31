# Project 1 Interpretation Register

**Status:** frozen against analysis manifest
`e1793afcdace33780563039ee89e40dcaa7df427cb07d2516421fb5d6c7bc52a` on 2026-08-31.

## Outcome overview

Values are condition means across ten paired seeds. `H` is aggregate harvest, `S` survival fraction,
`U` mean cumulative unmet need per original cohort member, `C` catastrophic-transition probability,
`G-H` harvest Gini, `G-E` final-energy Gini, `D` final resource depletion, and `R` cumulative recovery
deficit. These remain a vector; the table does not rank regimes.

| Experiment | Condition | H | S | U | C | G-H | G-E | D | R |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1-A | homogeneous | 1065.66 | 1.00 | 0.00 | 0.0000 | 0.000 | 0.000 | 0.400 | 0.00 |
| P1-A | checkerboard | 926.75 | 0.57 | 108.01 | 0.0057 | 0.310 | 0.559 | 0.342 | 0.00 |
| P1-B | 5 agents, cost 0 | 532.83 | 1.00 | 0.00 | 0.0000 | 0.000 | 0.000 | 0.200 | 0.00 |
| P1-B | 5 agents, cost 0.5 | 532.83 | 1.00 | 0.00 | 0.0000 | 0.000 | 0.000 | 0.200 | 0.00 |
| P1-B | 20 agents, cost 0 | 2131.32 | 1.00 | 0.00 | 0.0000 | 0.000 | 0.000 | 0.800 | 0.00 |
| P1-B | 20 agents, cost 0.5 | 2131.32 | 1.00 | 0.00 | 0.0000 | 0.000 | 0.000 | 0.800 | 0.00 |
| P1-C | independent | 746.91 | 0.52 | 98.19 | 0.0066 | 0.260 | 0.626 | 0.397 | 4.27 |
| P1-C | correlated | 507.80 | 0.15 | 145.70 | 0.0155 | 0.289 | 0.780 | 0.718 | 22.80 |
| P1-C | system | 922.70 | 0.80 | 41.98 | 0.0029 | 0.103 | 0.359 | 0.367 | 3.10 |
| P1-D | recovery 2 | 753.15 | 0.49 | 101.83 | 0.0068 | 0.251 | 0.625 | 0.358 | 2.69 |
| P1-D | recovery 10 | 701.83 | 0.52 | 96.55 | 0.0070 | 0.304 | 0.625 | 0.433 | 9.51 |
| P1-E | control | 10065.66 | 1.00 | 0.00 | 0.0000 | 0.000 | 0.000 | 0.400 | 0.00 |
| P1-E | heterogeneous pressure | 16589.83 | 0.565 | 113.83 | 0.0007 | 0.435 | 0.493 | 0.658 | 0.00 |
| P1-E | correlated slow recovery | 3398.44 | 0.24 | 160.78 | 0.0027 | 0.620 | 0.777 | 0.388 | 90.95 |

The displayed means come from the validated condition-summary artifact. Raw replicate values,
definedness reasons, 4,480 all-pairs within-seed differences, full temporal paths, and record-level
evidence remain in the validated analysis and child run bundles. Differences below are descriptive
paired-seed results; no confidence interval or population inference was preregistered.

## P1-A — Mean-preserving heterogeneity

- **Observed pattern:** checkerboard minus homogeneous changed mean harvest by `-138.91`, survival by
  `-0.43`, unmet need by `+108.01`, harvest Gini by `+0.310`, and final depletion by `-0.058`.
  Checkerboard cumulative-harvest rank autocorrelation was `1.0`; the homogeneous value was undefined
  because all ranks were tied.
- **Mechanical causal explanation:** the same total capacity was redistributed across fixed initial
  locations. Low-capacity cells crossed the literal harvest threshold, causing random moves, costs,
  and path dependence; 69 moves occurred across P1-A. No social allocation mechanism intervened.
- **Computational domain:** 5×5 torus, 10 agents, 100 ticks, ten paired seeds, designed 5/15 cells
  with a centre value of 10. The result is conditional on row-major placement and the literal policy.
- **Economic interpretation:** unequal ecological opportunity alone generated unequal material flows
  and security in this model. It does not identify a market, endowment distribution, or welfare order.
- **Political-economic interpretation:** the result is an ecological control for later relational
  studies. There is no ownership, class process, labour contract, appropriation, or accumulation.
- **Anthropological interpretation:** it is consistent with spatially uneven foraging opportunity
  producing livelihood risk, but contains no household, sharing, tenure, knowledge, or cultural norm.
- **Alternative explanation:** the threshold policy and unrandomized initial placement may amplify
  checkerboard geometry; another policy could attenuate, reverse, or redistribute the result.
- **Missing mechanisms / prohibited conclusion:** perception error, learning, cooperation, property,
  demographics, and institutions are absent. Heterogeneity does not demonstrate class or exploitation.

## P1-B — Density and the mobility null

- **Observed pattern:** moving from 5 to 20 agents increased aggregate harvest by `1598.49` and final
  depletion by `0.60`, while survival remained 1 and inequality/unmet need remained zero. Movement
  cost changed no recorded outcome at either density.
- **Mechanical causal explanation:** all 50,000 P1-B active transitions were harvest actions; no agent
  moved, so the movement-cost parameter was never applied. Higher aggregate harvest is largely the
  arithmetic consequence of four times as many continuously harvesting agents.
- **Computational domain:** homogeneous 5×5 world, 100 ticks, counts 5/20, costs 0/0.5, ten seeds. The
  density fixture did not create local threshold scarcity and therefore did not activate mobility.
- **Economic interpretation:** the design shows higher aggregate throughput and ecological pressure,
  not improved per-capita provisioning. The preregistered shortfall and mobility-interaction hypotheses
  were not supported in this computational domain.
- **Political-economic interpretation:** population count is not a class or labour relation; the null
  cannot support scarcity, overpopulation, or productivity claims about real economies.
- **Anthropological interpretation:** the fixture omits settlement, territorial access, household
  organization, cooperation, and purposeful relocation, so it is not a mobility model of a community.
- **Alternative explanation:** a lower-stock, contested, or heterogeneous fixture would trigger moves
  and could make mobility cost consequential. The null diagnoses this design-policy combination.
- **Missing mechanisms / prohibited conclusion:** strategic movement and access rules are absent.
  Do not conclude that mobility costs are generally irrelevant or that density cannot create insecurity.

## P1-C — Disturbance scope

- **Observed pattern:** relative to independent shocks, correlated shocks changed harvest by `-239.10`,
  survival by `-0.37`, unmet need by `+47.51`, depletion by `+0.321`, and recovery deficit by `+18.52`.
  System shocks changed those outcomes by `+175.79`, `+0.28`, `-56.21`, `-0.030`, and `-1.17`.
- **Mechanical causal explanation:** the design matched one expected initially affected cell per tick,
  not temporal clustering or propagated exposure. Correlated events began every tick and spread;
  system events were rare simultaneous pulses. Complete exposure/damage records preserve this difference.
- **Computational domain:** homogeneous 5×5 world, 10 agents, 100 ticks, common damage and five-tick
  recovery, ten paired seeds. Only initial incidence is matched exactly.
- **Economic interpretation:** disturbance geometry and timing changed both provisioning and incidence;
  expected initial hit count alone was not sufficient to characterize material risk.
- **Political-economic interpretation:** correlated ecological exposure is not unequal exchange,
  dispossession, or crisis transmission through social institutions because none is represented.
- **Anthropological interpretation:** the comparison may motivate attention to clustered livelihood
  hazards, but has no social buffering, memory, kin network, or collective response.
- **Alternative explanation:** severity follows the chosen hazard frequencies and propagation design;
  matching realized damaged-cell time or event duration could yield a different scope ordering.
- **Missing mechanisms / prohibited conclusion:** adaptation, forecasting, relief, and institutions are
  absent. Do not translate scope differences into real disaster estimates.

## P1-D — Recovery speed

- **Observed pattern:** recovery 10 minus recovery 2 changed mean recovery deficit by `+6.825`, final
  depletion by `+0.0745`, harvest by `-51.32`, survival by `+0.03`, and unmet need by `-5.28`. The
  security differences varied substantially across seeds and do not form a uniformly worse vector.
- **Mechanical causal explanation:** the longer cell-local clock retained capacity/regeneration damage
  for more ticks. Agent paths and shock realizations then interacted with the altered stock trajectory.
- **Computational domain:** correlated hazard 0.2, spread 0.5, two rounds, 100 ticks, ten paired seeds;
  only recovery duration changed.
- **Economic interpretation:** slow ecological recovery clearly increased ecological burden and reduced
  mean harvest, while short-run survival/unmet-need components did not move monotonically.
- **Political-economic interpretation:** recovery time is a biophysical control, not investment,
  reconstruction policy, social resilience, or a relation of appropriation.
- **Anthropological interpretation:** no local recovery practice, mutual aid, seasonal knowledge, or
  household smoothing exists, so resilience is limited to the cell ecology.
- **Alternative explanation:** ten seeds are a transparent screen, not a precise tail estimate; longer
  horizons or a policy that responds to recovery could change security effects.
- **Missing mechanisms / prohibited conclusion:** adaptation and social buffering are absent. The result
  does not estimate community resilience or establish a single superior recovery regime.

## P1-E — Long-horizon persistence

- **Observed pattern:** at 1,000 ticks, cumulative-harvest rank autocorrelation was undefined in the
  tied control, `1.000` under heterogeneous pressure, and `0.986` under correlated slow recovery.
  Mean advantage-spell durations were 0, `555.7`, and `215.1` ticks respectively. The two non-control
  regimes also retained large harvest/energy inequalities and substantial survival losses.
- **Mechanical causal explanation:** fixed local ecology, literal threshold action, and mortality lock
  in early cumulative-harvest ordering. No learning, transfer, reproduction, or inheritance is needed
  for this bounded material-rank persistence.
- **Computational domain:** three deliberately different representative regimes, 1,000 ticks, ten seeds.
  Because the regimes also differ in agent count or shock process, their aggregate harvests are not a
  clean one-factor causal contrast.
- **Economic interpretation:** persistent cumulative material advantage exists in the model, but it is
  not a wealth stock, return to capital, income process, or composite welfare ranking.
- **Political-economic interpretation:** persistence without property relations is a control showing
  what ecology alone can generate; it cannot explain class reproduction or exploitation.
- **Anthropological interpretation:** durable provisioning differences can arise without modeled norms,
  but real persistence may instead be transformed by sharing, tenure, household cycles, and knowledge.
- **Alternative explanation:** cumulative ranks are mechanically inertial and mortality removes later
  opportunities to reorder; windowed flow ranks could show less persistence.
- **Missing mechanisms / prohibited conclusion:** assets, inheritance, institutions, social information,
  and demographics are absent. Do not call the result wealth, class, or intergenerational persistence.

## Standing boundaries

- A Gini change with constant aggregate harvest is distributional, not automatically efficient or
  inefficient.
- Higher harvest with greater downside exposure is a tradeoff, not a superior regime.
- Recovery deficit is an abstract ecological-state burden, not biodiversity or ecosystem function.
- Mortality is failure of an abstract energetic viability condition, not an empirical mortality risk.
- Every numeric level is a project choice rather than an empirical calibration.
