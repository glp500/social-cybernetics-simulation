# Project 1 Experiments

## Design principles

- all conditions are complete validated `Study01Config` objects;
- ten paired model seeds are used: `101, 202, 303, 404, 505, 606, 707, 808, 909, 1010`;
- P1-A–D run 100 ticks; P1-E runs 1,000 ticks;
- initial positions and material distributions are identical within each contrast;
- parameter and seed variation remain separate columns in published evidence;
- numeric values are project choices, not empirical calibration;
- analysis reads only validated published artifacts.

## Shared 5×5 fixture

The world is a Von Neumann torus with unlimited occupancy. Uniform capacity and initial stock are
`10`, regeneration is `0.1`, initial energy/target are `10`, basal cost is `1`, movement cost defaults
to `0.25`, harvest capacity is `2`, threshold is `1`, and efficiency is `1`. The fixed literal policy
and allow-all gate never vary.

The deterministic placement lists are prefixes of row-major `(x, y)` coordinates. Placement is held
fixed across paired conditions and seeds. It is not randomized into more favourable ecological cells.

## P1-A — Ecological heterogeneity

Two conditions × ten seeds = 20 runs:

- `homogeneous`: capacity/initial stock `10` in every cell;
- `checkerboard`: alternating capacity/initial stock `5` and `15`, with the centre cell set to `10`
  so total capacity remains exactly `250`.

Both use 10 agents, movement cost `0.25`, and no shock.

## P1-B — Population pressure and mobility

Four conditions × ten seeds = 40 runs:

- agent count `5` or `20`;
- movement cost `0.0` or `0.5`.

The landscape is homogeneous and shocks are disabled. The design changes movement cost, not the
number of moves permitted.

## P1-C — Disturbance structure

Three conditions × ten seeds = 30 runs. All use 10 agents and the homogeneous landscape. Damage is
stock loss `0.5`, capacity loss `0.25`, regeneration suppression `0.5`, and recovery `5` ticks.

For 25 cells, expected initially affected cells per tick are matched at one:

```text
independent: 25 * event_probability(0.04) = 1
correlated:  event_probability(1.0) * one epicentre = 1
system:      event_probability(0.04) * 25 cells = 1
```

The correlated condition uses spread probability `0.5` and two outward rounds. Propagated hits are
not matched; realized affected-cell exposure and damage are reported outcomes.

## P1-D — Recovery speed

Two conditions × ten seeds = 20 runs. Both use the P1-C correlated shock with event probability
`0.2`, spread probability `0.5`, and two outward rounds. Only recovery changes: `2` versus `10` ticks.

## P1-E — Long-horizon persistence

Three conditions × ten seeds = 30 runs:

- `control`: 10 agents, homogeneous landscape, no shock;
- `heterogeneous_pressure`: 20 agents, checkerboard landscape, movement cost `0.5`, no shock;
- `correlated_slow_recovery`: 10 agents, homogeneous landscape, P1-D shock with recovery `10`.

These regimes are selected a priori for mechanical contrast. The experiment changes only duration
relative to its corresponding short-run mechanism; it adds no state or behaviour.

## Run count and cap

The canonical Project 1 experiment contains 140 runs: 110 at 100 ticks and 30 at 1,000 ticks. The
loader refuses expansion beyond this declared cap unless the plan schema is versioned and reviewed.

## Outputs and comparisons

Each run retains its full bundle. The aggregate analysis publishes one row per run with raw outcomes,
then condition-level descriptive statistics and paired differences. Confidence intervals, if added,
must retain the seed block and cannot treat ticks or agents as independent experimental replicates.
