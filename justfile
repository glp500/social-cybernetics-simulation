default:
    just --list

install:
    conda-lock install --name social-cybernetics conda-lock.yml
    conda run -n social-cybernetics python -m pip install -e . --no-deps --no-build-isolation

test:
    conda run -n social-cybernetics pytest

coverage:
    conda run -n social-cybernetics pytest --cov=social_cybernetics --cov-report=term-missing --cov-fail-under=90

lint:
    conda run -n social-cybernetics ruff check .

typecheck:
    conda run -n social-cybernetics sh -c 'pyright --venvpath "$(dirname "$CONDA_PREFIX")"'

format:
    conda run -n social-cybernetics ruff format .
    conda run -n social-cybernetics ruff check --fix .

check:
    conda run -n social-cybernetics ruff format --check .
    conda run -n social-cybernetics ruff check .
    conda run -n social-cybernetics sh -c 'pyright --venvpath "$(dirname "$CONDA_PREFIX")"'
    conda run -n social-cybernetics pytest --cov=social_cybernetics --cov-report=term-missing --cov-fail-under=90
    conda run -n social-cybernetics conda-lock lock -f environment.yml -p linux-64 --pypi_to_conda_lookup_file tools/conda-pypi-map.json --check-input-hash 2>&1 | grep -F "Spec hash already locked"

viz:
    PYTHONPATH=src XDG_CACHE_HOME=/tmp/scs-cache MPLCONFIGDIR=/tmp/scs-mpl IPYTHONDIR=/tmp/scs-ipython SOLARA_SESSION_HTTPS_ONLY=false conda run -n social-cybernetics solara run src/social_cybernetics/runtime/mesa/app.py

browser-check:
    conda run -n social-cybernetics node tools/verify_visualization.cjs

run:
    conda run -n social-cybernetics scs run --config configs/baseline.yml

batch output="results/batch-v0.2":
    conda run -n social-cybernetics scs batch --spec configs/batch-v0.2.yml --output {{output}}

sensitivity output="results/sensitivity-v0.2":
    conda run -n social-cybernetics scs sensitivity --spec configs/sensitivity-v0.2.yml --output {{output}}

validate:
    conda run -n social-cybernetics scs validate --config configs/baseline.yml

lock:
    conda run -n social-cybernetics conda-lock lock -f environment.yml -p linux-64 --pypi_to_conda_lookup_file tools/conda-pypi-map.json

obsidian:
    xdg-open "obsidian://open?path=$(pwd)/docs/00-dashboard.md"

literature:
    xdg-open "obsidian://open?path=$(pwd)/docs/literature/literature_matrix.md"

mechanisms:
    xdg-open "obsidian://open?path=$(pwd)/docs/modeling/mechanism_backlog.md"
