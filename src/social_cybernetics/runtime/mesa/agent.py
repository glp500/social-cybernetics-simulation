"""Passive Mesa spatial wrapper around authoritative domain state."""

from mesa.discrete_space import Cell, CellAgent

from social_cybernetics.domain import AgentState


class ForagerAgent(CellAgent):
    """Owns no behavior; the model executes every explicit scientific stage."""

    def __init__(self, model: object, state: AgentState, cell: Cell) -> None:
        super().__init__(model)
        self.state = state
        self.cell = cell
