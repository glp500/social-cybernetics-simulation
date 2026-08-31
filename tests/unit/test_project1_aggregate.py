import math

import pytest

from social_cybernetics.analysis.project1_aggregate import (
    MEASURE_FIELDS,
    condition_summaries,
    paired_differences,
)


def _row(condition: str, seed: int, harvest: float, rank: float | None) -> dict[str, object]:
    return {
        "experiment_id": "experiment",
        "condition_id": condition,
        "seed": seed,
        "aggregate_harvest": harvest,
        "rank_autocorrelation": rank,
        "rank_autocorrelation_reason": "constant ranks" if rank is None else None,
    }


def test_condition_summaries_record_defined_and_undefined_values() -> None:
    rows = [_row("control", 1, 2.0, None), _row("control", 2, 4.0, 0.5)]

    summaries = condition_summaries(rows)

    harvest = next(row for row in summaries if row["metric"] == "aggregate_harvest")
    assert harvest == {
        "experiment_id": "experiment",
        "condition_id": "control",
        "metric": "aggregate_harvest",
        "defined_count": 2,
        "undefined_count": 0,
        "mean": 3.0,
        "median": 3.0,
        "sample_std": math.sqrt(2.0),
        "minimum": 2.0,
        "maximum": 4.0,
    }
    rank = next(row for row in summaries if row["metric"] == "rank_autocorrelation")
    assert rank["defined_count"] == 1
    assert rank["undefined_count"] == 1
    assert rank["sample_std"] is None
    assert len(summaries) == len(MEASURE_FIELDS)


def test_paired_differences_use_all_condition_pairs_and_matching_seeds() -> None:
    rows = [
        _row("control", 1, 2.0, None),
        _row("control", 2, 4.0, 0.5),
        _row("treatment", 1, 5.0, None),
        _row("treatment", 2, 3.0, 0.25),
        _row("alternative", 1, 6.0, 0.75),
        _row("alternative", 2, 8.0, 0.75),
    ]

    contrasts = paired_differences(rows)

    harvest = [
        row
        for row in contrasts
        if row["metric"] == "aggregate_harvest" and row["condition_id"] == "treatment"
    ]
    assert [row["difference"] for row in harvest] == [3.0, -1.0]
    assert all(row["reference_condition_id"] == "control" for row in harvest)
    assert len(contrasts) == 3 * 2 * len(MEASURE_FIELDS)
    treatment_alternative = next(
        row
        for row in contrasts
        if row["reference_condition_id"] == "treatment"
        and row["condition_id"] == "alternative"
        and row["seed"] == 2
        and row["metric"] == "aggregate_harvest"
    )
    assert treatment_alternative["difference"] == 5.0
    undefined_rank = next(
        row for row in contrasts if row["metric"] == "rank_autocorrelation" and row["seed"] == 1
    )
    assert undefined_rank["defined"] is False
    assert undefined_rank["undefined_reason"] == (
        "reference: constant ranks; condition: constant ranks"
    )


def test_paired_differences_reject_duplicates_and_unpaired_seeds() -> None:
    duplicate = [_row("control", 1, 2.0, None), _row("control", 1, 3.0, None)]
    with pytest.raises(ValueError, match="duplicate condition seed"):
        paired_differences(duplicate)

    unpaired = [_row("control", 1, 2.0, None), _row("treatment", 2, 3.0, None)]
    with pytest.raises(ValueError, match="same seeds"):
        paired_differences(unpaired)


def test_aggregates_reject_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="not finite"):
        condition_summaries([_row("control", 1, math.inf, None)])
