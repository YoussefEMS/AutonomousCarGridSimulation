# Codebase Guide

This guide explains how the project is organized and how to work with the current Tkinter implementation. All instructions reflect the code inside `src/`.

## Project layout

```
assets/
  car.png                # default car sprite (rotated/scaled at runtime)
docs/                    # this directory; see docs/README.md
src/
  app.py                 # SimulatorGUI, Setup/Visualization frames, animations
  evaluator.py           # priority-aware ranking + threaded execution
  grid.py                # Grid + Cell, random-grid utilities, cost calculations
  weight_utils.py        # weight cycling + detection helpers
  algorithms/            # BFS, DFS, UCS, Greedy, A*, IDA*, Bidirectional variants
tests/
  test_priority_order.py # evaluator scoring contract
  test_weight_editing.py # weight persistence + cost effects
```

## Running the GUI

```
python -m src.app
```

Requirements:

- Python 3.x with Tkinter installed (bundled with standard CPython).
- Optional: Pillow (`pip install pillow`) for rotated car sprites. Without it, the fallback rectangle is used.
- Optional: `pytest` for automated tests.

## Application flow

1. **Setup screen**
   - Scrollable configuration sections (Preset Grid, Custom Grid Settings, Algorithm Selection, Best Algorithm Priority).
   - Action bar pinned to the bottom: “Show weights on grid” toggle and the **Start Visualization** button (disabled until a grid is ready).
   - Drag/drop priority control (`RankOrderControl`) determines the tuple passed into `evaluate_algorithms`.

2. **Visualization screen**
   - Canvas showing the grid, exploration, path, and car animation.
   - Playback controls (Run, Pause, Resume, Reset Run, Full Reset) that influence both the algorithm animation and the car sprite.
   - Tinkering controls (algorithm quick switch, “Re-run,” “Show weights” checkbox).
   - Weight editing block (“Edit weights (paint mode)” + cycle instructions + “Reset Weights”).
   - Analytics button that opens a modal overlay with three bar charts once results exist.
   - Results panes showing best algorithm summary and full per-algorithm metrics.

## Key features

### Grid building

- Presets come from `src/presets.py`.
- Custom grids use user-entered rows/cols/ratio values and `Grid.random_grid`.
- “Build Custom Grid” stores the generated grid in `SimulatorGUI.current_grid` and updates the summary.

### Algorithm evaluation

- `evaluate_algorithms()` executes every algorithm on a cloned grid in parallel (`ThreadPoolExecutor`).
- Each function returns a `SearchResult` with `path`, `cost`, `explored_nodes`, `duration`, `success`, `visited_order`.
- `select_best()` applies the tuple extracted from `RankOrderControl` (default `("cost","nodes","time")`).
- The Setup summary always shows the active priority order string.

### Visualization

- `animate_exploration` sequentially colors visited cells using the speed slider.
- `animate_path` highlights the final route, builds informational text, and sets `viz_info_var`.
- After the path animation, `_start_car_animation()` moves `assets/car.png` (rotated via Pillow) cell-by-cell. The sprite respects pause/resume/reset and is removed on rerun/full reset.
- The analytics overlay displays three bar charts (duration ms, cost, nodes) using matplotlib; failed algorithms are excluded.

### Weight editing

- Enable “Edit weights (paint mode)” to cycle weights `[1,2,3,5,10]` by clicking or dragging. Start/goal/wall cells are locked.
- Weight changes update the grid data (`Grid.cells`) so subsequent runs use the new costs.
- “Reset Weights” removes all custom weights and redraws the grid.
- Any edit marks analytics as stale until the user reruns algorithms.

### Show weights

- Toggle lives in the Setup action bar and Tinkering panel.
- When enabled, every drawn cell displays its weight text; color intensity also conveys higher weights.

## Developer workflows

### Running lint/tests

```
python -m py_compile src/app.py src/weight_utils.py
python -m pytest tests
```

### Common entry points

| Location | Purpose |
| --- | --- |
| `SimulatorGUI.start_simulation` | Button handler for “Start Visualization” on the Setup screen. |
| `SimulatorGUI.rerun_simulation` | Retains the current grid/weights, clears overlays, reruns algorithms. |
| `SimulatorGUI.toggle_weight_edit_mode` | Bound to the Visualization weight-edit checkbox. |
| `VisualizationFrame.show_analytics_overlay` | Builds the analytics modal. |
| `VisualizationFrame.update_analytics_button_state` | Called whenever results change or weights become stale. |

### Adding features

1. Modify `src/` modules. Keep offline guarantees (no HTTP).
2. Update tests or add new ones under `tests/`.
3. Re-run the GUI to ensure new controls fit (remember the Setup scroll container and pinned action bar).
4. Update docs per `docs/README.md`.

---  
Last verified: 2025-12-23  
