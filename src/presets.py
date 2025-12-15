from __future__ import annotations

from typing import Dict, Tuple

from src.grid import Grid


PRESETS: Dict[str, Grid] = {}


def _make_presets() -> None:
    global PRESETS
    PRESETS = {
        "5x5": Grid.with_defaults(
            rows=5,
            cols=5,
            start=(0, 0),
            goal=(4, 4),
            obstacles={(1, 1), (1, 2), (2, 1)},
        ),
        "10x10": Grid.with_defaults(
            rows=10,
            cols=10,
            start=(0, 0),
            goal=(9, 9),
            obstacles={(3, 3), (3, 4), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5)},
        ),
        "15x15": Grid.with_defaults(
            rows=15,
            cols=15,
            start=(0, 0),
            goal=(14, 14),
            obstacles={(5, i) for i in range(1, 14)} | {(i, 7) for i in range(3, 12)},
        ),
        "Maze": Grid.with_defaults(
            rows=10,
            cols=10,
            start=(0, 0),
            goal=(9, 9),
            obstacles={
                (1, i) for i in range(1, 9)
            }
            | {(i, 1) for i in range(2, 9)}
            | {(8, i) for i in range(2, 9)}
            | {(i, 8) for i in range(2, 9)},
        ),
        "Weighted": Grid.with_defaults(
            rows=8,
            cols=8,
            start=(0, 0),
            goal=(7, 7),
            obstacles={(3, 3), (3, 4), (4, 3)},
            weights={
                (1, 1): 3,
                (2, 2): 2.5,
                (2, 5): 4,
                (5, 2): 2,
                (6, 6): 5,
            },
            default_weight=1.0,
        ),
    }


_make_presets()


def get_preset(name: str) -> Grid:
    return PRESETS.get(name, PRESETS["5x5"]).clone()


def list_presets() -> Tuple[str, ...]:
    return tuple(PRESETS.keys())

