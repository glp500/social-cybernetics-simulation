# Assumptions, Limitations, and Protected Extensions

## Current assumptions

- Units are abstract and dimensionless.
- The default torus removes boundary-created inequality from the control condition.
- Cells permit unlimited co-location so movement conflict does not contaminate resource competition.
- Renewable resources relax toward capacity and recover from zero.
- Harvested resources are consumed immediately; stored holdings do not yet exist.
- The literal control policy values every harvest opportunity and can accumulate energy without bound.
- The baseline has perfect local sensing, a copied belief, one principal action, no shocks, and no
  institutional restriction.
- The initial cohort is fixed. Version 0.1 has mortality but no births or migration.
- Welfare is reported as multiple observables rather than a composite score.

## Known limitations

- Parameter values are verification fixtures, not empirical estimates.
- Direct resource-to-energy conversion omits storage, spoilage, and consumption choice.
- A current-cell observation gives cognitive boundaries a software form but does not yet model
  perceptual error.
- Multi-occupancy differs from classic single-occupancy Sugarscape.
- Regime clustering is exploratory and must be accompanied by continuous features and stability
  analysis.
- Governance categories initially describe norm diffusion rather than formal authority delegation.

## Protected extensions from early design work

The source drafts also proposed ideas intentionally excluded from version 0.1:

- separate food and material/tool resources;
- friction and resource-specific renewal/extraction time;
- physical tools that alter movement or extraction productivity;
- observation and action radii, signal/noise, and delayed feedback;
- communication and control actions with different spatial radii;
- internal hunger/health signals and external embodied action systems;
- social cooperation, exploitation, labour, trade, organisations, and institutions;
- information compression as a theoretical account of cognition.

These ideas are not rejected. They remain protected from entering the control model until a versioned
hypothesis, literature basis, state variables, interaction rule, and verification test exist.

## Boundaries for contributors

### Always

- update the specification before changing scientific semantics;
- validate external configuration once at the boundary;
- run focused tests and the full quality gate;
- record seeds, versions, and normalised configuration for experiment-producing versions.

### Ask first

- add or remove a scientific mechanism;
- change tick ordering or an accounting identity;
- change dependency, lockfile, CI, or output schema policy;
- redefine an outcome as welfare or introduce empirical units.

### Never

- use global randomness in scientific code;
- let agents mutate environment state directly;
- remove failing scientific tests to accept changed behaviour;
- commit secrets, generated results, caches, or local Obsidian plugin data.

