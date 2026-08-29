---
type: literature-note
citekey: mesoudi2011PayoffBiasedLearning
title: Payoff-biased social learning and complex diffusion
authors: McElreath et al.; Mesoudi; Centola; Macy
year: 2011
status: reviewed
model_family:
  - cultural-evolution
  - network-diffusion
mechanisms:
  - payoff-biased imitation
  - repeated-exposure adoption
implementation_links:
  - docs/model_specification.md
tags:
  - literature
  - social-learning
  - diffusion
---

# Payoff-biased social learning and complex diffusion

## Citations

- McElreath, R., Bell, A. V., Efferson, C., Lubell, M., Richerson, P. J., & Waring, T. (2008).
  Beyond existence and aiming outside the laboratory: estimating frequency-dependent and
  pay-off-biased social learning strategies. *Philosophical Transactions of the Royal Society B,
  363*, 3515–3528. <https://doi.org/10.1098/rstb.2008.0131>
- Mesoudi, A. (2011). An experimental comparison of human social learning strategies:
  payoff-biased social learning is adaptive but underused. *Evolution and Human Behavior, 32*,
  334–342. <https://doi.org/10.1016/j.evolhumbehav.2010.12.001>
- Centola, D., & Macy, M. (2007). Complex contagions and the weakness of long ties. *American
  Journal of Sociology, 113*, 702–734. <https://doi.org/10.1086/521848>

## Why this belongs

The main causal contribution depends on distinguishing private reinforcement, social learning, and
norm diffusion. These papers provide primary theoretical and experimental support for selective
copying and for adoption processes that require social reinforcement rather than one contact.

## Supporting evidence

McElreath et al. formulate payoff- and frequency-biased social-learning strategies and emphasize
estimating their use rather than assuming undifferentiated copying. Mesoudi's experiment finds that
payoff-biased copying can improve task performance, particularly on a multimodal task landscape.
Centola and Macy show theoretically that adoption requiring multiple affirmations behaves
differently from simple contagion and depends on network bridge width.

## Counterevidence and boundary conditions

Mesoudi also finds payoff-biased learning was used less than predicted, and its advantage depended
on task structure. Centola and Macy's multiple-source affirmation is not the same as repeated
exposure to one teacher. Neither source establishes that tools and governance rules share one
diffusion equation. Environmental change can also alter which social-learning rule is advantageous.

## Justified commitment

The model may compare individual learning, payoff-biased pairwise imitation, and an exposure-based
capability acquisition process as separate mechanisms. Exposure histories and observed payoffs must
be recorded so their effects can be distinguished.

## Project choices, not literature calibration

- proficiency increment `0.2`, adoption threshold `1.0`, and learning cost `0.5`;
- whether repeated exposure from one source counts the same as affirmation from multiple sources;
- pair selection, payoff window, imitation probability, and mutation/noise;
- the four-rule institutional vocabulary and retention duration.

The source-count question must be resolved before tool diffusion is implemented.

## Verification target

- [ ] private learning and social exposure are separately attributable in event records
- [ ] payoff-biased imitation probabilities are monotone in the declared payoff difference
- [ ] exposure order and source identity follow the selected diffusion design
- [ ] fixed-policy and non-diffusion controls remain available

