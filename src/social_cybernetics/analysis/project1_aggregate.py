"""Deterministic summaries and paired contrasts for flat Project 1 outcomes."""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence

MEASURE_FIELDS = (
    "aggregate_harvest",
    "survival_fraction",
    "mean_unmet_need",
    "shortfall_frequency",
    "mean_spell_length",
    "mean_shortfall_depth",
    "maximum_shortfall_depth",
    "catastrophic_shortfall_probability",
    "harvest_gini",
    "energy_gini",
    "unmet_need_gini",
    "top_harvest_share",
    "bottom_shortfall_share",
    "rank_autocorrelation",
    "mean_advantage_duration",
    "maximum_advantage_duration",
    "inequality_half_life",
    "inequality_half_life_peak_tick",
    "final_resource_depletion",
    "mean_resource_depletion",
    "maximum_resource_depletion",
    "final_capacity_deficit",
    "mean_capacity_deficit",
    "maximum_capacity_deficit",
    "final_regeneration_deficit",
    "mean_regeneration_deficit",
    "maximum_regeneration_deficit",
    "observed_mean_recovery_duration",
    "completed_mean_recovery_duration",
    "cumulative_capacity_deficit",
    "cumulative_regeneration_deficit",
    "cumulative_recovery_deficit",
)


def _value(row: Mapping[str, object], metric: str) -> float | None:
    value = row.get(metric)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Project 1 aggregate metric is not finite: {metric}")
    return float(value)


def _condition_groups(
    rows: Sequence[Mapping[str, object]],
) -> dict[tuple[str, str], list[Mapping[str, object]]]:
    groups: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    for row in rows:
        experiment = row.get("experiment_id")
        condition = row.get("condition_id")
        if not isinstance(experiment, str) or not isinstance(condition, str):
            raise ValueError("Project 1 aggregate rows require experiment and condition IDs")
        groups.setdefault((experiment, condition), []).append(row)
    return groups


def condition_summaries(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Return long-form descriptive statistics in declared condition order."""

    summaries: list[dict[str, object]] = []
    for (experiment, condition), group in _condition_groups(rows).items():
        for metric in MEASURE_FIELDS:
            values = [value for row in group if (value := _value(row, metric)) is not None]
            summaries.append(
                {
                    "experiment_id": experiment,
                    "condition_id": condition,
                    "metric": metric,
                    "defined_count": len(values),
                    "undefined_count": len(group) - len(values),
                    "mean": math.fsum(values) / len(values) if values else None,
                    "median": statistics.median(values) if values else None,
                    "sample_std": statistics.stdev(values) if len(values) > 1 else None,
                    "minimum": min(values, default=None),
                    "maximum": max(values, default=None),
                }
            )
    return summaries


def _experiment_conditions(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, dict[int, Mapping[str, object]]]]:
    experiments: dict[str, dict[str, dict[int, Mapping[str, object]]]] = {}
    for row in rows:
        experiment = row.get("experiment_id")
        condition = row.get("condition_id")
        seed = row.get("seed")
        if (
            not isinstance(experiment, str)
            or not isinstance(condition, str)
            or isinstance(seed, bool)
            or not isinstance(seed, int)
        ):
            raise ValueError("Project 1 paired rows require experiment, condition, and seed")
        by_seed = experiments.setdefault(experiment, {}).setdefault(condition, {})
        if seed in by_seed:
            raise ValueError("Project 1 paired rows contain a duplicate condition seed")
        by_seed[seed] = row
    return experiments


def _undefined_reason(reference: Mapping[str, object], condition: Mapping[str, object]) -> str:
    reasons = []
    for label, row in (("reference", reference), ("condition", condition)):
        reason = row.get("rank_autocorrelation_reason")
        if isinstance(reason, str):
            reasons.append(f"{label}: {reason}")
    return "; ".join(reasons) or "metric undefined"


def paired_differences(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Subtract every earlier condition from every later condition within seed."""

    contrasts: list[dict[str, object]] = []
    for experiment, conditions in _experiment_conditions(rows).items():
        ordered = tuple(conditions.items())
        for index, (reference_id, reference) in enumerate(ordered):
            for condition_id, candidates in ordered[index + 1 :]:
                if set(candidates) != set(reference):
                    raise ValueError("Project 1 paired conditions must contain the same seeds")
                for seed, reference_row in reference.items():
                    condition_row = candidates[seed]
                    for metric in MEASURE_FIELDS:
                        reference_value = _value(reference_row, metric)
                        condition_value = _value(condition_row, metric)
                        defined = reference_value is not None and condition_value is not None
                        difference = (
                            condition_value - reference_value
                            if reference_value is not None and condition_value is not None
                            else None
                        )
                        contrasts.append(
                            {
                                "experiment_id": experiment,
                                "reference_condition_id": reference_id,
                                "condition_id": condition_id,
                                "seed": seed,
                                "metric": metric,
                                "reference_value": reference_value,
                                "condition_value": condition_value,
                                "difference": difference,
                                "defined": defined,
                                "undefined_reason": (
                                    None
                                    if defined
                                    else _undefined_reason(reference_row, condition_row)
                                ),
                            }
                        )
    return contrasts
