# Onboarding Guide

Welcome! This quickstart walks a new developer through installing dependencies, running the app, and exploring key features.

## 1. Install prerequisites

- Python 3.x with Tkinter (bundled in the standard installer).
- Optional but recommended:
  ```
  pip install pillow matplotlib pytest
  ```
  Pillow enables rotated car sprites, matplotlib powers the analytics overlay, and pytest runs the unit tests.

## 2. Run the simulator

```
python -m src.app
```

Two windows (Setup and Visualization) live inside the same Tk root; the simulator switches between them when you click **Start Visualization** or **Back to Setup**.

## 3. Explore the Setup screen

- The left column is scrollable; key sections:
  1. **Preset Grid** – pick a named layout and click “Load Preset.”
  2. **Custom Grid Settings** – rows/cols/obstacle & weighted ratios, seed, plus “Build Custom Grid.”
  3. **Algorithm Selection** – choose a specific algorithm or “Auto (best).”
  4. **Best Algorithm Priority** – drag criteria (Cost, Nodes explored, Time taken) to reorder the ranking tuple.
- The bottom action bar is always visible. Use:
  - “Show weights on grid” toggle (applies globally).
  - **Start Visualization** (primary CTA, disabled until a grid exists).

## 4. Visualization screen tour

- **Navigation** – “Back to Setup” returns to configuration.
- **Playback controls** – Run / Pause / Resume / Reset Run / Full Reset plus a speed slider.
- **Tinkering** – switch algorithms, rerun, show weights toggle, weight editing mode, reset weights.
- **Canvas** – displays exploration, final path, and the car sprite driving along the finished route.
- **Analytics** – button at the bottom of the Results pane opens a modal with three bar charts (time, cost, nodes) after a run finishes.
- **Weight editing** – enable “Edit weights (paint mode)” to click/drag cells; weights cycle `[1,2,3,5,10]`. “Reset Weights” clears custom weights.

## 5. Verify behaviors

1. Load a preset, press **Start Visualization**, watch algorithms run.
2. Change the priority order (e.g., Time → Cost → Nodes) and rerun; note that the “Best Algorithm” text updates.
3. Enable weight edit mode, paint heavier weights along part of the map, rerun, and see the new path + analytics.
4. Pause mid-run, then resume; confirm both exploration and the car continue from the right step.
5. Open the analytics overlay and verify the metrics match the textual results.

## 6. Update docs after changes

- Whenever you move controls or add new actions, edit the relevant doc(s) plus `docs/README.md`.
- Remember to update the “Last verified” footer.

---  
Last verified: 2025-12-23  
Commit: local-working-tree  
Verified by: Codex Assistant
