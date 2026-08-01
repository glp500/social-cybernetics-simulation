default:
    just --list

install:
    python -m pip install -e .

test:
    pytest

lint:
    ruff check .
    pyright

format:
    ruff format .
    ruff check --fix .

lab:
    jupyter lab

viz:
    solara run scripts/launch_viz.py

run:
    python scripts/run_baseline.py --config configs/baseline.yml

lock:
    conda-lock -f environment.yml -p linux-64

clean:
    find . -type d -name "__pycache__" -prune -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
