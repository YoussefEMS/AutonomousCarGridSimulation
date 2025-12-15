from __future__ import annotations

import heapq
from typing import Dict, Optional, Set

from .base import SearchResult, path_cost, reconstruct_path
from src.grid import Grid, Position


def uniform_cost_search(grid: Grid) -> SearchResult:
    start = grid.start
    goal = grid.goal
    frontier: list[tuple[float, Position]] = [(0.0, start)]
    costs: Dict[Position, float] = {start: 0.0}
    parent: Dict[Position, Optional[Position]] = {start: None}
    visited_order = [start]
    visited: Set[Position] = set()

    while frontier:
        current_cost, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            break
        for neighbor in grid.neighbors(current):
            new_cost = current_cost + grid.cost(current, neighbor)
            if neighbor not in costs or new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                parent[neighbor] = current
                heapq.heappush(frontier, (new_cost, neighbor))
                visited_order.append(neighbor)

    success = goal in parent
    path = reconstruct_path(parent, goal) if success else []
    cost = path_cost(grid, path) if success else float("inf")
    return SearchResult(
        name="Uniform Cost",
        path=path,
        cost=cost,
        explored_nodes=len(visited),
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

