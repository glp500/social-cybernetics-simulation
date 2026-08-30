# Shared Ontology

## Material and informational objects

| Term | Definition | First represented |
| --- | --- | --- |
| baseline capacity | undamaged cell-level resource attractor | Project 1 |
| effective capacity | current damaged/recovering resource attractor | Project 1 |
| resource stock | current extractable material in a cell | Project 1 |
| regeneration rate | relaxation fraction toward effective capacity per tick | Project 1 |
| energy | agent viability stock changed by harvest conversion and costs | Project 1 |
| action capacity | the schedule permits one intent per living agent per tick | Project 1, as a rule rather than a mutable stock |
| objective opportunity | environmental resource state relevant to feasible extraction before sensing filters | Project 1 |
| exposure | objective opportunity locally encountered by an agent | Project 1 |
| material extraction | resource physically allocated to an agent during simultaneous resolution | Project 1 |
| shortfall | `max(0, viability_target - energy)` at a recorded point | Project 1 |
| observation | timestamped, framed, possibly noisy/delayed environmental signal | Project 2 |
| belief | decision-facing state constructed from an observation/history | Project 2 |
| privately actionable opportunity | objective opportunity filtered through private sensing and policy | Project 2 |
| sensing profile | complete tuple of observation radius, noise, and delay | Project 2 |
| report | timestamped information sent from one agent to another | Project 3 |
| trust | directional weight on a specific report source | Project 3 |
| socially accessible opportunity | private opportunity extended or altered by received reports | Project 3 |
| information credit | conserved access/accounting token used only in specified circulation regimes | Project 3 |
| obligation | separate claim for a future transfer of existing information credit | Project 3 |

## Outcome vocabulary

| Term | Permitted meaning |
| --- | --- |
| difference | agents or cells have unequal recorded values |
| inequality | a distribution of a named model quantity is unequal |
| persistence | rank or inequality remains related across a stated time lag |
| material advantage | an agent has a higher named material outcome; no ownership relation implied |
| informational advantage | sensing or reports improve a named observation/decision outcome |
| adaptive advantage | a learned policy improves a named outcome relative to a matched control |
| information dependency | removing one source's reports reduces a receiver's effective information |
| gatekeeping potential | concentrated, discretionary access that could constrain another's information |
| resilience | recovery of explicitly named material, security, information, or network measures after shock |

## Reserved vocabulary

The following terms require relations not present in Project 1 and are not synonyms for model
statistics:

- **wealth** requires a defined asset or claim stock with persistence and control;
- **capital** requires an accumulation and production relation, not merely high energy or harvest;
- **class** requires durable social relations of property, production, or control;
- **exploitation** requires an explicit appropriation relation;
- **money** requires monetary functions beyond a conserved experiment token;
- **market** requires an exchange institution, feasible offers, and terms of trade;
- **reciprocity** requires a specified social transfer relation, not merely balanced flows;
- **power** requires demonstrated asymmetric control over another's feasible action or access;
- **metabolic rift** requires historically specific social organization of material exchange.

## State-composition rule

Shared agent state contains only the minimum material/physiological state used by every executable
study. Sensing, learning, network, trust, credit, and obligation state belongs to Project 2 or 3
components. Documentation may reserve a concept; shared code may not pre-allocate it.
