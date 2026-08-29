# Mechanism Backlog

## Candidate mechanisms from literature

| Mechanism | Source citekey | Model family | Implementation target | Status |
|---|---|---|---|---|
| Relaxation resource regrowth | @kremerHerman2024ReplacingSugarscape | ABM | domain/ecology.py | verified v0.1 |
| Explicit heterogeneous landscape | @kremerHerman2024ReplacingSugarscape | ABM | config.py + domain/ecology.py | verified v0.2 |
| Independent/correlated/system shocks | @turnerEtAl1989LandscapeDisturbance; @massieEtAl2015EnhancedMoran | disturbance ecology | domain/ecology.py | verified v0.2 core/runtime |
| Gini inequality | @epstein1996GrowingArtificialSocieties | ABM | metrics.py | verified v0.1 |
| Direct observation and copied belief | project specification | ABM | domain/cognition.py | verified v0.1 |
| Simultaneous proportional harvest | project specification | ABM | domain/actions.py | verified v0.1 |
| Tabular Q-learning | @watkinsDayan1992QLearning | reinforcement learning | future policy module | evidence reviewed; design pending |
| Repeated-exposure tool diffusion | @centolaMacy2007ComplexContagions | network diffusion | future capability module | evidence reviewed; source-count design pending |
| Payoff-biased norm imitation | @mcElreathEtAl2008SocialLearning; @mesoudi2011PayoffBiasedLearning | cultural evolution | future norms module | evidence reviewed; design pending |
| Information-value trust rewiring | @holmeNewman2006Coevolution; @bendtsenEtAl2016ExpertGame | network communication | future network module | adjacent evidence reviewed; equation evidence gap |
| Costly cell-local enforcement | @fehrGaechter2002AltruisticPunishment; @dreberEtAl2008WinnersDontPunish | experimental economics | future enforcement module | paired evidence reviewed; design pending |
| Multi-scope nested governance | @ostrom2010PolycentricGovernance; @ostrom2012NestedExternalities | institutional analysis | future norms/analysis modules | evidence reviewed; operationalization pending |
| Gaussian-mixture regime discovery | @fraleyRaftery2002ModelBasedClustering; @hennig2007ClusterStability | statistical analysis | future analysis module | paired evidence reviewed; protocol pending |
| Local alignment + noise | @vicsek1995NovelType | Statistical physics | protected extension | speculative |
| DeGroot influence | @degroot1974ReachingConsensus | Network communication | protected extension | speculative |

## Rule

A mechanism cannot enter `src/` until it has:
- one literature note
- one sentence explaining why it belongs
- one testable implementation target

Each reviewed note must distinguish supporting evidence, counterevidence or boundary conditions,
the justified model commitment, and uncalibrated project choices.

Roadmap status alone does not authorize executable code. The active task must also have its required
evidence, specification semantics, and verification target.
