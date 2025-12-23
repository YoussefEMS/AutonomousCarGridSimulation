from __future__ import annotations

import heapq
from typing import Dict, Optional, Set

from .base import SearchResult, path_cost
from src.grid import Grid, Position


def _heuristic(a: Position, b: Position) -> float:
    # Manhattan distance
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct_bidirectional_astar(
    meet: Position,
    parents_start: Dict[Position, Optional[Position]],
    parents_goal: Dict[Position, Optional[Position]],
) -> list[Position]:
    if meet is None:
        return []

    # Path from start to meet
    path_start = []
    node = meet
    while node is not None:
        path_start.append(node)
        node = parents_start.get(node)
    path_start.reverse()  # now start -> meet

    # Path from meet to goal
    path_goal = []
    node = parents_goal.get(meet)
    while node is not None:
        path_goal.append(node)
        node = parents_goal.get(node)

    return path_start + path_goal


def bidirectional_a_star_search(grid: Grid) -> SearchResult:
    start, goal = grid.start, grid.goal
    if start == goal:
        return SearchResult("Bidirectional A*", [start], 0.0, 1, 0.0, True, [start])

    frontier_start = [(0.0, start)]
    frontier_goal = [(0.0, goal)]

    g_start: Dict[Position, float] = {start: 0.0}
    g_goal: Dict[Position, float] = {goal: 0.0}

    parents_start: Dict[Position, Optional[Position]] = {start: None}
    parents_goal: Dict[Position, Optional[Position]] = {goal: None}

    visited_start: Set[Position] = set()
    visited_goal: Set[Position] = set()

    visited_order = [start, goal]
    meet_node: Optional[Position] = None
    best_total_cost = float("inf")

    while frontier_start or frontier_goal:
        # Expand from START side
        if frontier_start:
            _, current = heapq.heappop(frontier_start)
            if current not in visited_start:
                visited_start.add(current)
                for neighbor in grid.neighbors(current):
                    tentative_g = g_start[current] + grid.cost(current, neighbor)
                    if neighbor not in g_start or tentative_g < g_start[neighbor]:
                        g_start[neighbor] = tentative_g
                        parents_start[neighbor] = current
                        f = tentative_g + _heuristic(neighbor, goal)
                        heapq.heappush(frontier_start, (f, neighbor))
                        visited_order.append(neighbor)
                    # Check if meet
                    if neighbor in visited_goal:
                        total_cost = tentative_g + g_goal[neighbor]
                        if total_cost < best_total_cost:
                            best_total_cost = total_cost
                            meet_node = neighbor

        # Expand from GOAL side
        if frontier_goal:
            _, current = heapq.heappop(frontier_goal)
            if current not in visited_goal:
                visited_goal.add(current)
                for neighbor in grid.neighbors(current):
                    tentative_g = g_goal[current] + grid.cost(current, neighbor)
                    if neighbor not in g_goal or tentative_g < g_goal[neighbor]:
                        g_goal[neighbor] = tentative_g
                        parents_goal[neighbor] = current
                        f = tentative_g + _heuristic(neighbor, start)
                        heapq.heappush(frontier_goal, (f, neighbor))
                        visited_order.append(neighbor)
                    # Check if meet
                    if neighbor in visited_start:
                        total_cost = tentative_g + g_start[neighbor]
                        if total_cost < best_total_cost:
                            best_total_cost = total_cost
                            meet_node = neighbor

        # Early stop if the best_total_cost is found
        if meet_node is not None and frontier_start and frontier_goal:
            # Optional: break if the sum of min f-values exceeds best_total_cost
            min_f_start = frontier_start[0][0] if frontier_start else float("inf")
            min_f_goal = frontier_goal[0][0] if frontier_goal else float("inf")
            if min_f_start + min_f_goal >= best_total_cost:
                break

    success = meet_node is not None
    path = _reconstruct_bidirectional_astar(meet_node, parents_start, parents_goal) if success else []

    explored_nodes = len(visited_start | visited_goal)
    cost = path_cost(grid, path) if success else float("inf")

    return SearchResult(
        name="Bidirectional A*",
        path=path,
        cost=cost,
        explored_nodes=explored_nodes,
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )
