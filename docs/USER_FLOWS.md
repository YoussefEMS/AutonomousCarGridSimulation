# User Flows

Step-by-step guides for common tasks within the Autonomous Car Grid Simulation. These flows reflect the latest two-screen UI (scrollable Setup + Visualization with weight editing, analytics, and the car sprite).

## 1. Launch the simulator

```
python -m src.app
```

The Setup screen appears first.

## 2. Configure a grid

1. **Choose a preset**  
   - Open the “Preset Grid” combo, pick a configuration, click “Load Preset.”  
   - The summary on the right updates.
2. **OR build a custom grid**  
   - Enter rows/cols + obstacle & weighted ratios + seed.  
   - Click “Build Custom Grid.”
3. **Adjust algorithm selection**  
   - Choose a specific algorithm or keep “Auto (best).”
4. **Set priority order**  
   - Drag the handles in “Best Algorithm Priority” to reorder Cost, Nodes explored, Time taken.  
   - Status text updates with the new order.
5. **Start Visualization**  
   - The action bar at the bottom always displays “Show weights on grid” and **Start Visualization**. Ensure Start is enabled, toggle weights if desired, then click Start.

## 3. Visualize and compare algorithms

1. Click **Run** (or it auto-runs after Start).  
2. Watch the exploration phase (blue), then the path phase (yellow).  
3. After the path completes, the car sprite drives from start to goal, rotating toward each direction.  
4. The right panes show:
   - Optimal algorithm summary.
   - Per-algorithm metrics text box.
   - Analytics button (enabled once results exist).
5. Playback controls:  
   - Pause/resume stops/continues both the algorithm animation and the car.  
   - Reset Run clears overlays but keeps the grid.  
   - Full Reset clears everything and returns to Setup.

## 4. Weight editing workflow

1. Enable **Edit weights (paint mode)** in the “Weight Editing” group.  
2. Click or drag across walkable cells to cycle weights `[1,2,3,5,10]`. Start, goal, and walls are locked.  
3. The canvas updates immediately; the Setup summary reports “Custom weights applied: Yes.”  
4. Click **Reset Weights** to revert all non-wall weights to 1.  
5. Press **Re-run** (in the Tinkering block) to execute algorithms with the updated costs. Analytics re-enable after the rerun.

## 5. Analytics overlay

1. After a run finishes, click **Show Analytics** in the Results frame.  
2. A modal overlay appears with three bar charts:  
   - Duration (milliseconds)  
   - Cost  
   - Nodes explored  
3. Failed algorithms are excluded and listed below the charts.  
4. Close the overlay via the button or the Esc key.

## 6. Switching algorithms manually

1. In the Tinkering block, choose another algorithm from the dropdown.  
2. Click **Re-run** to execute only that algorithm and update the visualization.  
3. If the selected algorithm fails, the UI falls back to the previously computed best result while warning the user.

## 7. Returning to Setup

1. Click “← Back to Setup” on the Visualization screen.  
2. The Setup summary reflects the latest run (including weight edits).  
3. You can immediately change priorities or build another grid and press **Start Visualization** again.

---  
Last verified: 2025-12-23  
