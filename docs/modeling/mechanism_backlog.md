# Mechanism Backlog

## Candidate mechanisms from literature

| Mechanism | Source citekey | Model family | Implementation target | Status |
|---|---|---|---|---|
| Relaxation resource regrowth | @kremerHerman2024ReplacingSugarscape | ABM | domain/ecology.py | specified |
| Gini inequality | @epstein1996GrowingArtificialSocieties | ABM | metrics.py | started |
| Direct observation and copied belief | project specification | ABM | domain/cognition.py | specified |
| Simultaneous proportional harvest | project specification | ABM | domain/actions.py | specified |
| Tabular Q-learning | literature note required | ABM | future policy module | roadmap |
| Payoff-biased norm imitation | literature note required | cultural evolution | future norms module | roadmap |
| Information-value trust rewiring | literature note required | network communication | future network module | roadmap |
| Local alignment + noise | @vicsek1995NovelType | Statistical physics | protected extension | speculative |
| DeGroot influence | @degroot1974ReachingConsensus | Network communication | protected extension | speculative |

## Rule

A mechanism cannot enter `src/` until it has:
- one literature note
- one sentence explaining why it belongs
- one testable implementation target

Roadmap status means specified but not authorised for the current executable version.
