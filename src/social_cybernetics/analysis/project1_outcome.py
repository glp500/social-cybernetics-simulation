"""Assembly of the non-composite Project 1 outcome vector."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from numpy.typing import ArrayLike

from social_cybernetics.domain import AgentTransitionRecord, CohortRecord

from .project1 import SubsistenceSecurity, calculate_subsistence_security
from .project1_distribution import (
    DistributionMetrics,
    PersistenceMetrics,
    calculate_distribution,
    calculate_persistence,
)
from .project1_ecology import EcologyMetrics, calculate_ecology


@dataclass(frozen=True, slots=True)
class Project1Outcome:
    seed: int
    completed_ticks: int
    cohort_size: int
    aggregate_harvest: float
    survival_fraction: float
    mean_unmet_need: float
    subsistence: SubsistenceSecurity
    distribution: DistributionMetrics
    persistence: PersistenceMetrics
    ecology: EcologyMetrics

    def as_payload(self) -> dict[str, Any]:
        return {"schema_version": "scs-project1-outcome/v1.0.0", **asdict(self)}


def calculate_project1_outcome(
    *,
    seed: int,
    completed_ticks: int,
    transitions: tuple[AgentTransitionRecord, ...],
    cohort: tuple[CohortRecord, ...],
    resource_stock: ArrayLike,
    effective_capacity: ArrayLike,
    effective_regeneration: ArrayLike,
    recovery_remaining: ArrayLike,
    baseline_capacity: ArrayLike,
    baseline_regeneration: ArrayLike,
) -> Project1Outcome:
    """Assemble material, security, distribution, persistence, and ecology outcomes."""

    cohort_size = sum(record.tick == 0 for record in cohort)
    final_alive = sum(record.tick == completed_ticks and record.snapshot.alive for record in cohort)
    aggregate_harvest = math.fsum(record.harvested for record in transitions)
    cumulative_unmet_need = math.fsum(record.shortfall for record in transitions)
    return Project1Outcome(
        seed=seed,
        completed_ticks=completed_ticks,
        cohort_size=cohort_size,
        aggregate_harvest=aggregate_harvest,
        survival_fraction=final_alive / cohort_size if cohort_size else 0.0,
        mean_unmet_need=cumulative_unmet_need / cohort_size if cohort_size else 0.0,
        subsistence=calculate_subsistence_security(transitions, completed_ticks=completed_ticks),
        distribution=calculate_distribution(transitions, cohort, completed_ticks=completed_ticks),
        persistence=calculate_persistence(transitions, cohort, completed_ticks=completed_ticks),
        ecology=calculate_ecology(
            resource_stock=resource_stock,
            effective_capacity=effective_capacity,
            effective_regeneration=effective_regeneration,
            recovery_remaining=recovery_remaining,
            baseline_capacity=baseline_capacity,
            baseline_regeneration=baseline_regeneration,
        ),
    )
