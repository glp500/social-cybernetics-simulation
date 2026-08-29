---
type: literature-note
citekey: watkinsDayan1992QLearning
title: Q-learning
authors: Watkins; Dayan
year: 1992
status: reviewed
model_family:
  - reinforcement-learning
mechanisms:
  - tabular action-value learning
  - exploratory action selection
implementation_links:
  - docs/model_specification.md
tags:
  - literature
  - learning
  - q-learning
---

# Q-learning

## Citation

Watkins, C. J. C. H., & Dayan, P. (1992). Q-learning. *Machine Learning, 8*,
279–292. <https://doi.org/10.1007/BF00992698>

## Why this belongs

The roadmap needs a fixed, inspectable learning mechanism that can be compared with the literal
v0.1 policy. Tabular Q-learning supplies an incremental action-value update without requiring an
agent to know the environment's transition model.

## Supporting evidence

Watkins and Dayan define Q-learning for discrete state-action values and prove convergence to
optimal action values under conditions that include repeated sampling of every action in every
state. This directly supports using a tabular learner as an explicit adaptive-policy variant.

## Counterevidence and boundary conditions

The convergence result does not automatically transfer to this non-stationary multi-agent model.
Other agents, resource depletion, learning, network change, and institutional change can make an
individual agent's experienced transition process non-stationary. Finite experiments with constant
exploration also need not approach the asymptotic result.

## Justified commitment

Q-learning may enter as a versioned policy variant beside a fixed-policy control. Its Q table,
state encoding, action set, update evidence, and random exploration must remain inspectable.

## Project choices, not literature calibration

- energy and resource belief bins;
- learning rate `alpha = 0.1`;
- discount factor `gamma = 0.95`;
- exploration probability `epsilon = 0.1`;
- a homeostatic reward capped at the viability target;
- training duration and initialization values.

These values are preregistered experimental defaults until a calibration study supports them.

## Verification target

- [ ] fixed transitions reproduce hand-calculated Q updates
- [ ] the fixed-policy control never reads or mutates a Q table
- [ ] exploration draws use only the model-owned generator
- [ ] state-bin boundaries and reward capping are tested explicitly

