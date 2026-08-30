# Project 3 Specification: Social Information and Circulation

**Status:** specified; not implemented or executable.

## Purpose

Project 3 asks how realized communication ties transform private adaptation into socially accessible
opportunity, and whether trust, rewiring, capability diffusion, and bounded circulation rules equalize
or concentrate informational advantage and dependency.

## Network and reports

The canonical initial network is an undirected ring lattice of degree four over canonical agent order;
reports and trust are directional. A report records sender, receiver, source tick, send tick, source
position, perceived stock content, both sensing profiles, trust before/after, circulation regime,
sender cost, credit transfer, and optional obligation ID.

In P3-A–C, each agent sends its latest highest-stock private observation to every current neighbour
once per tick after private belief formation. Social belief fuses private and received values position
by position using private weight `1` and report weights equal to directional trust. Source tick is
preserved; no report becomes current merely because it arrives now.

## Directional trust and rewiring

Trust starts at `0.5`. A report is evaluated when the receiver later directly observes its reported
position within five ticks. Accuracy is `1 - normalized_absolute_error`, clamped to `[0,1]`.

```text
trust_next = clip((1 - decay) * trust + learning_rate * (accuracy - 0.5), 0, 1)
```

Project choices are learning rate `0.2`, per-tick unused decay `0.01`, and rewiring threshold `0.2`.
At most one outgoing relation per agent-tick is rewired: the lowest-trust relation below threshold is
removed and a non-neighbour agent currently within Manhattan distance two is selected uniformly from
canonical candidates. If no candidate exists, no edge is added. Network draws use a dedicated stream.

The fixed-network control records evaluations but holds trust weights and topology fixed.

## Sensing-profile diffusion

The complete profile `(radius, noise, delay)` diffuses; components never mix independently.

- **no diffusion:** profiles remain initial endowments;
- **simple:** one exposure to an enhanced source causes deterministic adoption at the next diffusion
  stage;
- **reinforced:** adoption requires exposures from at least two distinct enhanced sources within a
  five-tick window.

Adoption is retained. P3-C begins with the balanced randomized restricted/enhanced assignment frozen
in Project 2. Diffusion does not change policy or material productivity.

## Circulation regimes

P3-D holds report content, network, trust, and sender communication cost constant except where the
regime definition requires otherwise. One receiver request to one selected source can be fulfilled per
agent-tick. Sender cost is `C_comm=0.5` energy in D1–D3 and is applied once on transmission.

- **D0 unconditional sharing:** sender cost `0`, no transfer, no obligation.
- **D1 costly contribution:** sender cost `0.5`, no transfer, no obligation.
- **D2 immediate accounted exchange:** same sender cost; receiver transfers one existing information
  credit to sender at transmission or receives no report.
- **D3 deferred obligation:** same sender cost; if an immediate credit is unavailable, the report is
  delivered and a one-credit claim due after five ticks is created.

Every agent begins P3-D with two information credits. Credits are conserved in D2/D3. Creating,
settling, or defaulting on an obligation never creates or destroys credits: settlement transfers one
existing credit; default closes the claim. Default blocks only future deferred access from that
creditor to that debtor.

There is no interest, bargaining, collateral, refinancing, claim resale, inheritance, punishment, or
material transfer.

## State composition and scheduling

`Study03Config` composes a frozen `Study02Config` with network, trust, diffusion, and circulation
variants. Project 3 state components contain realized ties, directional trust, report history,
diffusion exposure/adoption, credit balances, and obligation ledgers only when used. Shared material
agent state is unchanged.

The future scheduler must visibly place report creation, social belief fusion, action, trust feedback,
rewiring, diffusion, circulation accounting, and measurement. Exact ordering is a specification-freeze
decision before code.

## Exclusions

No material exchange, money, prices, firms, wages, ownership, enforcement, institution, governance,
birth, inheritance, interest, collateral, debt market, or LLM/neural policy is present.
