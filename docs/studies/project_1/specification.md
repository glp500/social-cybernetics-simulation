# Project 1 Specification: Ecology, Provisioning, and Inequality

**Status:** mechanics verified from the pre-refactor v0.2 release; analytical and freeze work active.

## Purpose

Project 1 asks which unequal material outcomes, subsistence risks, and persistent advantages can arise
from environmental opportunity, mobility, simultaneous competition, disturbance, and recovery alone.
It establishes the ecological control against which Projects 2 and 3 later identify informational and
relational transformations.

## Entities and scales

- **World:** rectangular Von Neumann grid, toroidal when configured, with unlimited cell occupancy.
- **Cell:** baseline/effective resource capacity, resource stock, baseline/effective regeneration, and
  recovery clock.
- **Agent:** immutable domain identity, energy, and alive status; position is authoritative in Mesa's
  cell.
- **Shock event:** stable run-local identity, scope, timing, footprint, propagation state, damage, and
  termination evidence.
- **Time:** one abstract discrete tick. Units are dimensionless.

## Stocks and flows

Material stocks remain separate:

- resource stock is extractable material;
- baseline capacity is the undamaged attractor;
- effective capacity is the temporarily damaged/recovering attractor;
- energy is the agent viability stock.

Action capacity is a scheduling constraint—one intent per living agent per tick—not a mutable agent
stock. Project 1 contains no holdings, debt, information capability, trust, credit, or obligation.

## Authoritative scheduler

Tick zero records the initialized cohort and ecology. Every tick then executes:

1. recovery;
2. regeneration;
3. shock;
4. exact local observation;
5. copied belief;
6. fixed literal intent;
7. allow-all gate;
8. simultaneous physical resolution;
9. metabolism;
10. mortality;
11. measurement.

This order is a scientific contract. Stages that are identity-like controls remain visible.

## Resource dynamics

For cell `c`, after recovery advances, stock relaxes toward current effective capacity:

```text
S[c,t+1] = S[c,t] + r_eff[c,t] * (K_eff[c,t] - S[c,t])
```

The result is bounded by baseline capacity, not immediately by damaged effective capacity. Stock may
temporarily exceed `K_eff` and decline gradually. Heterogeneous landscapes explicitly provide
baseline capacity and initial stock matrices indexed `(x, y)`.

## Shock dynamics

Every enabled shock explicitly provides initiation probability, stock-loss fraction,
capacity-loss fraction, regeneration-suppression fraction, and recovery ticks. Correlated shocks also
provide edge transmission probability and outward spread rounds.

- **independent:** one Bernoulli draw per cell per tick; each success damages that cell;
- **correlated:** one Bernoulli draw per tick starts a concurrent synchronous wavefront;
- **system:** one Bernoulli draw per tick damages every cell simultaneously.

Simultaneous hits compound against the cell's current effective state and restart one linear,
cell-local recovery trajectory. A cell reaches baseline exactly `recovery_ticks` after its most recent
hit. Damage occurs after regeneration and receives no same-tick recovery or compensating regrowth.

## Agent policy and physical resolution

An agent observes exact current stock in its cell. Belief copies that scalar. If believed local stock
meets the threshold, the agent requests up to harvest capacity; otherwise it moves uniformly to a Von
Neumann neighbour using the model-owned policy stream. There is no rest branch or energy cap.

Harvest requests at a cell resolve simultaneously. If requests exceed stock, allocation is
proportional to requested amounts. Movement has no collision rule. Agent energy changes by:

```text
E_after = E_before + efficiency * harvested - basal_cost - moved * movement_cost
```

If this is non-positive, energy is clamped to zero, the agent dies, its Mesa wrapper is removed, and
its state remains in cohort and event evidence.

## Randomness

All draws use model-owned NumPy generators created from permanent `SeedSequence` spawn keys:

- policy/movement `(1,)`;
- shock initiation `(2, 1)`;
- shock location `(2, 2)`;
- shock transmission `(2, 3)`.

Global random calls are prohibited. Changing propagation settings cannot shift initiation or location
draw sequences.

## Evidence contract

Project 1 records:

- tick-zero and per-completed-tick cohort snapshots;
- one immutable transition per active agent-tick containing exposure, intent, resolution, energy,
  shortfall, movement, and mortality;
- per-tick model totals;
- normalized agent events, shock snapshots, exposures, and damage applications;
- complete `(tick, x, y)` resource, effective capacity, effective regeneration, and recovery history;
- static baseline capacity and regeneration;
- normalized configuration, RNG/software provenance, and artifact digests.

Derived metrics are not runtime state. They are calculated from immutable records under the
[analysis plan](analysis_plan.md).

## Configuration boundary

`Study01Config` is the canonical executable contract. It supports only Project 1 variants. A temporary
`SimulationConfig` compatibility alias and explicit legacy v0.1/v0.2 normalization preserve old
fixtures while canonical YAML migrates to the study identifier. Project 2 and 3 configs are not
accepted by the Project 1 runner.

## Outputs

The CLI summary retains the stable baseline fields. Persistent runs add full Project 1 evidence.
Experiment analysis reports a vector of harvest, survival, unmet need, downside risk, distribution,
persistence, and ecological recovery. It emits no composite welfare score.

## Exclusions

No learning, social reports, network, diffusion, rule choice, enforcement, institution, exchange,
material holding, debt, birth, inheritance, firm, wage, ownership, or demographic process is present.
