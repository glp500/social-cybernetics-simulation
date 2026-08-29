---
type: literature-note
citekey: fraleyRaftery2002ModelBasedClustering
title: Model-based institutional regime discovery
authors: Schwarz; Fraley; Raftery; Hennig
year: 2002
status: reviewed
model_family:
  - statistical-analysis
mechanisms:
  - Gaussian mixture clustering
  - BIC model comparison
  - bootstrap cluster stability
implementation_links:
  - docs/model_specification.md
tags:
  - literature
  - analysis
  - clustering
  - institutions
---

# Model-based institutional regime discovery

## Citations

- Schwarz, G. (1978). Estimating the dimension of a model. *The Annals of Statistics, 6*,
  461–464. <https://doi.org/10.1214/aos/1176344136>
- Fraley, C., & Raftery, A. E. (2002). Model-based clustering, discriminant analysis, and density
  estimation. *Journal of the American Statistical Association, 97*, 611–631.
  <https://doi.org/10.1198/016214502760047131>
- Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Computational Statistics & Data
  Analysis, 52*, 258–271. <https://doi.org/10.1016/j.csda.2006.11.025>

## Why this belongs

Institutional regimes should be discovered from multivariate, rolling-window behavior rather than
declared solely from the rule currently held by an agent. Model-based clustering offers an explicit
probabilistic exploratory analysis, while information criteria and resampling provide checks against
unconstrained storytelling.

## Supporting evidence

Schwarz derives the large-sample model-dimension criterion now known as BIC. Fraley and Raftery
develop a principled model-based clustering methodology using finite mixture models. Hennig gives a
cluster-wise resampling approach in which bootstrap solutions are compared with original clusters,
including Jaccard-based stability evidence.

## Counterevidence and boundary conditions

A Gaussian component need not correspond to a substantively meaningful institutional regime.
Mixtures can split a non-Gaussian cluster into multiple components, EM solutions can depend on
initialization, and stable clusters can still be artifacts of an inflexible clustering method.
Time-window overlap also violates a naive independent-observation interpretation. BIC and bootstrap
stability therefore do not validate the causal meaning of a label.

## Justified commitment

Gaussian mixtures may be used as secondary exploratory summaries after features and windows are
preregistered. Component labels must always accompany standardized raw features, continuous
institutional metrics, BIC comparisons, initialization diagnostics, and resampling stability.

## Project choices, not literature calibration

- considering 1–6 components and using 20 initializations;
- covariance parameterization and regularization;
- rolling-window length and overlap;
- the adoption, connectivity, boundary, enforcement, entropy, and nesting feature definitions;
- bootstrap unit, number of replicates, matching rule, and stability threshold;
- naming and interpreting fitted components as institutional regimes.

These choices require an analysis protocol before implementation.

## Verification target

- [ ] synthetic one-regime data can retain the one-component explanation
- [ ] label permutations do not change stability results
- [ ] multiple initializations and all BIC values are retained
- [ ] raw continuous metrics remain available independently of fitted labels
- [ ] bootstrap units respect experimental and temporal dependence

