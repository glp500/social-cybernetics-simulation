# Project 2 Validation and Freeze Gates

**Status:** all gates open; implementation is not authorized by the current Project 1 phase.

| Gate | Freeze requirement |
| --- | --- |
| specification | observation frame, historical indexing, belief, fixed policy, Q update, reward, and scheduler equations agree |
| literature | paired evidence covers partial observation, delay/noise, value of information, Q-learning limits, and situated-skill boundaries |
| verification | exact frames, independent noise, no future leakage, delay history, belief isolation, fixed-policy paths, Q updates, and RNG isolation pass |
| sensitivity | learning/channel parameters and stochastic seeds are screened without mixing profile categories into numeric factors |
| experiment | all P2-A/P2-B bundles publish with matched controls and profile-assignment provenance |
| analysis | information, decision, conversion, and material metrics are frozen before headline inference |
| interpretation | every result distinguishes information, adaptation, material conversion, and missing social mechanisms |

## Required invariants

- observation positions stay within the declared radius and source tick;
- delayed observations never read future or mutable state;
- zero noise reproduces objective historical values exactly;
- noise draws do not shift ecology, policy, learning, or assignment streams;
- mixed profile assignment is balanced and independent of position/resource quality;
- belief records never alias observation history;
- Q updates touch exactly one state-action entry and use the specified reward/next-state value;
- fixed-policy and learning controls share ecology and sensing draws under paired seeds;
- material conservation and all Project 1 invariants remain unchanged.

## Integration ladder

- I0: radius zero, zero noise/delay, fixed policy reproduces the corresponding Project 1 trajectory;
- I1: asymmetric historical fixture proves spatial orientation and delay source tick;
- I2: noise-only sham confirms stream isolation and recorded errors;
- I3: hand-calculated Q transition matches the update equation;
- I4: mixed profiles start from identical material conditions and balanced randomized assignments;
- I5: artifact-only analysis reconstructs the full information-to-material conversion chain.
