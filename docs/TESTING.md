# Testing Guide

The simulator ships with lightweight automated tests and several manual scenarios. This document explains how to keep coverage in sync with the current features (priority ordering, weight editing, analytics, car animation).

## Quick checks

```
python -m py_compile src/app.py src/weight_utils.py
python -m pytest tests
```

- `py_compile` catches syntax errors in the main modules.
- `pytest` runs:
  - `tests/test_priority_order.py` (scoring tuple + selection logic)
  - `tests/test_weight_editing.py` (weight persistence and path cost impact)

## Installing pytest (if missing)

```
pip install pytest
```

## Manual verification matrix

| Area | Scenario | Expected result |
| --- | --- | --- |
| Setup screen layout | Resize window to ~1366×768 | Scroll container engages, action bar with “Show weights” + “Start Visualization” stays visible. |
| Priority order | Drag “Time taken” to the top, run Auto(best) | Best algorithm summary should reflect the new order. |
| Algorithm execution | Run with preset and custom grid | Results panel lists all algorithms, analytics button enabled. |
| Weight editing | Enable edit mode, paint weights, rerun | Canvas redraws weights, analytics disabled until rerun, new path respects heavier cells. |
| Reset weights | Click “Reset Weights” | All non-wall weights revert to 1; summary shows “Custom weights applied: No.” |
| Analytics overlay | After a run, click “Show Analytics” | Modal opens with three bar charts, Esc closes overlay. |
| Car animation | Let a run finish | Car sprite drives path, rotates per direction; pause/resume/ reset stops movement immediately. |
| Full reset | Click “Full Reset” from Visualization | Canvas clears, analytics + results text cleared, Setup screen shown. |

## Adding tests

- Favor pure-Python helpers (`weight_utils.next_weight_value`, evaluator scoring) for new unit tests.
- For Tkinter-heavy behavior, document manual test steps in PR descriptions.
- Keep tests offline and deterministic (set seeds when building grids).

---  
Last verified: 2025-12-23  
