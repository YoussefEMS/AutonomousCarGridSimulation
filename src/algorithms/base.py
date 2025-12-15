from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from src.grid import Grid, Position


@dataclass
class SearchResult:
    name: str
    path: List[Position]
    cost: float
    explored_nodes: int
    duration: float
    success: bool
    visited_order: List[Position]


AlgorithmRunner = Callable[[Grid], SearchResult]


def reconstruct_path(parent: Dict[Position, Optional[Position]], goal: Position) -> List[Position]:
    path: List[Position] = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    path.reverse()
    return path


def path_cost(grid: Grid, path: Iterable[Position]) -> float:
    cost = 0.0
    prev = None
    for pos in path:
        if prev is not None:
            cost += grid.cost(prev, pos)
        prev = pos
    return round(cost, 4)


def timed_run(name: str, func: Callable[[], SearchResult]) -> SearchResult:
    start = time.perf_counter()
    result = func()
    result.duration = time.perf_counter() - start
    result.name = name
    return result
