from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle

from social_cybernetics.config import ExplicitResourceConfig, SimulationConfig
from social_cybernetics.runtime.mesa.app import (
    agent_portrayal,
    metric_values,
    page,
    property_layer_portrayal,
    visualization_config,
)
from social_cybernetics.runtime.mesa.model import SugarscapeModel


def test_visualization_portrays_living_agent_energy() -> None:
    model = SugarscapeModel(SimulationConfig(duration=1))
    agent = model.active_agents[0]

    style = agent_portrayal(agent)

    assert isinstance(style, AgentPortrayalStyle)
    assert style.size == 65.0
    assert style.x == 2
    assert style.y == 2


def test_visualization_scales_resource_stock_to_heterogeneous_data() -> None:
    model = SugarscapeModel(SimulationConfig(duration=1))

    stock_style = property_layer_portrayal(model.resource_layer)
    capacity_style = property_layer_portrayal(model.capacity_layer)

    assert isinstance(stock_style, PropertyLayerStyle)
    assert stock_style.vmin == 0
    assert stock_style.vmax is None
    assert capacity_style is None


def test_metric_values_change_after_a_step() -> None:
    model = SugarscapeModel(SimulationConfig(duration=1))

    before = metric_values(model)
    model.step()
    after = metric_values(model)

    assert before == {
        "Total resources": 250.0,
        "Alive": 1,
        "Mean cohort energy": 10.0,
        "Recovering cells": 0,
        "Active shock events": 0,
        "Cells damaged this tick": 0,
    }
    assert after == {
        "Total resources": 248.0,
        "Alive": 1,
        "Mean cohort energy": 11.0,
        "Recovering cells": 0,
        "Active shock events": 0,
        "Cells damaged this tick": 0,
    }
    assert page is not None


def test_visualization_uses_a_heterogeneous_correlated_shock_fixture() -> None:
    assert isinstance(visualization_config.resources, ExplicitResourceConfig)
    assert visualization_config.shock.kind == "correlated"


def test_metric_values_expose_current_shock_damage_and_recovery() -> None:
    config = SimulationConfig.model_validate(
        {
            "schema_version": "0.2.0",
            "duration": 1,
            "world": {"width": 2, "height": 1},
            "agents": {"count": 0, "initial_positions": []},
            "shock": {
                "kind": "system",
                "event_probability": 1.0,
                "stock_loss_fraction": 0.1,
                "capacity_loss_fraction": 0.2,
                "regeneration_suppression_fraction": 0.3,
                "recovery_ticks": 4,
            },
        }
    )
    model = SugarscapeModel(config)

    model.step()

    assert metric_values(model) == {
        "Total resources": 18.0,
        "Alive": 0,
        "Mean cohort energy": 0.0,
        "Recovering cells": 2,
        "Active shock events": 0,
        "Cells damaged this tick": 2,
    }
