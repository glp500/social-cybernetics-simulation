# Project 3 Analysis Plan

## Embeddedness

- `social_information_fraction` is social fusion weight divided by total private-plus-social weight for
  positions used by the selected action, averaged per agent/run;
- report network degree, betweenness, and eigenvector centrality are calculated on the realized
  directed effective-report graph with definedness metadata;
- report correlations between network position and material outcome, and between network position and
  information access, with raw scatter data and no causal label.

## Source concentration

An effective report is one that contributes positive weight to a belief used for action.

- `source_HHI` is the sum of squared source shares of effective reports;
- `source_gini` is the Gini of effective-report counts by source, including zero-source agents;
- `top_source_share` and `top_10_percent_source_share` use deterministic fixed-size groups and report
  cutoff ties.

## Information dependency

For receiver `i` and source `j`, remove all of `j`'s reports from `i`'s recorded history, recompute
belief fusion and the fixed decision-quality score without rerunning ecology, and define:

```text
dependency[i,j] = max(0, factual_mean_quality - counterfactual_mean_quality)
```

Q-learning counterfactual dependency is not identified by offline removal because learning paths would
change; it is reported only for the fixed-policy control unless a separately specified replay method
is validated. Aggregate outputs include mean/max dependency, dependency concentration, and agents with
a single source accounting for more than half of total dependency.

Use “information dependency” or “gatekeeping potential,” never automatic “power.”

## Circulation

Per agent and dyad report:

- gross reports sent/received;
- `dyadic_balance = sent(i,j) - sent(j,i)`;
- gift/contribution cost burden and its distribution;
- credit inflow/outflow and net credit position;
- repayment latency for settled claims;
- default rate by claim and debtor;
- creditor/debtor concentration using HHI and Gini;
- obligation-network centralization;
- share of agents excluded from deferred access by at least one creditor.

Credit identities publish opening, inflow, outflow, and closing stocks separately from outstanding
principal. Every aggregate table carries a conservation check.

## Resilience

For each named outcome—survival, unmet need, information coverage, and network connectivity—record the
pre-shock value, worst post-shock deviation, and first tick that returns to and remains within 10% of
the pre-shock value for five ticks. Non-recovery by horizon is right-censored. Survival cannot recover
without births, so its measure is retained level loss rather than time-to-return.

## Joint reporting and inference

Relational outcomes accompany Project 1's material/ecological vector and Project 2's information
vector. Seeds are replicates. Reports, dyads, and ticks are nested observations and are not treated as
independent experimental units. Raw continuous outcomes accompany any regime label.
