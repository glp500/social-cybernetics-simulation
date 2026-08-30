# Project 2 Specification: Private Information and Adaptive Capacity

**Status:** specified; not implemented or executable.

## Purpose

Project 2 asks how bounded private information and private adaptation transform objective ecological
opportunity into privately actionable opportunity. It reuses frozen Project 1 ecological regimes and
changes only the observation/belief/policy layer.

## Observation channel

Each agent has a complete sensing profile:

```text
C = (radius, noise, delay)
```

- `radius` is Manhattan distance on the configured world and is one of `0, 1, 2` in P2-A;
- `noise` is the standard deviation of independent zero-mean Gaussian error expressed as a fraction
  of each observed cell's baseline capacity; experiment levels are `0.0` and `0.25`;
- `delay` selects environmental state from `max(0, tick - delay)`; levels are `0` and `2` ticks.

An observation is an immutable tuple of source tick, observation tick, spatial frame, and perceived
stock by position. Perceived stock is clamped to `[0, baseline_capacity]`. Noise draws use a dedicated
recorded substream and never shift ecology, movement, learning, or profile-assignment draws.

## Belief

The initial belief is a direct immutable copy of the most recent observation frame. No Bayesian model,
world model, social report, or imputation beyond the observed frame exists. Belief records preserve
source age and error against the objective historical frame for analysis.

## Policies

### Fixed information-sensitive control

If believed current-cell stock meets the harvest threshold, request harvest as in Project 1.
Otherwise select the believed richest visible cell and move one step along a shortest toroidal
Von Neumann path toward it. Equal-valued target/path ties use the policy stream. If the radius-zero
profile has no distinct target, use Project 1's uniform-neighbour movement.

### Private tabular Q-learning

Q-learning uses energy and believed-resource bins, action values for harvest and four cardinal moves,
and no shared experience. Project choices are `alpha=0.1`, `gamma=0.95`, `epsilon=0.1`, zero initial
Q-values, and epsilon-greedy/tie draws from a dedicated learning stream.

The homeostatic reward is:

```text
reward = min(E_after, viability_target) - min(E_before, viability_target)
```

Thus energy above the target provides no additional reward. These settings are controlled
comparators, not cognitive calibration.

## State composition

`Study02Config` contains one validated frozen Project 1 ecological config plus observation and policy
variants. `Project2AgentState` composes base material state with a sensing profile, observation/belief
history, and—only for the learning variant—a Q-table. Project 1's base state is not widened.

## Scheduler changes

Project 1 ecology, gate, physical resolution, metabolism, mortality, and measurement remain fixed.
The observation, belief, and intent stages dispatch Project 2 variants. Learning updates after
physical/physiological feedback and before measurement, with an explicit stage added to the Study 02
trace. Exact ordering must be frozen before code.

## Evidence

Records must retain objective frame, perceived frame, source/observation tick, profile, belief used,
action values or fixed-policy scores, selected action, exploration flag, reward, and material
transition. Every error/quality metric must be reconstructable without a live agent.

## Exclusions

No report, network, trust, social learning, capability diffusion, exchange, credit, obligation,
institution, material market, demographic mechanism, neural policy, or world model is present.
