# Autonomous Car Grid Simulation

GUI-based simulator that runs seven search algorithms on the same grid, compares their performance, and visualizes the optimal path.

## Features
- Preset grids (5x5, 10x10, 15x15, maze, weighted) or deterministic custom random grids with obstacles and weights.
- Algorithms: BFS, DFS, Uniform Cost, Greedy Best-First, A*, IDA*, Bidirectional.
- Metrics: path cost, explored nodes, execution time. Automatic optimal selection (cost → nodes → time).
- Tkinter GUI with start/pause/resume/reset controls, speed slider, live exploration animation, final path highlighting, and a car sprite (asset at `assets/car.png`, with a base64 fallback in `src/app.py`) that drives along the finished path.
- Analytics overlay: Visualization screen features a **Show Analytics** button (implemented in `src/app.py` → `VisualizationFrame.show_analytics_overlay`) that plots per-algorithm bar charts for `SearchResult.cost`, `SearchResult.explored_nodes`, and `SearchResult.duration` using embedded matplotlib.

## Run
```bash
python -m src.app
```
Requires Python 3 with Tkinter available (bundled in standard CPython).

## Usage
1. Choose a preset or enter custom grid parameters (rows/cols, obstacle ratio, weighted ratio).
2. Click **Start**. When prompted, choose whether to use the preset; select "No" to use custom settings.
3. Watch exploration animate; pause/resume as needed. Final optimal algorithm and metrics appear in the side panel along with per-algorithm comparisons, and once the path is ready a car drives the route. After each run, click **Show Analytics** to open the chart overlay for time, cost, and nodes explored.
4. Click **Reset** to clear the canvas and run again.

## Structure
- `src/grid.py` — grid model, weights, random generation.
- `src/presets.py` — preset grid definitions.
- `src/algorithms/` — implementations of the seven algorithms and shared helpers.
- `src/evaluator.py` — runs algorithms (threaded) and selects the optimal result.
- `src/app.py` — Tkinter GUI and visualization.
