from __future__ import annotations

from collections import deque
from typing import Dict, Optional, Set

from .base import SearchResult, path_cost
from src.grid import Grid, Position


def _reconstruct_bidirectional(
    meet: Position,
    parents_start: Dict[Position, Optional[Position]],
    parents_goal: Dict[Position, Optional[Position]],
) -> list[Position]:
    # Path from start to meeting node
    path_start = []
    node = meet
    while node is not None:
        path_start.append(node)
        node = parents_start.get(node)
    path_start.reverse()

    # Path from meeting node to goal
    path_goal = []
    node = parents_goal.get(meet)
    while node is not None:
        path_goal.append(node)
        node = parents_goal.get(node)
    return path_start + path_goal


def bidirectional_search(grid: Grid) -> SearchResult:
    start, goal = grid.start, grid.goal
    if start == goal:
        return SearchResult("Bidirectional", [start], 0.0, 1, 0.0, True, [start])

    frontier_start = deque([start])
    frontier_goal = deque([goal])
    parents_start: Dict[Position, Optional[Position]] = {start: None}
    parents_goal: Dict[Position, Optional[Position]] = {goal: None}
    visited_start: Set[Position] = {start}
    visited_goal: Set[Position] = {goal}
    visited_order = [start, goal]
    meet_node: Optional[Position] = None

    while frontier_start and frontier_goal:
        # Expand from start side
        for _ in range(len(frontier_start)):
            current = frontier_start.popleft()
            for neighbor in grid.neighbors(current):
                if neighbor in visited_start:
                    continue
                visited_start.add(neighbor)
                parents_start[neighbor] = current
                visited_order.append(neighbor)
                if neighbor in visited_goal:
                    meet_node = neighbor
                    break
                frontier_start.append(neighbor)
            if meet_node:
                break
        if meet_node:
            break

        # Expand from goal side
        for _ in range(len(frontier_goal)):
            current = frontier_goal.popleft()
            for neighbor in grid.neighbors(current):
                if neighbor in visited_goal:
                    continue
                visited_goal.add(neighbor)
                parents_goal[neighbor] = current
                visited_order.append(neighbor)
                if neighbor in visited_start:
                    meet_node = neighbor
                    break
                frontier_goal.append(neighbor)
            if meet_node:
                break

    success = meet_node is not None
    path = _reconstruct_bidirectional(meet_node, parents_start, parents_goal) if success else []
    explored_nodes = len(visited_start | visited_goal)
    cost = path_cost(grid, path) if success else float("inf")
    return SearchResult(
        name="Bidirectional",
        path=path,
        cost=cost,
        explored_nodes=explored_nodes,
        duration=0.0,
        success=success,
        visited_order=visited_order,
    )

