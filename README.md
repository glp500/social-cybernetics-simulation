# Social Cybernetics Sugarscape

A research-first agent-based model of cognitive tools, adaptive behaviour, norm diffusion, and
institutional emergence. The scientific model is specified independently of its Mesa runtime.

The current executable target is a deterministic material control model: renewable spatial resources,
local observation, explicit beliefs and action intents, simultaneous harvest competition, metabolism,
and mortality.

## Quick start

```bash
conda-lock install --name social-cybernetics conda-lock.yml
conda run -n social-cybernetics python -m pip install -e . --no-deps
conda run -n social-cybernetics scs validate --config configs/baseline.yml
conda run -n social-cybernetics scs run --config configs/baseline.yml
```

During development, the `just` recipes wrap the same commands:

```bash
just test
just check
just run
just viz
```

## Architecture

```text
scientific specification
        |
CLI/config/visualisation -> Mesa runtime -> pure domain core
                                      records -> analysis
```

- [Scientific specification](docs/model_specification.md)
- [Software architecture](docs/architecture.md)
- [Model rules](docs/model_rules.md)
- [Assumptions and limitations](docs/assumptions.md)
- [Research roadmap](docs/research_roadmap.md)
- [Architecture decisions](docs/adr/README.md)

## Current scope

Version 0.1 deliberately excludes shocks, adaptive learning, communication networks, norm diffusion,
institutions, exchange, debt, births, and persistent scientific output bundles. Those mechanisms have
dependency-ordered specifications but cannot enter executable source before their verification gate.

## Reproducibility

- Python 3.12 and Mesa 3.5.1 are pinned through the project metadata and Conda lock.
- Every scientific random draw originates from the model-owned generator.
- Identical configuration, seed, and software versions must yield an identical trajectory.
- Generated results are ignored; later experiment versions will store normalised configuration and
  software metadata beside every run.

## License

Apache License 2.0. See [LICENSE](LICENSE).
