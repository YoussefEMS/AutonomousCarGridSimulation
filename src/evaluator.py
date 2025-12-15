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
)
from src.algorithms.base import timed_run


AlgorithmEntry = Tuple[str, Callable[[Grid], SearchResult]]


ALGORITHMS: List[AlgorithmEntry] = [
    ("BFS", bfs),
    ("DFS", dfs),
    ("Uniform Cost", uniform_cost_search),
    ("Greedy Best-First", greedy_best_first),
    ("A*", a_star_search),
    ("IDA*", ida_star_search),
    ("Bidirectional", bidirectional_search),
]


def _score(result: SearchResult) -> Tuple[float, int, float]:
    return (result.cost, result.explored_nodes, result.duration)


def evaluate_algorithms(grid: Grid) -> Tuple[List[SearchResult], Optional[SearchResult]]:
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

    successful = [r for r in results if r.success]
    best = min(successful, key=_score) if successful else None
    # Sort results for consistent display
    results.sort(key=lambda r: (r.name))
    return results, best
