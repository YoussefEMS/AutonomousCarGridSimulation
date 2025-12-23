# Contributing Guide

Thank you for helping improve the Autonomous Car Grid Simulation. This guide explains how to make changes that align with the current offline Tkinter implementation.

## Ground rules

1. **Stay offline** – no network calls, telemetry, or cloud dependencies.
2. **Keep both screens usable** – verify the Setup scroll container and action bar still expose the Start + Show weights controls on laptop screen sizes.
3. **Protect algorithm correctness** – weight editing, priority order, and analytics must reflect real `SearchResult` data.
4. **Animate responsibly** – pause/resume/reset/rerun must stop any exploration, path, or car animations you add.

## Development workflow

1. Create a virtual environment (optional but recommended).
2. Install optional extras if needed:
   ```
   pip install pillow matplotlib pytest
   ```
3. Run the app: `python -m src.app`.
4. Make changes in `src/` (and `assets/` if updating the car sprite).
5. Run quick checks:
   ```
   python -m py_compile src/app.py src/weight_utils.py
   python -m pytest tests
   ```
6. Exercise both screens manually:
   - Build/load a grid, reorder priorities, start visualization.
   - Toggle weight edit mode, paint a few cells, rerun.
   - Open the analytics overlay.
   - Confirm the car drives the final path and respects pause/resume/reset.
7. Update docs (this folder) whenever UI/behavior changes. Each doc needs an updated “Last verified” footer.

## Code conventions

- Follow existing style: small helper methods, descriptive status strings, minimal new dependencies.
- Use `RankOrderControl` patterns for new drag/drop widgets (Frame + handles + Tk events).
- Keep concurrency limited to the existing `ThreadPoolExecutor` in `evaluate_algorithms`.
- Prefer configuration/state on `SimulatorGUI` so both frames can observe updates.

## Testing

- Unit coverage lives under `tests/`. Add new files when you introduce logic that can be tested without the GUI.
- For GUI features, describe manual verification steps in the PR description.

## Documentation expectations

- Update `docs/` whenever you move controls, change flows, or add features (analytics, weight editing, assets, etc.).
- Reference the doc index (`docs/README.md`) to decide which files are affected.
- Keep terminology consistent (Setup screen, Visualization screen, cost/nodes/time metrics).

## Filing issues / support

- Include environment info (OS, Python version, presence of Pillow/Matplotlib).
- Attach screenshots for UI regressions (especially Setup layout issues).
- Mention whether weights or analytics were enabled when the bug occurred.

---  
Last verified: 2025-12-23  
