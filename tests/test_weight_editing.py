"""Tests for weight editing helpers and behavior."""

from src.grid import Grid, Cell
from src.algorithms.base import path_cost
from src.weight_utils import next_weight_value, WEIGHT_CYCLE_VALUES, grid_has_custom_weights


def test_next_weight_value_cycles_through_defaults():
    value = 1.0
    seen = []
    for _ in range(len(WEIGHT_CYCLE_VALUES)):
        value = next_weight_value(value, WEIGHT_CYCLE_VALUES)
        seen.append(value)
    assert seen == WEIGHT_CYCLE_VALUES[1:] + [WEIGHT_CYCLE_VALUES[0]]


def test_custom_weight_affects_path_cost():
    grid = Grid.with_defaults(rows=2, cols=2)
    path = [(0, 0), (0, 1), (1, 1)]
    base_cost = path_cost(grid, path)
    assert base_cost == 2.0

    grid.cells[(0, 1)] = Cell(weight=5.0, obstacle=False)
    assert grid_has_custom_weights(grid) is True

    updated_cost = path_cost(grid, path)
    assert updated_cost == 6.0
    assert updated_cost > base_cost
