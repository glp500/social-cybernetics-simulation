from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle

from social_cybernetics.config import SimulationConfig
from social_cybernetics.runtime.mesa.app import (
    agent_portrayal,
    metric_values,
    page,
    property_layer_portrayal,
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


def test_visualization_only_draws_resource_stock() -> None:
    model = SugarscapeModel(SimulationConfig(duration=1))

    stock_style = property_layer_portrayal(model.resource_layer)
    capacity_style = property_layer_portrayal(model.capacity_layer)

    assert isinstance(stock_style, PropertyLayerStyle)
    assert stock_style.vmin == 0
    assert stock_style.vmax == 10
    assert capacity_style is None


def test_metric_values_change_after_a_step() -> None:
    model = SugarscapeModel(SimulationConfig(duration=1))

    before = metric_values(model)
    model.step()
    after = metric_values(model)

    assert before == {"Total resources": 250.0, "Alive": 1, "Mean cohort energy": 10.0}
    assert after == {"Total resources": 248.0, "Alive": 1, "Mean cohort energy": 11.0}
    assert page is not None
