from __future__ import annotations

from math import inf
from typing import List, Set

from .base import SearchResult, path_cost
from src.grid import Grid, Position


def _heuristic(a: Position, b: Position) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def ida_star_search(grid: Grid) -> SearchResult:
    start, goal = grid.start, grid.goal
    bound = _heuristic(start, goal)
    visited_order: List[Position] = [start]
    explored: Set[Position] = set([start])
    final_path: List[Position] = []

    def search(path: List[Position], g_cost: float, limit: float) -> float:
        nonlocal final_path
        node = path[-1]
        f_score = g_cost + _heuristic(node, goal)
        if f_score > limit:
            return f_score
        if node == goal:
            final_path = list(path)
            return "FOUND"
        minimum = inf
        for neighbor in grid.neighbors(node):
            if neighbor in path:
                continue
            visited_order.append(neighbor)
            explored.add(neighbor)
            cost = g_cost + grid.cost(node, neighbor)
            result = search(path + [neighbor], cost, limit)
            if result == "FOUND":
                return "FOUND"
            if isinstance(result, float) and result < minimum:
                minimum = result
        return minimum

    while True:
        t = search([start], 0.0, bound)
        if t == "FOUND":
            success = True
            break
        if t == inf:
            success = False
            break
        bound = t

    cost = path_cost(grid, final_path) if success else float("inf")
    return SearchResult(
        name="IDA*",
        path=final_path if success else [],
        cost=cost,
        explored_nodes=len(explored),
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

