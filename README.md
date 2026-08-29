# Social Cybernetics Sugarscape

A research-first agent-based model of cognitive tools, adaptive behaviour, norm diffusion, and
institutional emergence. The scientific model is specified independently of its Mesa runtime.

The executable target now includes the verified deterministic material control plus the v0.2
ecological core: explicit heterogeneous landscapes, recoverable independent/correlated/system shocks,
normalized event evidence, local observation, simultaneous harvest competition, metabolism, and
mortality. It can also publish validated provenance-rich run bundles with Parquet records and complete
streamed NetCDF spatial history and deterministic sequential batches. Sensitivity workflows remain a
later v0.2 slice.

## Quick start

```bash
conda-lock install --name social-cybernetics conda-lock.yml
conda run -n social-cybernetics python -m pip install -e . --no-deps --no-build-isolation
conda run -n social-cybernetics playwright install chromium
conda run -n social-cybernetics scs validate --config configs/baseline.yml
conda run -n social-cybernetics scs run --config configs/baseline.yml
mkdir -p results
conda run -n social-cybernetics scs run --config configs/baseline.yml --output results/run-001
conda run -n social-cybernetics scs batch --spec configs/batch-v0.2.yml --output results/batch-v0.2
```

Output directories must not already exist. Run and batch bundles are validated in hidden sibling
staging directories and atomically published only when complete; commands never overwrite prior
results. A batch continues after individual run failures, publishes their typed index records without
partial child bundles, and exits 1 if any run failed. Generated `results/` remain local and are
ignored by Git.

After `conda activate social-cybernetics`, the `just` recipes wrap the same commands:

```bash
just test
just check
just run
just batch
just viz
just browser-check
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

Version 0.1 remains the no-shock control. Version 0.2 implements heterogeneous landscapes and
recoverable ecological shocks, but still excludes adaptive learning, communication networks, norm
diffusion, institutions, exchange, debt, and births. The literal policy intentionally has no energy
cap, so a surviving agent's energy may grow without bound.

Version 0.2 is in implementation. Its domain, runtime shock, persistent-output, and deterministic
batch slices are complete. Sensing, policy, gating, competition, and physiology stay fixed; seeded
sensitivity design is next. See the active
[implementation plan](tasks/plan.md) and [task list](tasks/todo.md).

The debugging page is exercised in isolated Chromium and captured in the
[version 0.1 reference screenshot](docs/solara-v0.1.png). Installing Chromium is a one-time local step;
the browser binary is not stored in the repository.

## Reproducibility

- Python 3.12, Mesa 3.5.1, Solara 1.61, and compatible Vue 2 widgets are pinned through the project
  metadata and Conda lock.
- Every scientific random draw originates from a recorded model-owned substream.
- Identical configuration, seed, stream registry, and software versions must yield an identical
  trajectory.
- Generated results are ignored. Each published bundle stores normalized configuration (including
  realized explicit landscapes), seed and RNG registry, software metadata, summary, and immutable
  record tables, plus tick-zero and every completed tick of ecological spatial state.
- Each published batch retains its normalized base, explicit overrides, complete resolved
  configurations, configuration hashes, ordered JSON/Parquet indexes, and successful child bundles.

## License

Apache License 2.0. See [LICENSE](LICENSE).
