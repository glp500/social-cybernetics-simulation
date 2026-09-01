"""Arrow schemas and serialization for immutable scientific run records."""

from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa

from social_cybernetics.domain import (
    AgentTransitionRecord,
    CellDamageApplication,
    CohortRecord,
    EventCellExposure,
    EventRecord,
    ModelRecord,
    ShockEventSnapshot,
)

TABLE_SCHEMA_VERSIONS = {
    "model": "scs-table/model/v0.1.0",
    "cohort": "scs-table/cohort/v1.0.0",
    "agent_transitions": "scs-table/agent-transitions/v1.0.0",
    "agent_events": "scs-table/agent-events/v0.1.0",
    "shock_events": "scs-table/shock-events/v0.1.0",
    "shock_exposures": "scs-table/shock-exposures/v0.1.0",
    "cell_damage": "scs-table/cell-damage/v0.1.0",
}

_POSITION_TYPE = pa.struct(
    [
        pa.field("x", pa.int64(), nullable=False),
        pa.field("y", pa.int64(), nullable=False),
    ]
)


def _schema(name: str, fields: list[pa.Field]) -> pa.Schema:
    return pa.schema(
        fields,
        metadata={
            b"scs.table_name": name.encode(),
            b"scs.schema_version": TABLE_SCHEMA_VERSIONS[name].encode(),
        },
    )


_TABLE_SCHEMAS = {
    "model": _schema(
        "model",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("total_resources", pa.float64(), nullable=False),
            pa.field("alive_count", pa.int64(), nullable=False),
            pa.field("cohort_mean_energy", pa.float64(), nullable=False),
            pa.field("total_harvest", pa.float64(), nullable=False),
            pa.field("unmet_need", pa.float64(), nullable=False),
            pa.field("energy_gini", pa.float64(), nullable=False),
        ],
    ),
    "cohort": _schema(
        "cohort",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("agent_id", pa.int64(), nullable=False),
            pa.field("position_x", pa.int64(), nullable=False),
            pa.field("position_y", pa.int64(), nullable=False),
            pa.field("energy", pa.float64(), nullable=False),
            pa.field("alive", pa.bool_(), nullable=False),
        ],
    ),
    "agent_transitions": _schema(
        "agent_transitions",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("agent_id", pa.int64(), nullable=False),
            pa.field("origin_x", pa.int64(), nullable=False),
            pa.field("origin_y", pa.int64(), nullable=False),
            pa.field("observed_stock", pa.float64(), nullable=False),
            pa.field("believed_stock", pa.float64(), nullable=False),
            pa.field("intent_kind", pa.string(), nullable=False),
            pa.field("requested_amount", pa.float64(), nullable=False),
            pa.field("intended_destination_x", pa.int64()),
            pa.field("intended_destination_y", pa.int64()),
            pa.field("gate_allowed", pa.bool_(), nullable=False),
            pa.field("harvested", pa.float64(), nullable=False),
            pa.field("moved", pa.bool_(), nullable=False),
            pa.field("final_position_x", pa.int64(), nullable=False),
            pa.field("final_position_y", pa.int64(), nullable=False),
            pa.field("energy_before", pa.float64(), nullable=False),
            pa.field("energy_after", pa.float64(), nullable=False),
            pa.field("shortfall", pa.float64(), nullable=False),
            pa.field("died", pa.bool_(), nullable=False),
        ],
    ),
    "agent_events": _schema(
        "agent_events",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("event", pa.string(), nullable=False),
            pa.field("agent_id", pa.int64()),
            pa.field("amount", pa.float64()),
            pa.field("position_x", pa.int64()),
            pa.field("position_y", pa.int64()),
        ],
    ),
    "shock_events": _schema(
        "shock_events",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("event_id", pa.int64(), nullable=False),
            pa.field("scope", pa.string(), nullable=False),
            pa.field("initiation_tick", pa.int64(), nullable=False),
            pa.field("epicenter_x", pa.int64()),
            pa.field("epicenter_y", pa.int64()),
            pa.field("age", pa.int64(), nullable=False),
            pa.field("status", pa.string(), nullable=False),
            pa.field(
                "frontier",
                pa.list_(pa.field("element", _POSITION_TYPE, nullable=False)),
                nullable=False,
            ),
            pa.field("affected_count", pa.int64(), nullable=False),
            pa.field("event_probability", pa.float64(), nullable=False),
            pa.field("stock_loss_fraction", pa.float64(), nullable=False),
            pa.field("capacity_loss_fraction", pa.float64(), nullable=False),
            pa.field("regeneration_suppression_fraction", pa.float64(), nullable=False),
            pa.field("recovery_ticks", pa.int64(), nullable=False),
            pa.field("spread_probability", pa.float64()),
            pa.field("max_spread_ticks", pa.int64()),
            pa.field("termination_reason", pa.string()),
        ],
    ),
    "shock_exposures": _schema(
        "shock_exposures",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("event_id", pa.int64(), nullable=False),
            pa.field("position_x", pa.int64(), nullable=False),
            pa.field("position_y", pa.int64(), nullable=False),
            pa.field(
                "exposing_neighbors",
                pa.list_(pa.field("element", _POSITION_TYPE, nullable=False)),
                nullable=False,
            ),
            pa.field(
                "successful_neighbors",
                pa.list_(pa.field("element", _POSITION_TYPE, nullable=False)),
                nullable=False,
            ),
            pa.field("transmitted", pa.bool_(), nullable=False),
        ],
    ),
    "cell_damage": _schema(
        "cell_damage",
        [
            pa.field("tick", pa.int64(), nullable=False),
            pa.field("position_x", pa.int64(), nullable=False),
            pa.field("position_y", pa.int64(), nullable=False),
            pa.field(
                "event_ids",
                pa.list_(pa.field("element", pa.int64(), nullable=False)),
                nullable=False,
            ),
            pa.field("combined_stock_multiplier", pa.float64(), nullable=False),
            pa.field("combined_capacity_multiplier", pa.float64(), nullable=False),
            pa.field("combined_regeneration_multiplier", pa.float64(), nullable=False),
            pa.field("pre_stock", pa.float64(), nullable=False),
            pa.field("post_stock", pa.float64(), nullable=False),
            pa.field("pre_effective_capacity", pa.float64(), nullable=False),
            pa.field("post_effective_capacity", pa.float64(), nullable=False),
            pa.field("pre_effective_regeneration", pa.float64(), nullable=False),
            pa.field("post_effective_regeneration", pa.float64(), nullable=False),
            pa.field("recovery_completion_tick", pa.int64(), nullable=False),
        ],
    ),
}


