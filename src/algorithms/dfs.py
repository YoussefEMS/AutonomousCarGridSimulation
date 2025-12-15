from __future__ import annotations

from typing import Dict, Optional, Set

from .base import SearchResult, path_cost, reconstruct_path
from src.grid import Grid, Position


def dfs(grid: Grid) -> SearchResult:
    start = grid.start
    goal = grid.goal
    stack = [start]
    visited: Set[Position] = {start}
    parent: Dict[Position, Optional[Position]] = {start: None}
    visited_order = [start]

    while stack:
        current = stack.pop()
        if current == goal:
            break
        for neighbor in grid.neighbors(current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current
            stack.append(neighbor)
            visited_order.append(neighbor)

    success = goal in parent
    path = reconstruct_path(parent, goal) if success else []
    cost = path_cost(grid, path) if success else float("inf")
    return SearchResult(
        name="DFS",
        path=path,
        cost=cost,
        explored_nodes=len(visited),
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

