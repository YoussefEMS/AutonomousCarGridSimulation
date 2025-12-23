# Troubleshooting Guide

Use this reference when the simulator behaves unexpectedly. All fixes assume the current Tkinter codebase in `src/`.

## The app fails to launch (Tkinter import errors)

- Confirm you are using the standard CPython installer with Tk support.
- On Linux, install `python3-tk`.
- On macOS, avoid the Homebrew “frameworkless” build; use the official installer.

## “Start Visualization” stays disabled

- A grid has not been loaded/built yet. Load a preset (“Load Preset”) or click “Build Custom Grid.”
- If a previous Full Reset cleared the grid, rebuild before pressing Start.

## Scroll wheel doesn’t move the Setup sections

- Ensure the mouse pointer is over the left scroll area (inside the “Configuration” frame). The new canvas-based scroller only listens while focused.

## Analytics button is disabled

- Analytics require at least one successful run. Run the algorithms first.
- Weight editing or resetting weights disables analytics until you rerun.

## Analytics overlay shows nothing / crashes

- Matplotlib is required. Install with `pip install matplotlib`.
- The overlay only includes successful algorithms. Failures are listed as “Excluded failed algorithms …”.

## Car sprite missing or unrotated

- Pillow is optional but recommended. Install with `pip install pillow`.
- Without Pillow, the app falls back to a simple rectangle and cannot rotate.
- If `assets/car.png` is missing, the inline base64 fallback is used automatically.

## Car keeps moving after reset

- Expected behavior: `Reset Run` and `Full Reset` both call `_stop_car_animation()`. If you still see motion, ensure no custom modifications cancelled the car animation job.

## Weight editing does nothing

- Verify “Edit weights (paint mode)” is checked.
- Start/goal/wall cells are locked; paint on walkable cells.
- Dragging outside the grid is ignored.

## Weighted cells render without numbers

- Enable “Show weights on grid” (Setup action bar or Visualization Tinkering panel).
- Numeric overlays are only drawn when the checkbox is on.

## “Rank order updated” message never goes away

- This is informational. Once you rerun the algorithms, the status text changes to the run status.

## Running tests fails with “No module named pytest”

- Install pytest locally (`pip install pytest`) or run only the `py_compile` check.

---  
Last verified: 2025-12-23  
