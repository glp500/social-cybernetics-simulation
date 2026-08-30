# Project 2 Experiments

**Status:** planned; execution awaits Project 1 freeze and Project 2 implementation gates.

## Preconditions

- Project 1 freezes representative ecological regimes and their artifact/config identities.
- Observation-frame, historical-state, noise, policy, and learning mechanisms pass unit/property and
  fixed-trajectory verification.
- Profile assignment uses an independent registered RNG stream and is balanced without reference to
  initial position or ecological quality.

## P2-A design

Factor levels:

- radius: `0, 1, 2`;
- Gaussian noise fraction: `0.0, 0.25`;
- delay ticks: `0, 2`;
- policy: `fixed_information_sensitive, tabular_q`.

This gives 24 conditions per frozen Project 1 regime. With three regimes and ten paired seeds, the
planned design contains 720 runs of 500 ticks. The longer horizon than P1-A–D allows a Q-learning
transient but is a project choice, not convergence evidence.

## P2-B design

Profiles:

- restricted: `(radius=0, noise=0.25, delay=2)`;
- enhanced: `(radius=2, noise=0.0, delay=0)`.

Population treatments are all restricted, all enhanced, and a balanced mixed assignment. Both fixed
and Q-learning policies are tested in each of three ecological regimes with ten paired seeds: 180
runs of 500 ticks.

Mixed assignments are generated once per `(ecology, seed)` from the profile-assignment stream and
reused across policy comparisons. Initial positions and material states are identical across treatments.

## Outputs

Every run retains Project 1's full outcome vector plus information coverage, observation error and age,
decision quality, opportunity gaps, exploration, reward, and profile-stratified material outcomes.
Condition summaries preserve raw run rows and matched-seed contrasts.

## Run cap

The canonical plan is 900 runs. Any reduction or expansion requires a versioned design decision,
power/precision rationale, and regenerated provenance before experiment freeze.
