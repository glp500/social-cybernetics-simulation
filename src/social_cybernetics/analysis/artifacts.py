"""Read validated published artifacts into pure Project 1 analysis contracts."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
from netCDF4 import Dataset

from social_cybernetics.domain import (
    ActionKind,
    AgentSnapshot,
    AgentTransitionRecord,
    CohortRecord,
)
from social_cybernetics.persistence import validate_run_bundle

from .project1_outcome import Project1Outcome, calculate_project1_outcome


def _read_transitions(bundle: Path) -> tuple[AgentTransitionRecord, ...]:
    rows = pq.read_table(bundle / "tables/agent_transitions.parquet").to_pylist()
    return tuple(
        AgentTransitionRecord(
            tick=row["tick"],
            agent_id=row["agent_id"],
            origin=(row["origin_x"], row["origin_y"]),
            observed_stock=row["observed_stock"],
            believed_stock=row["believed_stock"],
            intent_kind=ActionKind(row["intent_kind"]),
            requested_amount=row["requested_amount"],
            intended_destination=(
                (row["intended_destination_x"], row["intended_destination_y"])
                if row["intended_destination_x"] is not None
                else None
            ),
            gate_allowed=row["gate_allowed"],
            harvested=row["harvested"],
            moved=row["moved"],
            final_position=(row["final_position_x"], row["final_position_y"]),
            energy_before=row["energy_before"],
            energy_after=row["energy_after"],
            shortfall=row["shortfall"],
            died=row["died"],
        )
        for row in rows
    )


def _read_cohort(bundle: Path) -> tuple[CohortRecord, ...]:
    rows = pq.read_table(bundle / "tables/cohort.parquet").to_pylist()
    return tuple(
        CohortRecord(
            row["tick"],
            AgentSnapshot(
                tick=row["tick"],
                agent_id=row["agent_id"],
                position=(row["position_x"], row["position_y"]),
                energy=row["energy"],
                alive=row["alive"],
            ),
        )
        for row in rows
    )


def analyze_run_bundle(bundle: Path) -> Project1Outcome:
    """Validate and analyze one published Project 1 run without model access."""

    bundle = Path(bundle)
    manifest = validate_run_bundle(bundle)
    transitions = _read_transitions(bundle)
    cohort = _read_cohort(bundle)
    with Dataset(bundle / "spatial.nc", "r") as spatial:
        return calculate_project1_outcome(
            seed=manifest["seed"],
            completed_ticks=manifest["completed_ticks"],
            transitions=transitions,
            cohort=cohort,
            resource_stock=spatial.variables["resource_stock"][:],
            effective_capacity=spatial.variables["effective_capacity"][:],
            effective_regeneration=spatial.variables["effective_regeneration"][:],
            recovery_remaining=spatial.variables["recovery_remaining"][:],
            baseline_capacity=spatial.variables["baseline_capacity"][:],
            baseline_regeneration=spatial.variables["baseline_regeneration"][:],
        )
