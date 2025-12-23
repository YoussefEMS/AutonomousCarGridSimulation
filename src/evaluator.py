from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional, Tuple

from src.grid import Grid
from src.algorithms import (
    SearchResult,
    bfs,
    dfs,
    uniform_cost_search,
    greedy_best_first,
    a_star_search,
    ida_star_search,
    bidirectional_search,
    bidirectional_a_star_search
)
from src.algorithms.base import timed_run


AlgorithmEntry = Tuple[str, Callable[[Grid], SearchResult]]

# Priority criteria options
PRIORITY_CRITERIA = ("cost", "nodes", "time")
DEFAULT_PRIORITY_ORDER = ("cost", "nodes", "time")


ALGORITHMS: List[AlgorithmEntry] = [
    ("BFS", bfs),
    ("DFS", dfs),
    ("Uniform Cost", uniform_cost_search),
    ("Greedy Best-First", greedy_best_first),
    ("A*", a_star_search),
    ("IDA*", ida_star_search),
    ("Bidirectional", bidirectional_search),
    ("Bidirectional Astar", bidirectional_a_star_search),
]


def _get_criterion_value(result: SearchResult, criterion: str) -> float:
    """Get the value for a specific criterion from a SearchResult."""
    if criterion == "cost":
        return result.cost
    elif criterion == "nodes":
        return float(result.explored_nodes)
    elif criterion == "time":
        return result.duration
    else:
        raise ValueError(f"Unknown criterion: {criterion}")


def _score(result: SearchResult, priority_order: Tuple[str, str, str] = DEFAULT_PRIORITY_ORDER) -> Tuple[float, float, float]:
    """Build a scoring tuple based on the priority order.
    
    Args:
        result: The SearchResult to score
        priority_order: Tuple of 3 criterion names in priority order.
                       First element is highest priority.
    
    Returns:
        Tuple of (primary, secondary, tertiary) values for comparison.
    """
    return (
        _get_criterion_value(result, priority_order[0]),
        _get_criterion_value(result, priority_order[1]),
        _get_criterion_value(result, priority_order[2]),
    )


def select_best(
    results: List[SearchResult],
    priority_order: Tuple[str, str, str] = DEFAULT_PRIORITY_ORDER
) -> Optional[SearchResult]:
    """Select the best result based on priority order.
    
    Args:
        results: List of SearchResult objects
        priority_order: Tuple of 3 criterion names in priority order.
    
    Returns:
        The best result, or None if no successful results.
    """
    successful = [r for r in results if r.success]
    if not successful:
        return None
    return min(successful, key=lambda r: _score(r, priority_order))


def evaluate_algorithms(
    grid: Grid,
    priority_order: Tuple[str, str, str] = DEFAULT_PRIORITY_ORDER
) -> Tuple[List[SearchResult], Optional[SearchResult]]:
    """Run all algorithms on the grid and find the best one.
    
    Args:
        grid: The grid to run algorithms on.
        priority_order: Tuple of 3 criterion names (cost, nodes, time) in priority order.
                       Default is (cost, nodes, time).
    
    Returns:
        Tuple of (all_results, best_result).
    """
    results: List[SearchResult] = []
    with ThreadPoolExecutor(max_workers=len(ALGORITHMS)) as executor:
        futures = {
            executor.submit(
                lambda func=func, g=grid.clone(), name=name: timed_run(name, lambda: func(g))
            ): name
            for name, func in ALGORITHMS
        }
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:  # pragma: no cover - guardrail
                name = futures[future]
                result = SearchResult(
                    name=name,
                    path=[],
                    cost=float("inf"),
                    explored_nodes=0,
                    duration=0.0,
                    success=False,
                    visited_order=[],
                )
            results.append(result)

    best = select_best(results, priority_order)
    # Sort results for consistent display
    results.sort(key=lambda r: (r.name))
    return results, best

