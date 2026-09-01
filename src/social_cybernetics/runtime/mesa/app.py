"""Minimal read-only SolaraViz debugging page for the v0.2 ecology."""

from pathlib import Path

import solara
from mesa.discrete_space import PropertyLayer
from mesa.visualization import SolaraViz, SpaceRenderer
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle

from social_cybernetics.config import load_config
from social_cybernetics.domain import ShockEventStatus
from social_cybernetics.runtime.mesa.agent import ForagerAgent
from social_cybernetics.runtime.mesa.model import SugarscapeModel


def agent_portrayal(agent: ForagerAgent) -> AgentPortrayalStyle:
    """Render one living wrapper using its Mesa position and domain energy."""

    cell = agent.cell
    if cell is None:
        raise ValueError("only living spatial agents may be portrayed")
    energy = agent.state.energy
    return AgentPortrayalStyle(
        x=cell.coordinate[0],
        y=cell.coordinate[1],
        color="#1565c0",
        marker="o",
        size=min(140.0, 25.0 + 4.0 * energy),
        zorder=2,
        edgecolors="#0d2f4f",
    )


def property_layer_portrayal(layer: PropertyLayer) -> PropertyLayerStyle | None:
    """Render resource intensity without changing the property layer."""

    if layer.name != "resource_stock":
        return None
    return PropertyLayerStyle(
        colormap="YlGn",
        alpha=0.85,
        colorbar=True,
        vmin=0,
        vmax=None,
    )


def metric_values(model: SugarscapeModel) -> dict[str, float | int]:
    """Expose read-only debugging measures derived from records and layers."""

    latest = model.model_records[-1]
    tick = model.completed_ticks
    return {
        "Total resources": latest.total_resources,
        "Alive": latest.alive_count,
        "Mean cohort energy": latest.cohort_mean_energy,
        "Recovering cells": int((model.recovery_remaining > 0).sum()),
        "Active shock events": sum(
            snapshot.tick == tick and snapshot.status is ShockEventStatus.ACTIVE
            for snapshot in model.shock_event_snapshots
        ),
        "Cells damaged this tick": sum(
            application.tick == tick for application in model.cell_damage_applications
        ),
    }


@solara.component  # pyright: ignore[reportPrivateImportUsage]
def _model_metrics_view(values: dict[str, float | int]) -> None:
    with solara.Card("Current state"), solara.ColumnsResponsive(12, large=4):
        for label, value in values.items():
            shown = f"{value:.3f}" if isinstance(value, float) else str(value)
            solara.Markdown(f"**{label}**  \n{shown}")


def model_metrics(model: SugarscapeModel):
    """Return a fresh metrics element so Mesa's render counter refreshes it."""

    return _model_metrics_view(metric_values(model))


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
visualization_config = load_config(REPOSITORY_ROOT / "configs" / "visualization-v0.2.yml")
model = SugarscapeModel(visualization_config)

renderer = (
    SpaceRenderer(model, backend="matplotlib")
    .setup_agents(agent_portrayal)
    .setup_propertylayer(property_layer_portrayal)
)
renderer.draw_propertylayer()
renderer.draw_agents()

page = SolaraViz(
    model,
    renderer,
    components=[(model_metrics, 0)],  # pyright: ignore[reportArgumentType]
    model_params={"config": visualization_config},
    name="Social Cybernetics Sugarscape — stochastic ecology v0.2",
    play_interval=300,
)

_ = page
