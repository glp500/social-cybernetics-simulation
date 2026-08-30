# Project 2 Analysis Plan

## Analysis objects

Project 2 retains Project 1's full outcome vector and adds information, decision, and conversion
measures. All measures are calculated from immutable objective-frame, observation, belief, action, and
transition records.

## Information distribution

- `information_coverage` is observed unique cells divided by total world cells per agent-tick;
- `information_coverage_gini` is the Gini of agent-level mean coverage;
- `observation_error_distribution` contains signed and absolute perceived-minus-objective stock error,
  normalized by baseline cell capacity where positive;
- `observation_age_distribution` is `observation_tick - source_tick`;
- `opportunity_gap` is best objective stock in the declared frame minus objective stock at the selected
  target/current action cell, clamped non-negative;
- `decision_quality = 1 - opportunity_gap / max_baseline_capacity`, clamped to `[0,1]` when maximum
  capacity is positive and defined as `1` in an all-zero world;
- `decision_quality_gini` is calculated over agent-level mean decision quality.

This decision-quality score evaluates opportunity selection, not long-run policy optimality.

## Conversion chain

Agent/run tables report:

- profile and policy;
- mean coverage, error, age, decision quality, and opportunity gap;
- cumulative harvest and unmet need;
- survival and death tick;
- cumulative-harvest rank at fixed checkpoints.

Mixed-profile randomized contrasts estimate differences in each adjacent transformation:

```text
profile -> information quality -> decision quality -> harvest/shortfall -> survival
```

Report profile associations and randomized mean differences separately. Mediation language is not
permitted without a separately specified causal mediation analysis.

## Learning diagnostics

Retain exploration frequency, reward path, visited state-action coverage, Q-value range, policy-switch
count, and outcomes before/after the prespecified 100-tick learning warm-up. No convergence claim is
made from a stable average alone.

## Experimental unit

The seed-level run is the replicate. Profiles are randomized within mixed runs, so within-run
profile contrasts may use the assignment design while retaining run clustering. Agent-ticks are not
independent replicates.

## Joint reporting

Information and conversion metrics always accompany harvest, survival, unmet need, downside risk,
inequality, and ecological recovery. Improved sensing is not called beneficial when material/security
effects are absent or adverse.
