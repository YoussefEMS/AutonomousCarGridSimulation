from __future__ import annotations

import heapq
from typing import Dict, Optional, Set

from .base import SearchResult, path_cost, reconstruct_path
from src.grid import Grid, Position


def _heuristic(a: Position, b: Position) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_search(grid: Grid) -> SearchResult:
    start, goal = grid.start, grid.goal
    frontier: list[tuple[float, Position]] = [(0.0, start)]
    g_costs: Dict[Position, float] = {start: 0.0}
    parent: Dict[Position, Optional[Position]] = {start: None}
    visited: Set[Position] = set()
    visited_order = [start]

    while frontier:
        f_score, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            break
        for neighbor in grid.neighbors(current):
            tentative_g = g_costs[current] + grid.cost(current, neighbor)
            if neighbor not in g_costs or tentative_g < g_costs[neighbor]:
                g_costs[neighbor] = tentative_g
                parent[neighbor] = current
                f = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(frontier, (f, neighbor))
                visited_order.append(neighbor)

    success = goal in parent
    path = reconstruct_path(parent, goal) if success else []
    cost = path_cost(grid, path) if success else float("inf")
    return SearchResult(
        name="A*",
        path=path,
        cost=cost,
        explored_nodes=len(visited),
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

