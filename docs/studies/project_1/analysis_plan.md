# Project 1 Analysis Plan

**Status:** frozen and implemented in schema `scs-project1-outcome/v1.0.0` and aggregate bundle
schema `scs-project1-analysis-bundle/v1.0.0` on 2026-08-31.

The canonical artifact-only analysis completed 140/140 runs. Its local analysis-manifest SHA-256 is
`773f07fcb61d3f9616666e514e0a67c8c8299bfea3f03126dd11a0c28bab983a`.

## Authority and inputs

Analysis is pure and post hoc. It consumes validated Project 1 run bundles: normalized configuration,
cohort snapshots, active agent transitions, shock/damage records, and complete spatial history. No
headline measure may read a live model object.

Let `N` be original cohort size, `A` the set of active agent-transitions, `T` completed ticks,
`v` the viability target, and `u[i,t] = max(0, v - E[i,t])` for an active transition's post-metabolism
energy.

## Subsistence security

- `shortfall_frequency = count(u > 0) / count(A)`; defined as `0` when `A` is empty.
- A shortfall spell is a maximal consecutive sequence of active ticks with `u > 0` for one agent.
  Death closes a terminal spell; survival at the final tick marks it right-censored.
- `shortfall_spell_length` reports the full spell-length list plus mean; no spells gives an empty list
  and mean `0`.
- `mean_shortfall_depth = mean(u | u > 0)`; defined as `0` when no positive shortfall exists.
- `maximum_shortfall_depth = max(u)`; defined as `0` when `A` is empty.
- `catastrophic_shortfall_probability` is the fraction of active transitions ending at zero energy.
  A dead agent contributes once—on its terminal active transition—not on later archival snapshots.

## Distribution

At the final tick, use cumulative harvest `H[i]`, final cohort energy `E[i]`, and cumulative active
shortfall `U[i]`:

- `harvest_gini = gini(H)`;
- `energy_gini = gini(E)`;
- `unmet_need_gini = gini(U)`;
- `top_10_percent_harvest_share` is the share held by the highest `ceil(0.10*N)` agents;
- `bottom_25_percent_shortfall_share` is the share of `U` borne by the lowest
  `ceil(0.25*N)` agents ranked by `H`.

Groups contain at least one agent when `N > 0`. Zero totals yield share `0`. Agent ID breaks exact
harvest ties only to select a deterministic fixed-size group; the analysis reports the number of ties
at the cutoff.

## Persistence

Persistence uses cumulative harvest, not final energy, because harvest is the direct allocated
material flow.

- `material_rank_autocorrelation` is Spearman correlation between cumulative-harvest midranks at
  `ceil(T/2)` and `T`. It is undefined for fewer than two agents or constant ranks at either time.
- `rank_transition_matrix` maps quartile membership at `ceil(T/2)` to final quartile. Rows contain
  conditional proportions and raw counts. Percentile midranks assign ties to the same quartile.
- For each agent, an advantage spell is a maximal sequence of active ticks during which cumulative
  harvest is strictly above the cohort median. `advantage_duration` reports all spell lengths, their
  mean, and maximum.
- Let `G[t]` be cumulative-harvest Gini. `inequality_half_life` is the first tick after the earliest
  maximum where `G[t] <= 0.5 * max(G)`. If no such tick occurs before `T`, it is right-censored and
  reports observed remaining duration. If `max(G)=0`, the half-life is `0` and defined.

The half-life is a descriptive decay measure, not evidence of an equilibrium process.

## Ecology

For every spatial tick, sum over cells and normalize to avoid mixing landscape scale with deficit:

```text
resource_depletion[t] = sum(K_base - S[t]) / sum(K_base)
capacity_deficit[t] = sum(K_base - K_eff[t]) / sum(K_base)
regeneration_deficit[t] = sum(r_base - r_eff[t]) / sum(r_base)
```

When a denominator is zero, the corresponding fraction is `0` only if its numerator is also zero;
otherwise the bundle violates its configuration invariant.

- `recovery_duration` reports maximal contiguous cell-level sequences with recovery remaining above
  zero, distinguishing completed and right-censored spells. Repeated damage extends the observed spell.
- `cumulative_recovery_deficit` is the tick sum of mean normalized capacity and regeneration deficit:
  `sum_t((capacity_deficit[t] + regeneration_deficit[t]) / 2)`. Both components are also published;
  the combined value is a descriptive burden, not welfare.

Primary ecological outputs report final, mean, and maximum resource depletion; final/mean capacity and
regeneration deficits; recovery spell distributions; and cumulative deficit components.

## Efficiency/security vector

Every experiment reports jointly:

- aggregate harvest;
- survival fraction;
- mean cumulative unmet need per original cohort member;
- catastrophic shortfall probability;
- harvest, energy, and unmet-need inequality;
- ecological depletion and cumulative recovery deficit.

No scalar ranking or hidden weights are permitted.

## Experimental summaries

The raw table has one row per run. Condition summaries include replicate count, mean, median, standard
deviation, minimum, and maximum for each defined continuous measure. Paired contrasts subtract outcomes
within seed. Undefined values remain null with reasons and are excluded only from that measure's
summary; counts of defined/undefined runs are always retained.

Any inferential interval added later must be preregistered, use the seed as the replicate unit, and
appear alongside raw outcomes. Tick or agent resampling cannot masquerade as independent replication.
