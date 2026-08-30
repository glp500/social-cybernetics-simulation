"""Distribution and longitudinal persistence metrics for Project 1."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from social_cybernetics.domain import AgentTransitionRecord, CohortRecord
from social_cybernetics.metrics import (
    RankedShare,
    bottom_fraction_burden_share,
    gini,
    top_fraction_share,
)

from .project1 import _validated_transitions


@dataclass(frozen=True, slots=True)
class DefinedFloat:
    value: float | None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class DistributionMetrics:
    cumulative_harvest: tuple[tuple[int, float], ...]
    cumulative_unmet_need: tuple[tuple[int, float], ...]
    harvest_gini: float
    energy_gini: float
    unmet_need_gini: float
    top_10_percent_harvest_share: RankedShare
    bottom_25_percent_shortfall_share: RankedShare


@dataclass(frozen=True, slots=True)
class RankTransition:
    counts: tuple[tuple[int, ...], ...]
    probabilities: tuple[tuple[float, ...], ...]
    row_defined: tuple[bool, ...]


@dataclass(frozen=True, slots=True)
class DurationSummary:
    spell_lengths: tuple[int, ...]
    mean: float
    maximum: int


@dataclass(frozen=True, slots=True)
class HalfLife:
    value: int
    peak_tick: int
    right_censored: bool


@dataclass(frozen=True, slots=True)
class PersistenceMetrics:
    material_rank_autocorrelation: DefinedFloat
    rank_transition: RankTransition
    advantage_duration: DurationSummary
    inequality_half_life: HalfLife


def _cohort_ids_and_final_energy(
    cohort: tuple[CohortRecord, ...], completed_ticks: int
) -> tuple[tuple[int, ...], list[float]]:
    initial_ids = tuple(sorted(record.snapshot.agent_id for record in cohort if record.tick == 0))
    if len(initial_ids) != len(set(initial_ids)):
        raise ValueError("tick-zero cohort contains duplicate agents")
    final = {
        record.snapshot.agent_id: record.snapshot.energy
        for record in cohort
        if record.tick == completed_ticks
    }
    if set(final) != set(initial_ids):
        raise ValueError("final cohort differs from the original cohort")
    return initial_ids, [final[agent_id] for agent_id in initial_ids]


def _cumulative_histories(
    transitions: tuple[AgentTransitionRecord, ...],
    agent_ids: tuple[int, ...],
    completed_ticks: int,
) -> dict[int, list[float]]:
    harvested = {agent_id: 0.0 for agent_id in agent_ids}
    histories = {tick: [] for tick in range(1, completed_ticks + 1)}
    by_tick: dict[int, list[AgentTransitionRecord]] = {}
    for record in transitions:
        by_tick.setdefault(record.tick, []).append(record)
    for tick in range(1, completed_ticks + 1):
        for record in by_tick.get(tick, []):
            harvested[record.agent_id] += record.harvested
        histories[tick] = [harvested[agent_id] for agent_id in agent_ids]
    return histories


def calculate_distribution(
    transitions: tuple[AgentTransitionRecord, ...],
    cohort: tuple[CohortRecord, ...],
    *,
    completed_ticks: int,
) -> DistributionMetrics:
    ordered = _validated_transitions(transitions, completed_ticks)
    agent_ids, final_energy = _cohort_ids_and_final_energy(cohort, completed_ticks)
    harvest = {agent_id: 0.0 for agent_id in agent_ids}
    unmet = {agent_id: 0.0 for agent_id in agent_ids}
    for record in ordered:
        harvest[record.agent_id] += record.harvested
        unmet[record.agent_id] += record.shortfall
    harvest_values = [harvest[agent_id] for agent_id in agent_ids]
    unmet_values = [unmet[agent_id] for agent_id in agent_ids]
    return DistributionMetrics(
        cumulative_harvest=tuple(zip(agent_ids, harvest_values, strict=True)),
        cumulative_unmet_need=tuple(zip(agent_ids, unmet_values, strict=True)),
        harvest_gini=gini(harvest_values),
        energy_gini=gini(final_energy),
        unmet_need_gini=gini(unmet_values),
        top_10_percent_harvest_share=top_fraction_share(harvest_values, 0.10),
        bottom_25_percent_shortfall_share=bottom_fraction_burden_share(
            unmet_values,
            harvest_values,
            0.25,
            identifiers=list(agent_ids),
        ),
    )


def _midranks(values: list[float]) -> np.ndarray:
    order = np.argsort(np.asarray(values), kind="stable")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2
        start = end
    return ranks


def _rank_autocorrelation(midpoint: list[float], final: list[float]) -> DefinedFloat:
    if len(midpoint) < 2:
        return DefinedFloat(None, "fewer than two agents")
    first_ranks = _midranks(midpoint)
    final_ranks = _midranks(final)
    if np.ptp(first_ranks) == 0 or np.ptp(final_ranks) == 0:
        return DefinedFloat(None, "constant cumulative-harvest ranks")
    value = float(np.corrcoef(first_ranks, final_ranks)[0, 1])
    return DefinedFloat(min(1.0, max(-1.0, value)))


def _quartiles(values: list[float]) -> list[int]:
    if not values:
        return []
    ranks = _midranks(values)
    size = len(values)
    return [min(3, int(4 * (rank - 0.5) / size)) for rank in ranks]


def _rank_transition(midpoint: list[float], final: list[float]) -> RankTransition:
    counts = [[0 for _ in range(4)] for _ in range(4)]
    for origin, destination in zip(_quartiles(midpoint), _quartiles(final), strict=True):
        counts[origin][destination] += 1
    row_defined = tuple(sum(row) > 0 for row in counts)
    probabilities = tuple(
        tuple(value / sum(row) for value in row) if sum(row) else (0.0, 0.0, 0.0, 0.0)
        for row in counts
    )
    return RankTransition(tuple(tuple(row) for row in counts), probabilities, row_defined)


def _advantage_duration(
    histories: dict[int, list[float]],
    transitions: tuple[AgentTransitionRecord, ...],
    agent_ids: tuple[int, ...],
) -> DurationSummary:
    active_by_tick = {(record.tick, record.agent_id) for record in transitions}
    spells: list[int] = []
    for index, agent_id in enumerate(agent_ids):
        length = 0
        for tick, values in histories.items():
            advantaged = (tick, agent_id) in active_by_tick and values[index] > float(
                np.median(values)
            )
            if advantaged:
                length += 1
            elif length:
                spells.append(length)
                length = 0
        if length:
            spells.append(length)
    return DurationSummary(
        spell_lengths=tuple(spells),
        mean=sum(spells) / len(spells) if spells else 0.0,
        maximum=max(spells, default=0),
    )


def _inequality_half_life(histories: dict[int, list[float]]) -> HalfLife:
    if not histories:
        return HalfLife(0, 0, False)
    series = [(tick, gini(values)) for tick, values in histories.items()]
    maximum = max(value for _, value in series)
    peak_tick = next(tick for tick, value in series if value == maximum)
    if maximum == 0.0:
        return HalfLife(0, peak_tick, False)
    for tick, value in series:
        if tick > peak_tick and value <= 0.5 * maximum:
            return HalfLife(tick - peak_tick, peak_tick, False)
    final_tick = series[-1][0]
    return HalfLife(final_tick - peak_tick, peak_tick, True)


def calculate_persistence(
    transitions: tuple[AgentTransitionRecord, ...],
    cohort: tuple[CohortRecord, ...],
    *,
    completed_ticks: int,
) -> PersistenceMetrics:
    ordered = _validated_transitions(transitions, completed_ticks)
    agent_ids, _ = _cohort_ids_and_final_energy(cohort, completed_ticks)
    histories = _cumulative_histories(ordered, agent_ids, completed_ticks)
    midpoint_tick = math.ceil(completed_ticks / 2)
    midpoint = histories.get(midpoint_tick, [0.0 for _ in agent_ids])
    final = histories.get(completed_ticks, [0.0 for _ in agent_ids])
    return PersistenceMetrics(
        material_rank_autocorrelation=_rank_autocorrelation(midpoint, final),
        rank_transition=_rank_transition(midpoint, final),
        advantage_duration=_advantage_duration(histories, ordered, agent_ids),
        inequality_half_life=_inequality_half_life(histories),
    )
