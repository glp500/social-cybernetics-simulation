"""Pure derived metrics for Project 1 ecology and provisioning evidence."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from social_cybernetics.domain import AgentTransitionRecord


@dataclass(frozen=True, slots=True)
class ShortfallSpell:
    agent_id: int
    start_tick: int
    end_tick: int
    length: int
    right_censored: bool


@dataclass(frozen=True, slots=True)
class SubsistenceSecurity:
    shortfall_frequency: float
    spells: tuple[ShortfallSpell, ...]
    mean_spell_length: float
    mean_shortfall_depth: float
    maximum_shortfall_depth: float
    catastrophic_shortfall_probability: float


def _validated_transitions(
    transitions: tuple[AgentTransitionRecord, ...], completed_ticks: int
) -> tuple[AgentTransitionRecord, ...]:
    if completed_ticks < 0:
        raise ValueError("completed_ticks must be nonnegative")
    ordered = tuple(sorted(transitions, key=lambda record: (record.agent_id, record.tick)))
    keys = [(record.agent_id, record.tick) for record in ordered]
    if len(keys) != len(set(keys)):
        raise ValueError("agent transitions are duplicated")
    for record in ordered:
        values = (
            record.energy_before,
            record.energy_after,
            record.shortfall,
            record.observed_stock,
            record.believed_stock,
            record.requested_amount,
            record.harvested,
        )
        if record.tick < 1 or record.tick > completed_ticks:
            raise ValueError("agent transition tick is outside the completed history")
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("agent transition measures must be finite and nonnegative")
        if record.died != (record.energy_after == 0.0):
            raise ValueError("death must coincide with zero energy")
    return ordered


def _shortfall_spells(
    ordered: tuple[AgentTransitionRecord, ...], completed_ticks: int
) -> tuple[ShortfallSpell, ...]:
    by_agent: dict[int, list[AgentTransitionRecord]] = defaultdict(list)
    for record in ordered:
        by_agent[record.agent_id].append(record)

    spells: list[ShortfallSpell] = []
    for agent_id, history in sorted(by_agent.items()):
        if not history[-1].died and history[-1].tick != completed_ticks:
            raise ValueError("a surviving agent history must reach the final tick")
        start: int | None = None
        previous_tick = 0
        for record in history:
            if start is not None and record.tick != previous_tick + 1:
                spells.append(
                    ShortfallSpell(agent_id, start, previous_tick, previous_tick - start + 1, False)
                )
                start = None
            if record.shortfall > 0 and start is None:
                start = record.tick
            elif record.shortfall == 0 and start is not None:
                spells.append(
                    ShortfallSpell(agent_id, start, previous_tick, previous_tick - start + 1, False)
                )
                start = None
            previous_tick = record.tick
        if start is not None:
            right_censored = not history[-1].died and history[-1].tick == completed_ticks
            spells.append(
                ShortfallSpell(
                    agent_id,
                    start,
                    history[-1].tick,
                    history[-1].tick - start + 1,
                    right_censored,
                )
            )
    return tuple(spells)


def calculate_subsistence_security(
    transitions: tuple[AgentTransitionRecord, ...], *, completed_ticks: int
) -> SubsistenceSecurity:
    """Calculate longitudinal shortfall and catastrophic-risk measures."""

    ordered = _validated_transitions(transitions, completed_ticks)
    if not ordered:
        return SubsistenceSecurity(0.0, (), 0.0, 0.0, 0.0, 0.0)

    positive_depths = [record.shortfall for record in ordered if record.shortfall > 0]
    spells = _shortfall_spells(ordered, completed_ticks)
    return SubsistenceSecurity(
        shortfall_frequency=len(positive_depths) / len(ordered),
        spells=spells,
        mean_spell_length=(sum(spell.length for spell in spells) / len(spells) if spells else 0.0),
        mean_shortfall_depth=(
            sum(positive_depths) / len(positive_depths) if positive_depths else 0.0
        ),
        maximum_shortfall_depth=max(positive_depths, default=0.0),
        catastrophic_shortfall_probability=(
            sum(record.energy_after == 0.0 for record in ordered) / len(ordered)
        ),
    )
