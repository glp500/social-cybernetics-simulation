# Social Cybernetics Sugarscape

A research-first agent-based modelling programme that separates three transformations of material
opportunity:

1. objective ecological opportunity;
2. privately perceived and adaptively actionable opportunity;
3. socially accessible opportunity.

Project 1 is fully implemented and frozen. Projects 2 and 3 are fully specified but intentionally
non-executable until their own evidence gates open. The active programme does not model institutions,
governance, firms, markets, class, demographic reproduction, or LLM agents.

## Project status

| Project | Scientific specification | Implementation | Evidence gates |
| --- | --- | --- | --- |
| Project 1 — ecology, provisioning, inequality | complete | complete | 7/7 frozen |
| Project 2 — private perception and action | complete | not started | 0/7 frozen |
| Project 3 — social information and circulation | complete | not started | 0/7 frozen |

Project 1 includes heterogeneous renewable landscapes; a literal local harvest-or-move policy;
simultaneous competition; metabolism and mortality; recoverable independent, correlated, and system
shocks; registered RNG streams; immutable evidence; atomic Parquet/NetCDF run and batch bundles;
Morris sensitivity; artifact-only analysis; and the executed 140-run P1-A–E experiment.

## Quick start

```bash
conda-lock install --name social-cybernetics conda-lock.yml
conda run -n social-cybernetics python -m pip install -e . --no-deps --no-build-isolation
conda run -n social-cybernetics scs validate --config configs/baseline.yml
conda run -n social-cybernetics scs run --config configs/baseline.yml
```

Run the complete Project 1 design and artifact-only analysis only when their full cost is intended:

```bash
mkdir -p results
conda run -n social-cybernetics scs project1-run \
  --spec configs/project-1.yml --output results/project1-batch
conda run -n social-cybernetics scs project1-analyze \
  --spec configs/project-1.yml \
  --batch results/project1-batch \
  --output results/project1-analysis
```

Output destinations must not exist. Scientific directories are written into unique sibling staging
directories, validated completely, and atomically published without overwrite. Generated `results/`
remain local and are ignored by Git.

Useful development commands:

```bash
just check
just run
just project1
just project1-analysis
just viz
just browser-check
```

## Architecture

```text
study specification
      |
CLI/config/visualization -> thin Mesa runtime -> pure Python domain
                                      |
                              immutable records
                                      |
                              artifact-only analysis
```

The domain never imports Mesa, Pydantic, pandas, Solara, or visualization code. Mesa cells own
position and property-layer arrays; typed domain records own non-spatial state and evidence. Analysis
never steps or mutates a live model.

## Scientific authority

- [Programme overview](docs/programme/overview.md)
- [Canonical ODD+D specification](docs/model_specification.md)
- [Project 1 package](docs/studies/project_1/specification.md)
- [Project 1 frozen evidence](docs/studies/project_1/validation.md)
- [Project 1 interpretation register](docs/studies/project_1/interpretation.md)
- [Project 2 package](docs/studies/project_2/specification.md)
- [Project 3 package](docs/studies/project_3/specification.md)
- [Software architecture](docs/architecture.md)
- [Research roadmap](docs/research_roadmap.md)
- [Implementation plan and checklist](tasks/plan.md)

## Reproducibility

- Python 3.12 and Mesa 3.5.1 are pinned through project metadata and the Linux-64 Conda lock.
- Every scientific random draw comes from a recorded model-owned substream.
- Run bundles retain normalized configuration, software/RNG provenance, immutable Parquet records,
  and tick-zero through final-tick NetCDF ecology.
- Batch bundles retain ordered resolved configurations, hashes, indexes, and recursively validated
  children.
- Project 1 analysis cross-validates 140 raw outcomes, 448 condition summaries, and 4,480 paired
  contrasts between JSON and explicit Arrow schemas.
- The final gate passed 263 tests at 90.83% branch-aware coverage, Ruff, Pyright, lock consistency, a
  clean lock installation, baseline byte regression, and isolated browser stepping.

The literal Project 1 policy intentionally has no energy cap. Model units and all experiment values
remain abstract project choices until an empirical calibration study exists.

## License

Apache License 2.0. See [LICENSE](LICENSE).
