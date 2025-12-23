from __future__ import annotations

import math
from typing import Sequence

from src.grid import Grid

WEIGHT_CYCLE_VALUES = [1.0, 2.0, 3.0, 5.0, 10.0]


def next_weight_value(current: float, values: Sequence[float] = WEIGHT_CYCLE_VALUES) -> float:
    """Return the next weight in the configured cycle."""
    if not values:
        return current
    for idx, value in enumerate(values):
        if math.isclose(current, value, rel_tol=1e-9, abs_tol=1e-9):
            return values[(idx + 1) % len(values)]
    return values[0]


def grid_has_custom_weights(grid: Grid, tolerance: float = 1e-6) -> bool:
    """Return True if any non-obstacle cell deviates from the default weight of 1."""
    for cell in grid.cells.values():
        if cell.obstacle:
            continue
        if not math.isclose(cell.weight, 1.0, abs_tol=tolerance):
            return True
    return False
