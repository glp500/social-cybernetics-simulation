from pathlib import Path

import pytest
from pydantic import ValidationError

from social_cybernetics.project1_experiments import (
    Project1ExperimentSpecification,
    load_project1_design,
)

CANONICAL_PLAN = Path("configs/project-1.yml")
SEEDS = (101, 202, 303, 404, 505, 606, 707, 808, 909, 1010)


def test_canonical_project1_design_has_stable_order_and_exact_run_count() -> None:
    design = load_project1_design(CANONICAL_PLAN)

    assert tuple(group.id for group in design.specification.groups) == (
        "p1-a",
        "p1-b",
        "p1-c",
        "p1-d",
        "p1-e",
    )
    assert len(design.runs) == 140
    assert len(design.batch.runs) == 140
    assert design.runs[0].run_id == "p1-a-homogeneous-seed-101"
    assert design.runs[-1].run_id == "p1-e-correlated-slow-recovery-seed-1010"
    assert all(run.resolved.config.study == "project_1" for run in design.runs)
    assert tuple(run.seed for run in design.runs[:10]) == SEEDS


def test_p1_a_pairs_homogeneous_and_mean_preserving_checkerboard() -> None:
    design = load_project1_design(CANONICAL_PLAN)
    runs = [run for run in design.runs if run.experiment_id == "p1-a"]

    assert len(runs) == 20
    homogeneous = runs[0].resolved.config
    checkerboard = runs[10].resolved.config
    assert homogeneous.seed == checkerboard.seed == 101
    assert homogeneous.duration == checkerboard.duration == 100
    assert homogeneous.agents.count == checkerboard.agents.count == 10
    assert homogeneous.agents.initial_positions == checkerboard.agents.initial_positions
    assert homogeneous.resources.kind == "uniform"
    assert checkerboard.resources.kind == "explicit"
    assert sum(map(sum, checkerboard.resources.capacity)) == 250.0
    assert checkerboard.resources.capacity[2][2] == 10.0


def test_p1_b_is_exact_density_by_mobility_factorial() -> None:
    design = load_project1_design(CANONICAL_PLAN)
    runs = [run for run in design.runs if run.experiment_id == "p1-b" and run.seed == 101]

    assert [
        (
            run.condition_id,
            run.resolved.config.agents.count,
            run.resolved.config.agents.movement_cost,
        )
        for run in runs
    ] == [
        ("n5-cost0", 5, 0.0),
        ("n5-cost05", 5, 0.5),
        ("n20-cost0", 20, 0.0),
        ("n20-cost05", 20, 0.5),
    ]


def test_p1_c_matches_expected_initial_hits_but_not_propagation() -> None:
    design = load_project1_design(CANONICAL_PLAN)
    runs = [run for run in design.runs if run.experiment_id == "p1-c" and run.seed == 101]

    independent, correlated, system = (run.resolved.config for run in runs)
    assert independent.shock.kind == "independent"
    assert independent.shock.event_probability * 25 == 1.0
    assert correlated.shock.kind == "correlated"
    assert correlated.shock.event_probability == 1.0
    assert correlated.shock.spread_probability == 0.5
    assert correlated.shock.max_spread_ticks == 2
    assert system.shock.kind == "system"
    assert system.shock.event_probability * 25 == 1.0
    assert {
        (
            shock.stock_loss_fraction,
            shock.capacity_loss_fraction,
            shock.regeneration_suppression_fraction,
            shock.recovery_ticks,
        )
        for shock in (independent.shock, correlated.shock, system.shock)
    } == {(0.5, 0.25, 0.5, 5)}


def test_p1_d_changes_only_recovery_duration() -> None:
    design = load_project1_design(CANONICAL_PLAN)
    runs = [run for run in design.runs if run.experiment_id == "p1-d" and run.seed == 101]

    fast, slow = (run.resolved.config for run in runs)
    assert fast.shock.kind == slow.shock.kind == "correlated"
    fast_payload = fast.model_dump(mode="json")
    slow_payload = slow.model_dump(mode="json")
    assert fast_payload["shock"].pop("recovery_ticks") == 2
    assert slow_payload["shock"].pop("recovery_ticks") == 10
    assert fast_payload == slow_payload


def test_p1_e_uses_three_frozen_long_horizon_regimes() -> None:
    design = load_project1_design(CANONICAL_PLAN)
    runs = [run for run in design.runs if run.experiment_id == "p1-e" and run.seed == 101]

    assert [run.condition_id for run in runs] == [
        "control",
        "heterogeneous-pressure",
        "correlated-slow-recovery",
    ]
    assert all(run.resolved.config.duration == 1000 for run in runs)
    assert runs[0].resolved.config.shock.kind == "none"
    assert runs[1].resolved.config.agents.count == 20
    assert runs[1].resolved.config.agents.movement_cost == 0.5
    assert runs[1].resolved.config.resources.kind == "explicit"
    assert runs[2].resolved.config.shock.kind == "correlated"
    assert runs[2].resolved.config.shock.recovery_ticks == 10


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"expected_runs": 1}, "expected_runs"),
        ({"max_runs": 3}, "max_runs"),
        ({"seeds": [101, 101]}, "seeds"),
    ],
)
def test_plan_contract_rejects_inconsistent_controls(
    change: dict[str, object], message: str
) -> None:
    valid = {
        "study": "project_1",
        "schema_version": "1.0.0",
        "base_config": "baseline.yml",
        "seeds": [101, 202],
        "expected_runs": 4,
        "max_runs": 4,
        "groups": [
            {
                "id": "p1-a",
                "duration": 100,
                "conditions": [
                    {"id": "one", "agent_count": 1},
                    {"id": "two", "agent_count": 2},
                ],
            }
        ],
    }
    valid.update(change)

    with pytest.raises(ValidationError, match=message):
        Project1ExperimentSpecification.model_validate(valid)


def test_plan_contract_rejects_unstable_or_duplicate_ids() -> None:
    base = {
        "study": "project_1",
        "schema_version": "1.0.0",
        "base_config": "baseline.yml",
        "seeds": [101],
        "expected_runs": 2,
        "max_runs": 2,
        "groups": [
            {
                "id": "P1 A",
                "duration": 100,
                "conditions": [
                    {"id": "same", "agent_count": 1},
                    {"id": "same", "agent_count": 1},
                ],
            }
        ],
    }

    with pytest.raises(ValidationError):
        Project1ExperimentSpecification.model_validate(base)
