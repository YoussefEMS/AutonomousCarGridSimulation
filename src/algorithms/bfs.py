from __future__ import annotations

from collections import deque
from typing import Dict, Optional, Set

from .base import SearchResult, path_cost, reconstruct_path
from src.grid import Grid, Position


def bfs(grid: Grid) -> SearchResult:
    start = grid.start
    goal = grid.goal
    frontier: deque[Position] = deque([start])
    visited: Set[Position] = {start}
    parent: Dict[Position, Optional[Position]] = {start: None}
    visited_order = [start]

    while frontier:
        current = frontier.popleft()
        if current == goal:
            break
        for neighbor in grid.neighbors(current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current
            frontier.append(neighbor)
            visited_order.append(neighbor)

    success = goal in parent
    path = reconstruct_path(parent, goal) if success else []
    cost = path_cost(grid, path) if success else float("inf")
    return SearchResult(
        name="BFS",
        path=path,
        cost=cost,
        explored_nodes=len(visited),
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