@dataclass(frozen=True, slots=True)
class RunRecords:
    """Immutable record collections accepted by the persistence boundary."""

    model: tuple[ModelRecord, ...] = ()
    cohort: tuple[CohortRecord, ...] = ()
    agent_transitions: tuple[AgentTransitionRecord, ...] = ()
    agent_events: tuple[EventRecord, ...] = ()
    shock_events: tuple[ShockEventSnapshot, ...] = ()
    shock_exposures: tuple[EventCellExposure, ...] = ()
    cell_damage: tuple[CellDamageApplication, ...] = ()


def _positions(positions: tuple[tuple[int, int], ...]) -> list[dict[str, int]]:
    return [{"x": x, "y": y} for x, y in positions]


def build_record_tables(records: RunRecords) -> dict[str, pa.Table]:
    """Convert immutable domain records into explicitly typed Arrow tables."""

    rows: dict[str, list[dict[str, object]]] = {
        "model": [
            {
                "tick": record.tick,
                "total_resources": record.total_resources,
                "alive_count": record.alive_count,
                "cohort_mean_energy": record.cohort_mean_energy,
                "total_harvest": record.total_harvest,
                "unmet_need": record.unmet_need,
                "energy_gini": record.energy_gini,
            }
            for record in records.model
        ],
        "cohort": [
            {
                "tick": record.tick,
                "agent_id": record.snapshot.agent_id,
                "position_x": record.snapshot.position[0],
                "position_y": record.snapshot.position[1],
                "energy": record.snapshot.energy,
                "alive": record.snapshot.alive,
            }
            for record in records.cohort
        ],
        "agent_transitions": [
            {
                "tick": record.tick,
                "agent_id": record.agent_id,
                "origin_x": record.origin[0],
                "origin_y": record.origin[1],
                "observed_stock": record.observed_stock,
                "believed_stock": record.believed_stock,
                "intent_kind": record.intent_kind.value,
                "requested_amount": record.requested_amount,
                "intended_destination_x": (
                    record.intended_destination[0]
                    if record.intended_destination is not None
                    else None
                ),
                "intended_destination_y": (
                    record.intended_destination[1]
                    if record.intended_destination is not None
                    else None
                ),
                "gate_allowed": record.gate_allowed,
                "harvested": record.harvested,
                "moved": record.moved,
                "final_position_x": record.final_position[0],
                "final_position_y": record.final_position[1],
                "energy_before": record.energy_before,
                "energy_after": record.energy_after,
                "shortfall": record.shortfall,
                "died": record.died,
            }
            for record in records.agent_transitions
        ],
        "agent_events": [
            {
                "tick": record.tick,
                "event": record.event,
                "agent_id": record.agent_id,
                "amount": record.amount,
                "position_x": record.position[0] if record.position is not None else None,
                "position_y": record.position[1] if record.position is not None else None,
            }
            for record in records.agent_events
        ],
        "shock_events": [
            {
                "tick": record.tick,
                "event_id": record.event_id,
                "scope": record.scope.value,
                "initiation_tick": record.initiation_tick,
                "epicenter_x": record.epicenter[0] if record.epicenter is not None else None,
                "epicenter_y": record.epicenter[1] if record.epicenter is not None else None,
                "age": record.age,
                "status": record.status.value,
                "frontier": _positions(record.frontier),
                "affected_count": record.affected_count,
                "event_probability": record.event_probability,
                "stock_loss_fraction": record.damage.stock_loss_fraction,
                "capacity_loss_fraction": record.damage.capacity_loss_fraction,
                "regeneration_suppression_fraction": (
                    record.damage.regeneration_suppression_fraction
                ),
                "recovery_ticks": record.damage.recovery_ticks,
                "spread_probability": record.spread_probability,
                "max_spread_ticks": record.max_spread_ticks,
                "termination_reason": (
                    record.termination_reason.value
                    if record.termination_reason is not None
                    else None
                ),
            }
            for record in records.shock_events
        ],
        "shock_exposures": [
            {
                "tick": record.tick,
                "event_id": record.event_id,
                "position_x": record.position[0],
                "position_y": record.position[1],
                "exposing_neighbors": _positions(record.exposing_neighbors),
                "successful_neighbors": _positions(record.successful_neighbors),
                "transmitted": record.transmitted,
            }
            for record in records.shock_exposures
        ],
        "cell_damage": [
            {
                "tick": record.tick,
                "position_x": record.position[0],
                "position_y": record.position[1],
                "event_ids": list(record.event_ids),
                "combined_stock_multiplier": record.combined_stock_multiplier,
                "combined_capacity_multiplier": record.combined_capacity_multiplier,
                "combined_regeneration_multiplier": record.combined_regeneration_multiplier,
                "pre_stock": record.pre_stock,
                "post_stock": record.post_stock,
                "pre_effective_capacity": record.pre_effective_capacity,
                "post_effective_capacity": record.post_effective_capacity,
                "pre_effective_regeneration": record.pre_effective_regeneration,
                "post_effective_regeneration": record.post_effective_regeneration,
                "recovery_completion_tick": record.recovery_completion_tick,
            }
            for record in records.cell_damage
        ],
    }
    return {
        name: pa.Table.from_pylist(rows[name], schema=_TABLE_SCHEMAS[name])
        for name in TABLE_SCHEMA_VERSIONS
    }
