default:
    just --list

install:
    conda-lock install --name social-cybernetics conda-lock.yml
    conda run -n social-cybernetics python -m pip install -e . --no-deps

test:
    conda run -n social-cybernetics pytest

coverage:
    conda run -n social-cybernetics pytest --cov=social_cybernetics --cov-report=term-missing --cov-fail-under=90

lint:
    conda run -n social-cybernetics ruff check .

typecheck:
    conda run -n social-cybernetics pyright

format:
    conda run -n social-cybernetics ruff format .
    conda run -n social-cybernetics ruff check --fix .

check:
    conda run -n social-cybernetics ruff format --check .
    conda run -n social-cybernetics ruff check .
    conda run -n social-cybernetics pyright
    conda run -n social-cybernetics pytest --cov=social_cybernetics --cov-report=term-missing --cov-fail-under=90

viz:
    conda run -n social-cybernetics solara run src/social_cybernetics/runtime/mesa/app.py

run:
    conda run -n social-cybernetics scs run --config configs/baseline.yml

validate:
    conda run -n social-cybernetics scs validate --config configs/baseline.yml

lock:
    conda-lock -f environment.yml -p linux-64

obsidian:
    xdg-open "obsidian://open?path=$(pwd)/docs/00-dashboard.md"

literature:
    xdg-open "obsidian://open?path=$(pwd)/docs/literature/literature_matrix.md"

mechanisms:
    xdg-open "obsidian://open?path=$(pwd)/docs/modeling/mechanism_backlog.md"
