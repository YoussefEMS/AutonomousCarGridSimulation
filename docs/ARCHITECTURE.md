# Architecture Overview

This document explains how the autonomous-car grid simulation is structured today. The source of truth is the Tkinter implementation in `src/app.py`; everything below reflects the current codebase behavior.

## High-level layout

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│Grid presets │ -> │Simulator GUI│ -> │Visualization │
└─────────────┘    └─────────────┘    └──────────────┘
        │                │                      │
        │                ├─ evaluate_algorithms ┤
        │                │                      │
        ▼                ▼                      ▼
   src/presets.py   src/evaluator.py      Canvas + overlays
```

- The **Setup frame** gathers configuration data (preset, custom grid parameters, algorithm selection, priority order). All controls now sit inside a scrollable panel with a fixed action bar containing the “Show weights on grid” toggle and the **Start Visualization** CTA.
- The **Visualization frame** owns the Tk canvas, playback buttons, comparison tools, weight editing mode, analytics button, and results areas.
- `SimulatorGUI` orchestrates the two frames plus shared state (`current_grid`, `priority_order`, `results`, etc.).

## Core modules

| Module | Responsibility |
| --- | --- |
| `src/app.py` | UI, state management, queueing runs, animations (exploration, path, car sprite), analytics overlay. |
| `src/grid.py` | Grid data structure, weighted cells, random grid factory, movement cost calculation. |
| `src/evaluator.py` | Runs all algorithms concurrently via `ThreadPoolExecutor`, builds `SearchResult` objects, picks the “best” according to the current priority tuple. |
| `src/algorithms/*` | Search strategy implementations; each returns a `SearchResult` (path, cost, nodes explored, duration, success flag, visited order). |
| `src/weight_utils.py` | Helpers for cycling weights `[1, 2, 3, 5, 10]` and detecting custom weights. |
| `tests/test_priority_order.py` & `tests/test_weight_editing.py` | Unit coverage for evaluator scoring and weight persistence/cost impact. |
| `assets/car.png` | Base PNG used for the animated sprite (rotated/scaled at runtime; inline base64 fallback covers headless machines). |

## Data + control flow

1. **Setup frame**
   - User picks a preset or custom parameters, optionally changes algorithm priority order with the drag control (`RankOrderControl`).
   - “Start Visualization” remains enabled once a grid exists (either loaded preset or freshly built).

2. **Running algorithms**
   - `SimulatorGUI.start_simulation()` ensures the visualization frame is visible, then calls `run_simulation()`.
   - `run_simulation()` clones the grid and queues evaluation on a background thread.
   - `evaluate_algorithms()` runs every algorithm, timing each call. The `priority_order` tuple determines the lexicographic comparison used by `select_best()` (default `cost → nodes → time`). The results list and the best entry are stored back on the controller.

3. **Visualization frame**
   - When `_after_algorithms()` fires, the UI either displays the user-selected algorithm or falls back to `best_result`. Any run populates the “Optimal Algorithm” panel, the textual results list, and enables the **Show Analytics** button.
   - The canvas animates two phases: visited cell highlighting (`animate_exploration`) then the final path (`animate_path`).
   - After the final path is drawn, `_start_car_animation()` animates `assets/car.png` (rotated via PIL per direction) along the path using the same speed slider. Pause/resume/reset/rerun all stop the sprite cleanly.

4. **Analytics overlay**
   - A Toplevel window shows three matplotlib bar charts (duration ms, cost, nodes explored). Failed algorithms are excluded and noted in the footer.
   - The overlay is modal via `grab_set()` and can be dismissed via the Close button or Esc.

5. **Weight editing**
   - The Visualization sidebar exposes “Edit weights (paint mode)” and “Reset Weights.”
   - When enabled, clicking or dragging cycles weights in `[1, 2, 3, 5, 10]` so the destination cell cost reflects the new weight. Start/goal and wall cells are locked.
   - Resetting removes every custom weight (except walls) and redraws the grid.
   - Any edit sets `weights_dirty`, disables analytics until the user re-runs, and updates the setup summary to note “Custom weights applied: Yes.”

6. **State reset**
   - `Reset Run` clears animation state but keeps the grid.
   - `Full Reset` wipes everything, clears the canvas, deletes analytics text, resets weight-edit toggles, and returns to the Setup frame.

## Files + assets

```
src/
  app.py              # Tkinter GUI, animations, analytics overlay
  evaluator.py        # Threaded execution + ranking
  grid.py             # Grid + cell definitions
  weight_utils.py     # Weight cycling + detection helpers
  algorithms/         # Each search implementation + base helpers
assets/
  car.png             # Sprite used in Visualization car animation
docs/
  ...                 # Maintained per README guidance
tests/
  test_priority_order.py
  test_weight_editing.py
```

---
Last verified: 2025-12-23  
Commit: local-working-tree  
Verified by: Codex Assistant
