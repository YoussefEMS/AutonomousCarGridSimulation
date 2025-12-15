from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple
import random
import copy

Position = Tuple[int, int]


@dataclass(frozen=True)
class Cell:
    """Represents a single grid cell."""

    weight: float = 1.0
    obstacle: bool = False


@dataclass
class Grid:
    rows: int
    cols: int
    start: Position = (0, 0)
    goal: Position = (0, 0)
    cells: Dict[Position, Cell] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.rows = int(self.rows)
        self.cols = int(self.cols)
        self.start = self._clamp(self.start)
        self.goal = self._clamp(self.goal)

    def _clamp(self, pos: Position) -> Position:
        r, c = pos
        return (max(0, min(self.rows - 1, r)), max(0, min(self.cols - 1, c)))

    def clone(self) -> "Grid":
        """Deep copy used so algorithms operate on identical instances."""
        return copy.deepcopy(self)

    @classmethod
    def with_defaults(
        cls,
        rows: int,
        cols: int,
        start: Optional[Position] = None,
        goal: Optional[Position] = None,
        obstacles: Optional[Iterable[Position]] = None,
        weights: Optional[Dict[Position, float]] = None,
        default_weight: float = 1.0,
    ) -> "Grid":
        start = start if start is not None else (0, 0)
        goal = goal if goal is not None else (rows - 1, cols - 1)
        cells: Dict[Position, Cell] = {}
        if obstacles:
            for pos in obstacles:
                pos = (int(pos[0]), int(pos[1]))
                cells[pos] = Cell(weight=default_weight, obstacle=True)
        if weights:
            for pos, w in weights.items():
                pos = (int(pos[0]), int(pos[1]))
                if cells.get(pos, Cell()).obstacle:
                    continue
                cells[pos] = Cell(weight=float(w), obstacle=False)
        return cls(rows=rows, cols=cols, start=start, goal=goal, cells=cells)

    def in_bounds(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_walkable(self, pos: Position) -> bool:
        if not self.in_bounds(pos):
            return False
        cell = self.cells.get(pos)
        return not (cell.obstacle if cell else False)

    def get_weight(self, pos: Position) -> float:
        cell = self.cells.get(pos)
        return cell.weight if cell else 1.0

    def neighbors(self, pos: Position) -> List[Position]:
        r, c = pos
        candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        return [p for p in candidates if self.is_walkable(p)]

    def cost(self, current: Position, neighbor: Position) -> float:
        # Movement cost is the weight of the destination cell.
        return self.get_weight(neighbor)

    def as_matrix(self) -> List[List[Cell]]:
        matrix: List[List[Cell]] = []
        for r in range(self.rows):
            row: List[Cell] = []
            for c in range(self.cols):
                row.append(self.cells.get((r, c), Cell()))
            matrix.append(row)
        return matrix

    @staticmethod
    def random_grid(
        rows: int,
        cols: int,
        obstacle_ratio: float = 0.2,
        weighted_ratio: float = 0.2,
        weight_range: Tuple[float, float] = (1.5, 5.0),
        seed: Optional[int] = None,
    ) -> "Grid":
        rng = random.Random(seed)
        obstacles: Set[Position] = set()
        weights: Dict[Position, float] = {}

        for r in range(rows):
            for c in range(cols):
                if (r, c) in [(0, 0), (rows - 1, cols - 1)]:
                    continue
                roll = rng.random()
                if roll < obstacle_ratio:
                    obstacles.add((r, c))
                elif roll < obstacle_ratio + weighted_ratio:
                    weights[(r, c)] = round(rng.uniform(*weight_range), 2)

        return Grid.with_defaults(
            rows=rows,
            cols=cols,
            start=(0, 0),
            goal=(rows - 1, cols - 1),
            obstacles=obstacles,
            weights=weights,
        )

