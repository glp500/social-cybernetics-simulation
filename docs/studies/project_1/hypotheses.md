# Project 1 Hypotheses

Hypotheses are comparisons of named outcome vectors. A directional component may fail while another
holds; no condition is ranked by a single statistic.

## P1-A — Ecological heterogeneity

- **Contrast:** uniform capacity versus a mean-preserving low/high checkerboard landscape.
- **Primary hypothesis:** heterogeneity changes harvest and shortfall distributions even when total
  baseline capacity is held constant.
- **Persistence hypothesis:** any early rank advantage lasts longer in the heterogeneous condition.
- **Null:** paired outcome and persistence distributions do not differ beyond seed variation.

The test does not assume the sign of aggregate harvest or survival.

## P1-B — Population pressure and mobility

- **Contrast:** 5 versus 20 agents crossed with movement cost `0.0` versus `0.5` on the same 25-cell
  homogeneous world.
- **Primary hypothesis:** population pressure increases shortfall and depletion.
- **Interaction hypothesis:** movement cost changes how density is converted into security and
  inequality; the sign is not preregistered.
- **Null:** density and movement-cost contrasts do not change the outcome vector beyond seed variation.

## P1-C — Disturbance structure

- **Contrast:** independent, correlated, and system shocks with equal expected initially hit cells per
  tick.
- **Primary hypothesis:** spatial correlation changes downside risk and recovery even when expected
  initial incidence is matched.
- **Boundary:** correlated propagation adds later hits, so total realized affected-cell exposure is an
  outcome rather than a controlled equality.
- **Null:** scope-specific paired outcome distributions do not differ beyond seed variation.

## P1-D — Recovery

- **Contrast:** recovery in `2` versus `10` ticks with all other mechanisms fixed.
- **Primary hypothesis:** slow recovery increases cumulative recovery deficit and shortfall burden.
- **Tradeoff hypothesis:** endpoint stock can obscure cumulative ecological and security differences.
- **Null:** recovery speed does not change the outcome vector beyond seed variation.

## P1-E — Persistence

- **Contrast:** representative control, heterogeneous high-pressure, and correlated slow-recovery
  regimes run for 1,000 ticks.
- **Primary hypothesis:** some short-horizon distributional differences decay while others persist;
  classification depends on rank and half-life evidence rather than final Gini alone.
- **Null:** material ranks show no stable association across prespecified lags.

## Joint outcome requirement

Every hypothesis table reports aggregate harvest, survival, mean unmet need, catastrophic downside
risk, named inequality measures, and ecological recovery. Persistence experiments additionally report
rank autocorrelation, transition matrices, advantage duration, and inequality half-life with
definedness metadata.
