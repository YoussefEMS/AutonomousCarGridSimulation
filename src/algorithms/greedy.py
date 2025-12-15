from __future__ import annotations

import heapq
from typing import Dict, Optional, Set

from .base import SearchResult, path_cost, reconstruct_path
from src.grid import Grid, Position


def _heuristic(a: Position, b: Position) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def greedy_best_first(grid: Grid) -> SearchResult:
    start, goal = grid.start, grid.goal
    frontier: list[tuple[float, Position]] = [(_heuristic(start, goal), start)]
    parent: Dict[Position, Optional[Position]] = {start: None}
    visited: Set[Position] = {start}
    visited_order = [start]

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for neighbor in grid.neighbors(current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current
            heapq.heappush(frontier, (_heuristic(neighbor, goal), neighbor))
            visited_order.append(neighbor)

    success = goal in parent
    path = reconstruct_path(parent, goal) if success else []
    cost = path_cost(grid, path) if success else float("inf")
    return SearchResult(
        name="Greedy Best-First",
        path=path,
        cost=cost,
        explored_nodes=len(visited),
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

