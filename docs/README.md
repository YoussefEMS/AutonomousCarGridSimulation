# Documentation Index

All docs describe the current offline Tkinter implementation of the Autonomous Car Grid Simulation. Start here to figure out which guide you need.

## When to read what

- **ONBOARDING.md** ― first hour experience; install Python, run the app, and understand the two-screen workflow.
- **USER_FLOWS.md** ― task-oriented instructions (build grid, tweak priorities, edit weights, rerun, view analytics).
- **CODEBASE_GUIDE.md** ― deep dive into modules, state management, and how evaluation + visualization connect.
- **ARCHITECTURE.md** ― system-level view (data structures, algorithm execution pipeline, canvas rendering, animation).
- **TESTING.md** ― describes automated/unit tests, manual checks, and how to validate algorithm behavior after edits.
- **TROUBLESHOOTING.md** ― quick answers for missing Tk/Tcl, car sprite issues, analytics button disabled, etc.
- **CONTRIBUTING.md** ― coding standards, review expectations, doc update checklist.

## Key terms

- **Setup screen** ― the first frame (Preset, Custom settings, Algorithm selection, Best Algorithm Priority, Start Visualization + Show weights action bar).
- **Visualization screen** ― the second frame (grid canvas, playback controls, weight editing tools, analytics button, results panes).
- **Priority order** ― tuple of `("cost", "nodes", "time")` (reorderable) that drives Auto(best) selection.
- **Run / Re-run** ― “Run” executes all algorithms on the current grid; “Re-run” reuses the same grid and updated weights.
- **Analytics overlay** ― modal charts (time, cost, nodes) built with matplotlib after a successful run.
- **Weight editing mode** ― toggleable paint mode that cycles weights `[1,2,3,5,10]`, supports drag, and can be reset.
- **Car sprite** ― PNG at `assets/car.png` (PhotoImage fallback inline) that drives along the finished path.

## Keeping docs updated

1. Make functional changes in `src/`.
2. Re-run the app and note UI/responses that changed.
3. Update all impacted docs (at minimum this README and CODEBASE_GUIDE).
4. Append/refresh the verification footer with the current date + commit hash (or local state note).
5. When unsure, prefer deleting stale text over keeping incorrect statements.

---
Last verified: 2025-12-23  
