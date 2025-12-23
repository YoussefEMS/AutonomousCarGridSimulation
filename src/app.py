from __future__ import annotations

import base64
import io
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import math
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.grid import Grid, Cell
from src.evaluator import evaluate_algorithms, PRIORITY_CRITERIA, DEFAULT_PRIORITY_ORDER, select_best
from src.presets import get_preset, list_presets
from src.algorithms import SearchResult
from src.algorithms.base import path_cost
from src.weight_utils import next_weight_value, grid_has_custom_weights, WEIGHT_CYCLE_VALUES

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - optional dependency
    Image = None
    ImageTk = None


CANVAS_SIZE = 620
DEFAULT_SPEED_MS = 120
CAR_SPRITE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAKCAYAAAC9vt6cAAAAJElEQVR4nGNgoAXgL8v7jw2TpYlow4aBAXKa1v9JwYPQAHIBAGFPnzGvz+hPAAAAAElFTkSuQmCC"
)
CAR_IMAGE_PATH = Path(__file__).resolve().parent.parent / "assets" / "car.png"
ALGORITHM_OPTIONS = [
    "Auto (best)",
    "BFS",
    "DFS",
    "Uniform Cost",
    "Greedy Best-First",
    "A*",
    "IDA*",
    "Bidirectional",
    "Bidirectional Astar"
]

# Priority criteria display names
PRIORITY_DISPLAY_NAMES = {
    "cost": "Cost",
    "nodes": "Nodes explored",
    "time": "Time taken",
}


def reorder_priority(order: List[str], from_index: int, to_index: int) -> List[str]:
    """Return a new priority order with the item moved from one slot to another."""
    current = list(order)
    if from_index == to_index:
        return current
    if not (0 <= from_index < len(current)) or not (0 <= to_index < len(current)):
        return current
    item = current.pop(from_index)
    current.insert(to_index, item)
    return current


class RankOrderControl(tk.Frame):
    """Drag-to-reorder widget for ranking algorithm priority criteria."""

    DRAG_BG = "#dbeafe"
    ROW_BG = "#f8fafc"
    TARGET_BORDER = "#2563eb"
    IDLE_BORDER = "#cbd5f5"

    def __init__(
        self,
        parent: tk.Frame,
        items: List[Tuple[str, str]],
        order: Optional[List[str]] = None,
        on_change: Optional[Callable[[Tuple[str, ...]], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.items_by_key = {key: label for key, label in items}
        self.on_change = on_change
        incoming_order = order or [key for key, _ in items]
        self.order: List[str] = self._normalize_order(incoming_order)
        self.row_widgets: Dict[str, tk.Frame] = {}
        self.drag_key: Optional[str] = None
        self._target_index: Optional[int] = None

        self.rows_frame = tk.Frame(self, bg=self.ROW_BG)
        self.rows_frame.pack(fill=tk.X, expand=True)

        self._render_rows()

    def _normalize_order(self, incoming: List[str]) -> List[str]:
        normalized: List[str] = []
        for key in incoming:
            if key in self.items_by_key and key not in normalized:
                normalized.append(key)
        for key in self.items_by_key.keys():
            if key not in normalized:
                normalized.append(key)
        return normalized

    def _render_rows(self) -> None:
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.row_widgets.clear()
        for idx, key in enumerate(self.order):
            row_bg = self.DRAG_BG if key == self.drag_key else self.ROW_BG
            row = tk.Frame(
                self.rows_frame,
                bg=row_bg,
                padx=6,
                pady=6,
                highlightthickness=2 if self._target_index == idx else 1,
                highlightbackground=self.TARGET_BORDER if self._target_index == idx else self.IDLE_BORDER,
            )
            row.pack(fill=tk.X, pady=3)
            self.row_widgets[key] = row

            handle = tk.Label(
                row,
                text="≡",
                font=("Arial", 14),
                width=2,
                cursor="fleur",
                bg=row_bg,
            )
            handle.pack(side=tk.LEFT, padx=(0, 8))
            handle.bind("<ButtonPress-1>", lambda e, k=key: self._on_drag_start(k))
            handle.bind("<B1-Motion>", self._on_drag_motion)
            handle.bind("<ButtonRelease-1>", self._on_drag_release)

            info_frame = tk.Frame(row, bg=row_bg)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(
                info_frame,
                text=self.items_by_key[key],
                font=("Arial", 11, "bold"),
                bg=row_bg,
            ).pack(anchor="w")
            tk.Label(
                info_frame,
                text=f"Rank {idx + 1}",
                font=("Arial", 9),
                fg="#4b5563",
                bg=row_bg,
            ).pack(anchor="w")

            button_frame = tk.Frame(row, bg=row_bg)
            button_frame.pack(side=tk.RIGHT, padx=(8, 0))
            btn_up = tk.Button(
                button_frame,
                text="Move up",
                width=7,
                state=tk.NORMAL if idx > 0 else tk.DISABLED,
                command=lambda i=idx: self._manual_move(i, i - 1),
            )
            btn_up.pack(anchor="e", pady=1)
            btn_down = tk.Button(
                button_frame,
                text="Move down",
                width=7,
                state=tk.NORMAL if idx < len(self.order) - 1 else tk.DISABLED,
                command=lambda i=idx: self._manual_move(i, i + 1),
            )
            btn_down.pack(anchor="e", pady=1)

    def _manual_move(self, from_index: int, to_index: int) -> None:
        self._target_index = None
        new_order = reorder_priority(self.order, from_index, to_index)
        if new_order == self.order:
            return
        self.order = new_order
        self.drag_key = None
        self._render_rows()
        self._emit_change()

    def _on_drag_start(self, key: str) -> None:
        self.drag_key = key
        self._render_rows()

    def _on_drag_motion(self, event) -> None:
        if not self.drag_key:
            return
        self.update_idletasks()
        pointer_y = event.y_root
        target_index = self._index_at_pointer(pointer_y)
        if target_index is None:
            return
        self._target_index = target_index
        current_index = self.order.index(self.drag_key)
        if target_index != current_index:
            self.order = reorder_priority(self.order, current_index, target_index)
            self._render_rows()
        else:
            self._update_row_highlights()

    def _on_drag_release(self, event) -> None:
        if not self.drag_key:
            return
        self.drag_key = None
        self._target_index = None
        self._render_rows()
        self._emit_change()

    def _index_at_pointer(self, pointer_y: int) -> Optional[int]:
        indices = list(range(len(self.order)))
        for idx in indices:
            key = self.order[idx]
            row = self.row_widgets.get(key)
            if not row:
                continue
            top = row.winfo_rooty()
            bottom = top + row.winfo_height()
            midpoint = top + (bottom - top) / 2
            if pointer_y < midpoint:
                return idx
        return indices[-1] if indices else None

    def _update_row_highlights(self) -> None:
        for idx, key in enumerate(self.order):
            row = self.row_widgets.get(key)
            if not row:
                continue
            row.configure(
                highlightthickness=2 if self._target_index == idx else 1,
                highlightbackground=self.TARGET_BORDER if self._target_index == idx else self.IDLE_BORDER,
            )

    def _emit_change(self) -> None:
        if self.on_change:
            self.on_change(tuple(self.order))

    def get_order(self) -> Tuple[str, ...]:
        return tuple(self.order)

    def set_order(self, order: List[str]) -> None:
        normalized = self._normalize_order(order)
        if normalized == self.order:
            return
        self.order = normalized
        self.drag_key = None
        self._target_index = None
        self._render_rows()


class SetupFrame(tk.Frame):
    """Screen 1: Grid setup, preset selection, algorithm choice, and configuration."""
    
    def __init__(self, parent: tk.Frame, controller: "SimulatorGUI") -> None:
        super().__init__(parent)
        self.controller = controller
        self.analytics_window: Optional[tk.Toplevel] = None
        self._analytics_canvas: Optional[FigureCanvasTkAgg] = None
        self._build_ui()
    
    def _build_ui(self) -> None:
        # Title
        title_frame = tk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(20, 10))
        tk.Label(
            title_frame, 
            text="Autonomous Car Grid Simulation", 
            font=("Arial", 18, "bold")
        ).pack()
        tk.Label(
            title_frame, 
            text="Setup your grid and algorithm configuration", 
            font=("Arial", 10)
        ).pack()
        
        # Main content frame with two columns
        content_frame = tk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # Left column container with scrollable content + action bar
        left_column = tk.Frame(content_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_column.grid_columnconfigure(0, weight=1)
        
        config_container = tk.LabelFrame(left_column, text="Configuration", padx=0, pady=0)
        config_container.grid(row=0, column=0, sticky="nsew")
        left_column.grid_rowconfigure(0, weight=1)
        
        config_canvas = tk.Canvas(config_container, borderwidth=0, highlightthickness=0)
        config_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        config_scrollbar = tk.Scrollbar(config_container, orient=tk.VERTICAL, command=config_canvas.yview)
        config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        config_canvas.configure(yscrollcommand=config_scrollbar.set)
        
        config_frame = tk.Frame(config_canvas, padx=15, pady=15)
        config_canvas.create_window((0, 0), window=config_frame, anchor="nw")
        
        def _on_config_configure(event):
            config_canvas.configure(scrollregion=config_canvas.bbox("all"))
        
        config_frame.bind("<Configure>", _on_config_configure)
        config_canvas.bind_all(
            "<MouseWheel>",
            lambda e: config_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )
        
        # Preset selection
        tk.Label(config_frame, text="Preset Grid", font=("Arial", 10, "bold")).pack(anchor="w")
        preset_frame = tk.Frame(config_frame)
        preset_frame.pack(anchor="w", fill=tk.X, pady=(2, 10))
        self.preset_combo = ttk.Combobox(
            preset_frame, 
            textvariable=self.controller.preset_var, 
            values=list_presets(), 
            state="readonly", 
            width=18
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(
            preset_frame, 
            text="Load Preset", 
            command=self._load_preset
        ).pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Custom grid settings
        tk.Label(config_frame, text="Custom Grid Settings", font=("Arial", 10, "bold")).pack(anchor="w")
        
        # Grid size
        size_frame = tk.Frame(config_frame)
        size_frame.pack(anchor="w", fill=tk.X, pady=(5, 5))
        tk.Label(size_frame, text="Rows:").pack(side=tk.LEFT)
        tk.Entry(size_frame, textvariable=self.controller.rows_var, width=5).pack(side=tk.LEFT, padx=(5, 15))
        tk.Label(size_frame, text="Cols:").pack(side=tk.LEFT)
        tk.Entry(size_frame, textvariable=self.controller.cols_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # Obstacle ratio
        obs_frame = tk.Frame(config_frame)
        obs_frame.pack(anchor="w", fill=tk.X, pady=5)
        tk.Label(obs_frame, text="Obstacle ratio (0-0.5):").pack(side=tk.LEFT)
        tk.Entry(obs_frame, textvariable=self.controller.obstacle_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # Weight ratio
        wgt_frame = tk.Frame(config_frame)
        wgt_frame.pack(anchor="w", fill=tk.X, pady=5)
        tk.Label(wgt_frame, text="Weighted ratio (0-0.5):").pack(side=tk.LEFT)
        tk.Entry(wgt_frame, textvariable=self.controller.weight_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # Seed
        seed_frame = tk.Frame(config_frame)
        seed_frame.pack(anchor="w", fill=tk.X, pady=5)
        tk.Label(seed_frame, text="Random seed:").pack(side=tk.LEFT)
        tk.Entry(seed_frame, textvariable=self.controller.seed_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # Build custom grid button
        tk.Button(
            config_frame, 
            text="Build Custom Grid", 
            command=self._build_custom_grid,
            width=20
        ).pack(anchor="w", pady=(10, 5))
        
        # Separator
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Algorithm selection
        tk.Label(config_frame, text="Algorithm Selection", font=("Arial", 10, "bold")).pack(anchor="w")
        algo_frame = tk.Frame(config_frame)
        algo_frame.pack(anchor="w", fill=tk.X, pady=5)
        tk.Label(algo_frame, text="Algorithm:").pack(side=tk.LEFT)
        self.algorithm_combo = ttk.Combobox(
            algo_frame,
            textvariable=self.controller.algorithm_var,
            values=ALGORITHM_OPTIONS,
            state="readonly",
            width=18,
        )
        self.algorithm_combo.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(config_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Best Algorithm Priority
        tk.Label(config_frame, text="Best Algorithm Priority", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(config_frame, text="(How to rank algorithms for 'Auto' selection)", font=("Arial", 8)).pack(anchor="w")
        
        self.priority_control = RankOrderControl(
            config_frame,
            items=[(key, PRIORITY_DISPLAY_NAMES[key]) for key in PRIORITY_CRITERIA],
            order=list(self.controller.priority_order),
            on_change=self._on_priority_order_changed,
        )
        self.priority_control.pack(fill=tk.X, pady=6)

        # Pinned action bar
        action_bar = tk.Frame(left_column, pady=10)
        action_bar.grid(row=1, column=0, sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)
        action_bar.grid_columnconfigure(1, weight=0)
        
        tk.Checkbutton(
            action_bar,
            text="Show weights on grid",
            variable=self.controller.show_weights_var,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(10, 10))
        
        self.start_button = tk.Button(
            action_bar,
            text="Start Visualization",
            command=self._start_visualization,
            font=("Arial", 12, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            padx=16,
            pady=8,
            state=tk.DISABLED,
        )
        self.start_button.grid(row=0, column=1, sticky="e", padx=(10, 10))
        
        # Right column: Summary
        summary_frame = tk.LabelFrame(content_frame, text="Configuration Summary", padx=15, pady=15)
        summary_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Summary content
        self.summary_text = tk.Text(summary_frame, height=15, width=35, state="disabled", wrap="word")
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Update summary when values change
        self.controller.preset_var.trace_add("write", lambda *_: self._update_summary())
        self.controller.rows_var.trace_add("write", lambda *_: self._update_summary())
        self.controller.cols_var.trace_add("write", lambda *_: self._update_summary())
        self.controller.obstacle_var.trace_add("write", lambda *_: self._update_summary())
        self.controller.weight_var.trace_add("write", lambda *_: self._update_summary())
        self.controller.algorithm_var.trace_add("write", lambda *_: self._update_summary())
        
        # Initial summary
        self._update_summary()
        self.update_start_button_state()
        self.controller.root.bind("<Return>", self._on_return_pressed)
        
        # Status label
        status_bar = tk.Frame(self)
        status_bar.pack(fill=tk.X, pady=10, padx=40)
        self.status_label = tk.Label(status_bar, textvariable=self.controller.status_var, anchor="w")
        self.status_label.pack(fill=tk.X)
    
    def _load_preset(self) -> None:
        """Load selected preset and update summary."""
        preset_name = self.controller.preset_var.get()
        try:
            grid = get_preset(preset_name)
            self.controller.current_grid = grid
            self.controller.grid_source = "preset"
            self.controller.status_var.set(f"Loaded preset: {preset_name}")
            self._update_summary()
            self.update_start_button_state()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {e}")
    
    def _build_custom_grid(self) -> None:
        """Build custom grid from current settings."""
        try:
            grid = self.controller.build_grid()
            self.controller.current_grid = grid
            self.controller.grid_source = "custom"
            self.controller.status_var.set("Built custom grid")
            self._update_summary()
            self.update_start_button_state()
        except Exception:
            pass  # Error already shown by build_grid
    
    def _update_summary(self) -> None:
        """Update the summary panel with current configuration."""
        grid = self.controller.current_grid
        
        lines = []
        lines.append("=== Grid Configuration ===\n")
        
        if grid:
            lines.append(f"Grid Size: {grid.rows} × {grid.cols}")
            lines.append(f"Start: {grid.start}")
            lines.append(f"Goal: {grid.goal}")
            
            # Count obstacles and weighted cells
            obstacles = sum(1 for cell in grid.cells.values() if cell.obstacle)
            weighted = sum(1 for cell in grid.cells.values() if cell.weight > 1)
            lines.append(f"Obstacles: {obstacles}")
            lines.append(f"Weighted cells: {weighted}")
            lines.append(f"Source: {self.controller.grid_source or 'Not set'}")
            lines.append(f"Custom weights applied: {'Yes' if self.controller.has_custom_weights() else 'No'}")
        else:
            lines.append("No grid loaded yet.")
            lines.append(f"\nPending Settings:")
            lines.append(f"  Rows: {self.controller.rows_var.get()}")
            lines.append(f"  Cols: {self.controller.cols_var.get()}")
            lines.append(f"  Obstacle ratio: {self.controller.obstacle_var.get()}")
            lines.append(f"  Weight ratio: {self.controller.weight_var.get()}")
            lines.append(f"Custom weights applied: {'Yes' if self.controller.has_custom_weights() else 'No'}")
        
        lines.append(f"\n=== Algorithm ===\n")
        lines.append(f"Selected: {self.controller.algorithm_var.get()}")
        
        lines.append(f"\n=== Best Algorithm Priority ===\n")
        lines.append(f"Best by: {self.controller.get_priority_display_string()}")
        
        lines.append(f"\n=== Options ===\n")
        lines.append(f"Show weights: {'Yes' if self.controller.show_weights_var.get() else 'No'}")
        
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "\n".join(lines))
        self.summary_text.configure(state="disabled")

    def update_start_button_state(self) -> None:
        """Enable or disable the start button depending on grid availability."""
        if not hasattr(self, "start_button"):
            return
        state = tk.NORMAL if self.controller.current_grid else tk.DISABLED
        self.start_button.configure(state=state)

    def _start_visualization(self) -> None:
        """Handle Start Visualization button press."""
        if self.controller.current_grid is None:
            messagebox.showinfo("Build Grid", "Build or load a grid first.")
            self.controller.status_var.set("Build or load a grid first.")
            return
        self.controller.start_simulation()

    def _on_return_pressed(self, event) -> None:
        """Start visualization when Enter is pressed on the setup screen."""
        if self.controller.current_screen is not self:
            return
        if getattr(self, "start_button", None) is None:
            return
        if str(self.start_button["state"]) == tk.NORMAL:
            self._start_visualization()
    
    def _on_priority_order_changed(self, order: Tuple[str, ...]) -> None:
        """Update controller when the ranked order changes."""
        self.controller.set_priority_order(list(order))
        self._update_summary()
    
class VisualizationFrame(tk.Frame):
    """Screen 2: Grid visualization, animation controls, and tinkering tools."""
    
    def __init__(self, parent: tk.Frame, controller: "SimulatorGUI") -> None:
        super().__init__(parent)
        self.controller = controller
        self.analytics_window: Optional[tk.Toplevel] = None
        self._build_ui()
    
    def _build_ui(self) -> None:
        # Main layout: controls on left, canvas on right
        
        # Canvas (right side)
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.grid_canvas = tk.Canvas(canvas_frame, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
        self.grid_canvas.pack()
        self.grid_canvas.bind("<Button-1>", self.controller.on_canvas_click)
        self.grid_canvas.bind("<B1-Motion>", self.controller.on_canvas_drag)
        self.grid_canvas.bind("<ButtonRelease-1>", self.controller.on_canvas_release)
        
        # Controls (left side) - scrollable
        controls_container = tk.Frame(self)
        controls_container.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        control_canvas = tk.Canvas(controls_container, borderwidth=0, highlightthickness=0, width=320)
        vsb = tk.Scrollbar(controls_container, orient=tk.VERTICAL, command=control_canvas.yview)
        control_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.control_frame = tk.Frame(control_canvas)
        control_canvas.create_window((0, 0), window=self.control_frame, anchor="nw")
        
        def _on_control_configure(event):
            control_canvas.configure(scrollregion=control_canvas.bbox("all"))
        
        self.control_frame.bind("<Configure>", _on_control_configure)
        control_canvas.bind_all("<MouseWheel>", lambda e: control_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        
        # === Navigation ===
        nav_frame = tk.Frame(self.control_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Button(
            nav_frame, 
            text="← Back to Setup", 
            command=self.controller.show_setup
        ).pack(side=tk.LEFT)
        
        # === Status ===
        tk.Label(
            self.control_frame, 
            textvariable=self.controller.status_var, 
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))
        
        # === Playback Controls ===
        playback_frame = tk.LabelFrame(self.control_frame, text="Playback Controls", padx=10, pady=10)
        playback_frame.pack(fill=tk.X, pady=5)
        
        btn_row1 = tk.Frame(playback_frame)
        btn_row1.pack(fill=tk.X, pady=2)
        tk.Button(btn_row1, text="▶ Run", command=self.controller.run_simulation, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row1, text="⏸ Pause", command=self.controller.pause_animation, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row1, text="▶ Resume", command=self.controller.resume_animation, width=10).pack(side=tk.LEFT, padx=2)
        
        btn_row2 = tk.Frame(playback_frame)
        btn_row2.pack(fill=tk.X, pady=2)
        tk.Button(btn_row2, text="Reset Run", command=self.controller.reset_run, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row2, text="Full Reset", command=self.controller.full_reset, width=10).pack(side=tk.LEFT, padx=2)
        
        # Speed slider
        speed_frame = tk.Frame(playback_frame)
        speed_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(speed_frame, text="Animation speed (ms):").pack(anchor="w")
        tk.Scale(
            speed_frame,
            from_=30,
            to=500,
            orient=tk.HORIZONTAL,
            variable=self.controller.speed_var,
            length=200,
        ).pack(anchor="w")
        
        # === Tinkering Controls ===
        tinker_frame = tk.LabelFrame(self.control_frame, text="Tinkering", padx=10, pady=10)
        tinker_frame.pack(fill=tk.X, pady=5)
        
        # Algorithm quick-switch
        algo_frame = tk.Frame(tinker_frame)
        algo_frame.pack(fill=tk.X, pady=5)
        tk.Label(algo_frame, text="Algorithm:").pack(side=tk.LEFT)
        self.algo_combo = ttk.Combobox(
            algo_frame,
            textvariable=self.controller.algorithm_var,
            values=ALGORITHM_OPTIONS,
            state="readonly",
            width=16,
        )
        self.algo_combo.pack(side=tk.LEFT, padx=5)
        tk.Button(algo_frame, text="Re-run", command=self.controller.rerun_simulation).pack(side=tk.LEFT, padx=5)
        
        # Show weights
        tk.Checkbutton(
            tinker_frame, 
            text="Show weights", 
            variable=self.controller.show_weights_var, 
            command=self._on_show_weights_changed
        ).pack(anchor="w", pady=(5, 0))
        
        # Weight editing controls
        weight_tools = tk.LabelFrame(tinker_frame, text="Weight Editing", padx=10, pady=8)
        weight_tools.pack(fill=tk.X, pady=5)
        tk.Checkbutton(
            weight_tools,
            text="Edit weights (paint mode)",
            variable=self.controller.weight_edit_var,
            command=self.controller.toggle_weight_edit_mode,
        ).pack(anchor="w")
        tk.Label(
            weight_tools,
            text="Cycle weights: " + " → ".join(str(int(w)) for w in WEIGHT_CYCLE_VALUES),
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        tk.Label(
            weight_tools,
            text="Click or drag to paint weights. Walls/start/goal are locked.",
            wraplength=260,
            anchor="w",
            justify="left",
            fg="#334155",
        ).pack(anchor="w", pady=(2, 4))
        tk.Button(
            weight_tools,
            text="Reset Weights",
            command=self.controller.reset_all_weights,
        ).pack(anchor="w")
        
        # === Compare Mode ===
        compare_frame = tk.LabelFrame(self.control_frame, text="Compare Algorithms", padx=10, pady=10)
        compare_frame.pack(fill=tk.X, pady=5)
        
        compare_row = tk.Frame(compare_frame)
        compare_row.pack(fill=tk.X)
        tk.Label(compare_row, text="Compare:").pack(side=tk.LEFT)
        self.compare_algo1 = ttk.Combobox(compare_row, values=ALGORITHM_OPTIONS[1:], state="readonly", width=12)
        self.compare_algo1.pack(side=tk.LEFT, padx=2)
        self.compare_algo1.set("A*")
        tk.Label(compare_row, text="vs").pack(side=tk.LEFT, padx=2)
        self.compare_algo2 = ttk.Combobox(compare_row, values=ALGORITHM_OPTIONS[1:], state="readonly", width=12)
        self.compare_algo2.pack(side=tk.LEFT, padx=2)
        self.compare_algo2.set("BFS")
        
        tk.Button(compare_frame, text="Run Comparison", command=self._run_comparison).pack(pady=(5, 0))
        
        self.compare_result_var = tk.StringVar(value="")
        tk.Label(compare_frame, textvariable=self.compare_result_var, justify="left", wraplength=280).pack(anchor="w", pady=(5, 0))
        
        # === Visualization Info ===
        viz_frame = tk.LabelFrame(self.control_frame, text="Visualization Info", padx=10, pady=10)
        viz_frame.pack(fill=tk.X, pady=5)
        tk.Label(viz_frame, textvariable=self.controller.viz_info_var, justify="left", wraplength=280).pack(anchor="w")
        
        # === Results ===
        results_frame = tk.LabelFrame(self.control_frame, text="Results", padx=10, pady=10)
        results_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(results_frame, text="Optimal Algorithm:", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(results_frame, textvariable=self.controller.best_var, justify="left").pack(anchor="w")
        
        tk.Label(results_frame, text="All Results:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        self.results_box = tk.Text(results_frame, height=12, width=38, state="disabled", wrap="word")
        self.results_box.pack(anchor="w")
        
        self.analytics_button = tk.Button(
            results_frame,
            text="Show Analytics",
            command=self.show_analytics_overlay,
            state=tk.DISABLED,
            bg="#0f172a",
            fg="white",
            activebackground="#1e293b",
            activeforeground="white",
        )
        self.analytics_button.pack(fill=tk.X, pady=(10, 0))
    
    def _on_show_weights_changed(self) -> None:
        """Redraw grid when show weights changes."""
        if self.controller.current_grid:
            self.controller.draw_grid(self.controller.current_grid)
    
    def _run_comparison(self) -> None:
        """Run comparison between two selected algorithms."""
        algo1 = self.compare_algo1.get()
        algo2 = self.compare_algo2.get()
        
        if not algo1 or not algo2:
            messagebox.showwarning("Select Algorithms", "Please select two algorithms to compare.")
            return
        
        if algo1 == algo2:
            messagebox.showwarning("Different Algorithms", "Please select two different algorithms.")
            return
        
        # Find results for both algorithms
        result1 = next((r for r in self.controller.results if r.name == algo1), None)
        result2 = next((r for r in self.controller.results if r.name == algo2), None)
        
        if not result1 or not result2:
            messagebox.showinfo("Run First", "Please run the simulation first to get algorithm results.")
            return
        
        # Build comparison text
        comparison = f"=== {algo1} vs {algo2} ===\n\n"
        comparison += f"{'Metric':<15} {algo1:<15} {algo2:<15} Winner\n"
        comparison += "-" * 55 + "\n"
        
        # Cost
        cost_winner = algo1 if result1.cost < result2.cost else algo2 if result2.cost < result1.cost else "Tie"
        comparison += f"{'Cost':<15} {result1.cost:<15.3f} {result2.cost:<15.3f} {cost_winner}\n"
        
        # Nodes
        nodes_winner = algo1 if result1.explored_nodes < result2.explored_nodes else algo2 if result2.explored_nodes < result1.explored_nodes else "Tie"
        comparison += f"{'Nodes':<15} {result1.explored_nodes:<15} {result2.explored_nodes:<15} {nodes_winner}\n"
        
        # Time
        time_winner = algo1 if result1.duration < result2.duration else algo2 if result2.duration < result1.duration else "Tie"
        comparison += f"{'Time (s)':<15} {result1.duration:<15.4f} {result2.duration:<15.4f} {time_winner}\n"
        
        self.compare_result_var.set(comparison)
    
    def on_show(self) -> None:
        """Called when this screen is shown."""
        if self.controller.current_grid:
            self.controller.draw_grid(self.controller.current_grid)
    
    def write_results_text(self, text: str) -> None:
        """Update the results text box."""
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", tk.END)
        self.results_box.insert(tk.END, text)
        self.results_box.configure(state="disabled")
    
    def update_analytics_button_state(self, enabled: bool) -> None:
        """Enable or disable the Show Analytics button."""
        state = tk.NORMAL if enabled else tk.DISABLED
        if hasattr(self, "analytics_button"):
            self.analytics_button.configure(state=state)
        if not enabled:
            self._close_analytics_window()
    
    def show_analytics_overlay(self) -> None:
        """Display a modal overlay with analytics bar charts."""
        if not self.controller.results:
            messagebox.showinfo("No Results", "Run the algorithms first to view analytics.")
            return
        if self.analytics_window is not None and self.analytics_window.winfo_exists():
            self.analytics_window.deiconify()
            self.analytics_window.lift()
            self.analytics_window.focus_force()
            return
        
        successful = [r for r in self.controller.results if r.success]
        failed = [r for r in self.controller.results if not r.success]
        overlay = tk.Toplevel(self)
        overlay.title("Algorithm Analytics")
        overlay.transient(self.controller.root)
        overlay.grab_set()
        overlay.resizable(False, False)
        self.controller.root.update_idletasks()
        width, height = 780, 780
        root_x = self.controller.root.winfo_rootx()
        root_y = self.controller.root.winfo_rooty()
        root_w = max(self.controller.root.winfo_width(), width)
        root_h = max(self.controller.root.winfo_height(), height)
        x = root_x + (root_w - width) // 2
        y = root_y + (root_h - height) // 2
        overlay.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
        overlay.bind("<Escape>", lambda e: self._close_analytics_window())
        overlay.protocol("WM_DELETE_WINDOW", self._close_analytics_window)
        self.analytics_window = overlay
        
        content = tk.Frame(overlay, padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)
        
        if not successful:
            tk.Label(
                content,
                text="No successful algorithm runs to analyze.",
                font=("Arial", 12, "bold")
            ).pack(pady=20)
            tk.Button(content, text="Close", command=self._close_analytics_window).pack()
            return
        
        names = [r.name for r in successful]
        durations_ms = [r.duration * 1000.0 for r in successful]
        costs = [r.cost for r in successful]
        nodes = [r.explored_nodes for r in successful]
        
        figure = Figure(figsize=(7.2, 8), dpi=100)
        axes = [
            figure.add_subplot(311),
            figure.add_subplot(312),
            figure.add_subplot(313),
        ]
        charts = [
            (axes[0], durations_ms, "Time Taken", "Milliseconds"),
            (axes[1], costs, "Path Cost", "Cost"),
            (axes[2], nodes, "Nodes Explored", "Nodes"),
        ]
        for ax, values, title, ylabel in charts:
            ax.bar(names, values, color="#2563eb")
            ax.set_title(title)
            ax.set_ylabel(ylabel)
            ax.tick_params(axis="x", rotation=25)
            ax.grid(axis="y", linestyle="--", alpha=0.3)
        figure.tight_layout(pad=2.0)
        
        canvas = FigureCanvasTkAgg(figure, master=content)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._analytics_canvas = canvas
        
        if failed:
            fail_names = ", ".join(r.name for r in failed)
            tk.Label(
                content,
                text=f"Excluded failed algorithms: {fail_names}",
                fg="#b91c1c",
                anchor="w",
                justify="left",
            ).pack(anchor="w", pady=(10, 0))
        
        tk.Button(
            content,
            text="Close",
            command=self._close_analytics_window
        ).pack(pady=(12, 0))
    
    def _close_analytics_window(self) -> None:
        """Close the analytics overlay if it is open."""
        if self.analytics_window is not None and self.analytics_window.winfo_exists():
            try:
                self.analytics_window.grab_release()
            except tk.TclError:
                pass
            self.analytics_window.destroy()
        self.analytics_window = None
        self._analytics_canvas = None


class SimulatorGUI:
    """Main controller for the two-screen GUI application."""
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Autonomous Car Grid Simulation")
        root.geometry("1050x750")
        
        # === Shared State Variables ===
        
        # Configuration variables
        self.preset_var = tk.StringVar(value=list_presets()[0])
        self.algorithm_var = tk.StringVar(value=ALGORITHM_OPTIONS[0])
        self.rows_var = tk.StringVar(value="12")
        self.cols_var = tk.StringVar(value="12")
        self.obstacle_var = tk.StringVar(value="0.18")
        self.weight_var = tk.StringVar(value="0.18")
        self.seed_var = tk.StringVar(value="42")
        self.speed_var = tk.IntVar(value=DEFAULT_SPEED_MS)
        self.show_weights_var = tk.BooleanVar(value=False)
        self.weight_edit_var = tk.BooleanVar(value=False)
        
        # Priority order for best algorithm selection (internal keys)
        self.priority_order: List[str] = list(DEFAULT_PRIORITY_ORDER)
        
        # Status and display variables
        self.status_var = tk.StringVar(value="Ready")
        self.viz_info_var = tk.StringVar(value="-")
        self.best_var = tk.StringVar(value="-")
        
        # Grid state
        self.current_grid: Optional[Grid] = None
        self.grid_source: Optional[str] = None  # "preset" or "custom"
        
        # Run state
        self.running = False
        self.paused = False
        self.animation_job: Optional[str] = None
        self.animation_index = 0
        self.path_index = 0
        self.path_prev: Optional[Cell] = None
        self.cumulative_cost = 0.0
        self.path_taken: List[Tuple[int, int]] = []
        self.editing_weight = False
        self.weights_dirty = False
        self.last_painted_cell: Optional[Tuple[int, int]] = None
        self.car_base_image: Optional["Image.Image"] = None
        self.car_direction_images: Dict[str, "Image.Image"] = {}
        self.scaled_car_images: Dict[Tuple[str, int], tk.PhotoImage] = {}
        self.car_sprite_id: Optional[int] = None
        self.car_sprite_is_image = False
        self.car_anim_job: Optional[str] = None
        self.car_path: List[Tuple[int, int]] = []
        self.car_step_index = 0
        self.car_animating = False
        self.car_heading = "right"
        self.selected_cell: Optional[Tuple[int, int]] = None
        
        # Results
        self.results: List[SearchResult] = []
        self.best_result: Optional[SearchResult] = None
        self.visualized_result: Optional[SearchResult] = None
        
        # === Container for screens ===
        self.container = tk.Frame(root)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Create screens
        self.setup_frame = SetupFrame(self.container, self)
        self.visualization_frame = VisualizationFrame(self.container, self)
        self._load_car_sprite()
        
        # Initially show setup
        self.current_screen: Optional[tk.Frame] = None
        self.show_setup()
    
    # === Screen Navigation ===
    
    def show_setup(self) -> None:
        """Show the setup screen."""
        if self.current_screen:
            self.current_screen.pack_forget()
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        self.current_screen = self.setup_frame
        self.setup_frame.update_start_button_state()
        self.status_var.set("Configure your grid and algorithm")
    
    def show_visualization(self) -> None:
        """Show the visualization screen."""
        if self.current_screen:
            self.current_screen.pack_forget()
        self.visualization_frame.pack(fill=tk.BOTH, expand=True)
        self.current_screen = self.visualization_frame
        self.visualization_frame.on_show()
        self.status_var.set("Ready to run")

    def start_simulation(self) -> None:
        """Entry point for the Start Visualization button on the setup screen."""
        if self.current_grid is None:
            messagebox.showinfo("No Grid", "Build or load a grid first.")
            self.status_var.set("Build or load a grid first.")
            return
        if self.current_screen is not self.visualization_frame:
            self.show_visualization()
        self.run_simulation()
    
    # === Grid Building ===
    
    def build_grid(self) -> Grid:
        """Build a custom grid from current settings."""
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            obstacle_ratio = float(self.obstacle_var.get())
            weight_ratio = float(self.weight_var.get())
            seed = int(self.seed_var.get()) if self.seed_var.get() else 42
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter valid numeric values.")
            raise

        # Clamp ratios to safe values
        obstacle_ratio = max(0.0, min(0.6, obstacle_ratio))
        weight_ratio = max(0.0, min(0.6, weight_ratio))
        return Grid.random_grid(
            rows=rows,
            cols=cols,
            obstacle_ratio=obstacle_ratio,
            weighted_ratio=weight_ratio,
            seed=seed,
        )
    
    # === Drawing ===
    
    def draw_grid(self, grid: Grid) -> None:
        """Draw the grid on the visualization canvas."""
        canvas = self.visualization_frame.grid_canvas
        canvas.delete("all")
        self._stop_car_animation()
        matrix = grid.as_matrix()
        cell_size = CANVAS_SIZE / max(grid.rows, grid.cols)
        for r in range(grid.rows):
            for c in range(grid.cols):
                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                cell: Cell = matrix[r][c]
                color = "white"
                if cell.obstacle:
                    color = "#1f2937"
                elif (r, c) == grid.start:
                    color = "#16a34a"
                elif (r, c) == grid.goal:
                    color = "#dc2626"
                elif cell.weight > 1:
                    if cell.weight <= 2:
                        color = "#fed7aa"
                    elif cell.weight <= 3:
                        color = "#fdba74"
                    elif cell.weight <= 5:
                        color = "#fb923c"
                    else:
                        color = "#f97316"
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#e5e7eb")
                # Optionally show weight text
                if self.show_weights_var.get():
                    if cell.weight == 1.0:
                        w_text = "1"
                    elif cell.weight.is_integer():
                        w_text = f"{int(cell.weight)}"
                    else:
                        w_text = f"{cell.weight:.1f}"
                    canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2, 
                        text=w_text, 
                        fill="#000000", 
                        font=("Arial", max(8, int(cell_size // 5)))
                    )
    
    def _highlight_cell(self, pos: Tuple[int, int], color: str) -> None:
        """Highlight a cell during animation."""
        grid = self.current_grid
        if grid is None:
            return
        canvas = self.visualization_frame.grid_canvas
        cell_size = CANVAS_SIZE / max(grid.rows, grid.cols)
        r, c = pos
        x1, y1 = c * cell_size, r * cell_size
        x2, y2 = x1 + cell_size, y1 + cell_size
        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#e5e7eb")
        # If showing weights, redraw weight text on top
        if self.show_weights_var.get():
            cell = grid.cells.get(pos, Cell())
            if cell.weight == 1.0:
                w_text = "1"
            elif cell.weight.is_integer():
                w_text = f"{int(cell.weight)}"
            else:
                w_text = f"{cell.weight:.1f}"
            canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2, 
                text=w_text, 
                fill="#000000", 
                font=("Arial", max(8, int(cell_size // 5)))
            )

    def _load_car_sprite(self) -> None:
        """Load or construct the car sprite image."""
        if self.car_base_image is not None or Image is None:
            return
        if CAR_IMAGE_PATH.exists():
            try:
                self.car_base_image = Image.open(CAR_IMAGE_PATH).convert("RGBA")
                return
            except Exception:
                self.car_base_image = None
        try:
            data = base64.b64decode(CAR_SPRITE_BASE64)
            self.car_base_image = Image.open(io.BytesIO(data)).convert("RGBA")
            return
        except Exception:
            fallback = Image.new("RGBA", (32, 20), (0, 0, 0, 0))
            for x in range(0, 32):
                for y in range(12, 20):
                    fallback.putpixel((x, y), (15, 23, 42, 255))
            for x in range(2, 30):
                for y in range(4, 12):
                    fallback.putpixel((x, y), (15, 118, 110, 255))
            for x in range(8, 24):
                for y in range(4, 10):
                    fallback.putpixel((x, y), (147, 197, 253, 255))
            self.car_base_image = fallback

    def _direction_for_step(self, start: Tuple[int, int], end: Tuple[int, int]) -> str:
        dr = end[0] - start[0]
        dc = end[1] - start[1]
        if abs(dr) > abs(dc):
            return "down" if dr > 0 else "up"
        if dc > 0:
            return "right"
        elif dc < 0:
            return "left"
        return "right"

    def _get_car_sprite_for_cell(self, cell_size: float, direction: str) -> Optional[tk.PhotoImage]:
        """Return a scaled sprite for the specified direction."""
        self._load_car_sprite()
        if Image is None or ImageTk is None or self.car_base_image is None:
            return None
        if direction not in self.car_direction_images:
            angle_map = {
                "right": 0,
                "down": -90,
                "left": 180,
                "up": -270,
            }
            angle = angle_map.get(direction, 0)
            self.car_direction_images[direction] = self.car_base_image.rotate(angle, expand=True)
        base_image = self.car_direction_images[direction]
        key = (direction, max(1, int(round(cell_size))))
        if key in self.scaled_car_images:
            return self.scaled_car_images[key]
        target = max(1, int(cell_size * 0.8))
        width, height = base_image.size
        if width <= target and height <= target:
            photo = ImageTk.PhotoImage(base_image)
        else:
            scale = max(width / target, height / target)
            new_size = (max(1, int(width / scale)), max(1, int(height / scale)))
            resized = base_image.resize(new_size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
        self.scaled_car_images[key] = photo
        return photo

    def _place_car_sprite(self, pos: Tuple[int, int], direction: str) -> None:
        """Place or move the car sprite to the specified cell."""
        if self.current_grid is None:
            return
        canvas = self.visualization_frame.grid_canvas
        cell_size = CANVAS_SIZE / max(self.current_grid.rows, self.current_grid.cols)
        r, c = pos
        cx = c * cell_size + cell_size / 2
        cy = r * cell_size + cell_size / 2
        sprite = self._get_car_sprite_for_cell(cell_size, direction)
        if sprite is not None:
            if self.car_sprite_id is None or not self.car_sprite_is_image:
                if self.car_sprite_id is not None:
                    canvas.delete(self.car_sprite_id)
                self.car_sprite_id = canvas.create_image(cx, cy, image=sprite)
                self.car_sprite_is_image = True
            else:
                canvas.coords(self.car_sprite_id, cx, cy)
                canvas.itemconfig(self.car_sprite_id, image=sprite)
        else:
            if self.car_sprite_id is None or self.car_sprite_is_image:
                if self.car_sprite_id is not None:
                    canvas.delete(self.car_sprite_id)
                self.car_sprite_id = canvas.create_rectangle(
                    cx - cell_size / 3,
                    cy - cell_size / 3,
                    cx + cell_size / 3,
                    cy + cell_size / 6,
                    fill="#0f172a",
                    outline="#334155",
                )
                self.car_sprite_is_image = False
            else:
                canvas.coords(self.car_sprite_id, cx, cy)

    def _start_car_animation(self, path: List[Tuple[int, int]]) -> None:
        """Begin animating the car along the final path."""
        self._stop_car_animation()
        if not path:
            self._complete_run()
            return
        self.car_path = list(path)
        self.car_step_index = 1  # start is already placed
        self.car_animating = True
        if len(path) >= 2:
            self.car_heading = self._direction_for_step(path[0], path[1])
        else:
            self.car_heading = "right"
        self.running = True
        self._place_car_sprite(path[0], self.car_heading)
        if len(path) == 1:
            self._finish_car_animation()
            return
        self._schedule_car_step()

    def _schedule_car_step(self) -> None:
        """Advance the car animation by one cell."""
        if not self.car_animating:
            return
        if self.current_grid is None:
            self._finish_car_animation()
            return
        if self.paused:
            self.car_anim_job = None
            return
        if self.car_step_index >= len(self.car_path):
            self._finish_car_animation()
            return
        prev = self.car_path[self.car_step_index - 1]
        pos = self.car_path[self.car_step_index]
        self.car_heading = self._direction_for_step(prev, pos)
        self._place_car_sprite(pos, self.car_heading)
        self.car_step_index += 1
        if self.car_step_index < len(self.car_path):
            delay = max(60, self.speed_var.get())
            self.car_anim_job = self.root.after(delay, self._schedule_car_step)
        else:
            self._finish_car_animation()

    def _finish_car_animation(self) -> None:
        """Finalize the run after the car reaches the goal."""
        self.car_anim_job = None
        self.car_animating = False
        self.car_path = []
        self.car_step_index = 0
        self._complete_run()

    def _stop_car_animation(self, remove_sprite: bool = True) -> None:
        """Cancel any pending car animation and optionally remove the sprite."""
        if self.car_anim_job:
            self.root.after_cancel(self.car_anim_job)
        self.car_anim_job = None
        self.car_animating = False
        self.car_path = []
        self.car_step_index = 0
        if remove_sprite and self.car_sprite_id and self.visualization_frame:
            self.visualization_frame.grid_canvas.delete(self.car_sprite_id)
            self.car_sprite_id = None
            self.car_sprite_is_image = False

    def _complete_run(self) -> None:
        """Mark the simulation run as completed."""
        self.running = False
        self.paused = False
    # === Simulation Control ===
    
    def run_simulation(self) -> None:
        """Run the simulation (first run or after reset)."""
        if self.running:
            return
        if self.current_grid is None:
            messagebox.showerror("No Grid", "Please go back to setup and configure a grid.")
            return
        
        self.running = True
        self.paused = False
        self.status_var.set("Running algorithms...")
        self.draw_grid(self.current_grid)
        
        thread = threading.Thread(target=self._execute_algorithms, daemon=True)
        thread.start()
    
    def rerun_simulation(self) -> None:
        """Re-run simulation on the same grid (for tinkering)."""
        if self.current_grid is None:
            messagebox.showerror("No Grid", "No grid available to re-run.")
            return
        
        # Cancel any existing animation
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        
        # Reset run state
        self._reset_run_state()
        
        # Redraw grid (preserves edits)
        self.draw_grid(self.current_grid)
        
        # Run algorithms
        self.running = True
        self.paused = False
        self.status_var.set("Re-running algorithms...")
        
        thread = threading.Thread(target=self._execute_algorithms, daemon=True)
        thread.start()
    
    def _execute_algorithms(self) -> None:
        """Execute algorithms in background thread."""
        grid = self.current_grid.clone() if self.current_grid else None
        if grid is None:
            return
        priority_order = self.get_priority_order()
        results, best = evaluate_algorithms(grid, priority_order)
        self.results = results
        self.best_result = best
        self.root.after(0, self._after_algorithms)
    
    def set_priority_order(self, order: List[str]) -> None:
        """Persist a new priority order and refresh dependent UI."""
        normalized: List[str] = [key for key in order if key in PRIORITY_CRITERIA]
        for key in PRIORITY_CRITERIA:
            if key not in normalized:
                normalized.append(key)
        if normalized == self.priority_order:
            return
        self.priority_order = normalized
        self.status_var.set(f"Priority order updated: {self.get_priority_display_string()}")

        if self.results:
            self.best_result = select_best(self.results, tuple(self.priority_order))
            self.render_results()

    def get_priority_order(self) -> Tuple[str, str, str]:
        """Get the current priority order as a tuple of internal keys."""
        if len(self.priority_order) != len(PRIORITY_CRITERIA):
            self.priority_order = list(DEFAULT_PRIORITY_ORDER)
        return tuple(self.priority_order)
    
    def get_priority_display_string(self) -> str:
        """Get a formatted string showing the current priority order."""
        names = [PRIORITY_DISPLAY_NAMES.get(key, key.title()) for key in self.priority_order]
        return " → ".join(names)
    
    def has_custom_weights(self) -> bool:
        """Return True if the active grid has edited weights."""
        if not self.current_grid:
            return False
        return grid_has_custom_weights(self.current_grid)
    
    def _after_algorithms(self) -> None:
        """Handle algorithm completion."""
        if self.best_result is None or self.current_grid is None:
            self.status_var.set("No solution found.")
            self.running = False
            return
        
        visualized = self._resolve_visualized_result()
        selected_name = self.algorithm_var.get()
        if visualized is None or not visualized.success:
            if selected_name != "Auto (best)":
                messagebox.showwarning(
                    "Selection unavailable",
                    f"Algorithm '{selected_name}' did not produce a valid path. "
                    "Falling back to the optimal result."
                )
            visualized = self.best_result
        if visualized is None:
            self.status_var.set("No solution found.")
            self.running = False
            return

        self.visualized_result = visualized
        self.status_var.set(
            f"Visualizing: {visualized.name} (Optimal: {self.best_result.name if self.best_result else 'N/A'})"
        )
        self.render_results()
        self.animation_index = 0
        self.animate_exploration()
    
    def _resolve_visualized_result(self) -> Optional[SearchResult]:
        """Get the result to visualize based on algorithm selection."""
        selected = self.algorithm_var.get()
        if selected == "Auto (best)":
            return self.best_result
        return next((r for r in self.results if r.name == selected), None)
    
    # === Animation ===
    
    def animate_exploration(self) -> None:
        """Animate the exploration phase."""
        if not self.visualized_result or not self.current_grid:
            return
        if self.paused:
            return
        visited = self.visualized_result.visited_order
        if self.animation_index < len(visited):
            pos = visited[self.animation_index]
            self._highlight_cell(pos, "#3b82f6")
            self.animation_index += 1
            delay = max(10, self.speed_var.get())
            self.animation_job = self.root.after(delay, self.animate_exploration)
        else:
            # Start step-by-step path animation
            self.path_index = 0
            self.cumulative_cost = 0.0
            self.path_prev = None
            self.path_taken = []
            self.animate_path()
    
    def animate_path(self) -> None:
        """Animate the path phase."""
        if not self.visualized_result or not self.current_grid:
            return
        if self.paused:
            return
        path = self.visualized_result.path
        if self.path_index < len(path):
            pos = path[self.path_index]
            self.path_taken.append(pos)
            self._highlight_cell(pos, "#fde047")
            if self.path_prev is not None:
                step_cost = self.current_grid.cost(self.path_prev, pos)
                self.cumulative_cost += step_cost
            self.path_prev = pos
            
            # Build detailed path display
            path_coords = " → ".join([f"({r},{c})" for r, c in self.path_taken])
            path_progress = f"Step {self.path_index + 1}/{len(path)}: {pos}\nCost so far: {self.cumulative_cost:.3f}\n\nPath taken:\n{path_coords}"
            
            info = (
                f"Algorithm: {self.visualized_result.name}\n"
                f"Path Progress:\n"
                f"{path_progress}"
            )
            self.viz_info_var.set(info)
            self.status_var.set(f"Path: {self.path_index + 1}/{len(path)} | Current cost: {self.cumulative_cost:.3f}")
            self.path_index += 1
            delay = max(50, self.speed_var.get())
            self.animation_job = self.root.after(delay, self.animate_path)
        else:
            # Final cost compute
            total_cost = path_cost(self.current_grid, path) if path else 0.0
            path_coords = " → ".join([f"({r},{c})" for r, c in self.path_taken])
            final_info = (
                f"Algorithm: {self.visualized_result.name}\n"
                f"Path Complete!\n"
                f"Total steps: {len(path)}\n"
                f"Total cost: {total_cost:.3f}\n\n"
                f"Final path:\n{path_coords}"
            )
            self.viz_info_var.set(final_info)
            self.status_var.set(f"Finished. Total cost: {total_cost:.3f}")
            if path:
                self._start_car_animation(path)
            else:
                self._complete_run()
    
    # === Controls ===
    
    def pause_animation(self) -> None:
        """Pause the current animation."""
        if not self.running:
            return
        if self.paused:
            return
        self.paused = True
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        if self.car_anim_job:
            self.root.after_cancel(self.car_anim_job)
            self.car_anim_job = None
        self.status_var.set("Paused")
    
    def resume_animation(self) -> None:
        """Resume a paused animation."""
        if not self.running:
            return
        if not self.paused:
            return
        self.paused = False
        self.status_var.set("Resumed")
        # Resume at the correct phase
        if self.visualized_result:
            path = self.visualized_result.path or []
            if self.animation_index < len(self.visualized_result.visited_order):
                self.animate_exploration()
            elif self.path_index < len(path):
                self.animate_path()
            elif self.car_animating and self.car_path:
                self._schedule_car_step()
    
    def reset_run(self) -> None:
        """Reset the current run but keep the grid."""
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
        
        self._reset_run_state()
        
        # Redraw grid
        if self.current_grid:
            self.draw_grid(self.current_grid)
        
        self.status_var.set("Run reset. Ready to re-run.")
    
    def full_reset(self) -> None:
        """Full reset - go back to setup."""
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
        
        self._reset_run_state()
        self.current_grid = None
        self.grid_source = None
        self.visualization_frame.grid_canvas.delete("all")
        self.visualization_frame.write_results_text("")
        self.visualization_frame.compare_result_var.set("")
        
        self.status_var.set("Ready")
        self.show_setup()
    
    def _reset_run_state(self) -> None:
        """Reset run-related state variables."""
        self._stop_car_animation()
        self.running = False
        self.paused = False
        self.animation_job = None
        self.animation_index = 0
        self.path_index = 0
        self.path_prev = None
        self.cumulative_cost = 0.0
        self.path_taken = []
        self.best_result = None
        self.visualized_result = None
        self.results = []
        self.best_var.set("-")
        self.viz_info_var.set("-")
        self.visualization_frame.write_results_text("")
        self.visualization_frame.update_analytics_button_state(False)
        self.editing_weight = False
        self.weights_dirty = False
        self.last_painted_cell = None
        if hasattr(self, "weight_edit_var"):
            self.weight_edit_var.set(False)
    
    # === Results Rendering ===
    
    def render_results(self) -> None:
        """Render algorithm results to the results panel."""
        if self.visualized_result:
            viz = self.visualized_result
            
            # Show complete path with all nodes
            path_detail = ""
            if viz.path:
                path_coords = " → ".join([f"({r},{c})" for r, c in viz.path])
                path_detail = f"Complete Path:\n{path_coords}\n"
            
            # Show all explored nodes
            explored_detail = ""
            if viz.visited_order:
                explored_coords = " → ".join([f"({r},{c})" for r, c in viz.visited_order])
                explored_detail = f"\nExplored Nodes ({len(viz.visited_order)}):\n{explored_coords}\n"
            
            info = (
                f"Algorithm: {viz.name}\n"
                f"Cost: {viz.cost:.3f} | Nodes explored: {viz.explored_nodes} | Time: {viz.duration:.4f}s\n"
                f"Path length: {len(viz.path) if viz.path else 0}\n"
                f"{path_detail}"
                f"{explored_detail}"
            )
            self.viz_info_var.set(info)
        else:
            self.viz_info_var.set("-")

        if self.best_result:
            best = self.best_result
            priority_display = self.get_priority_display_string()
            best_summary = (
                f"{best.name}\n"
                f"Cost: {best.cost}\n"
                f"Nodes: {best.explored_nodes}\n"
                f"Time: {best.duration:.4f}s\n"
                f"\nBest by: {priority_display}"
            )
            self.best_var.set(best_summary)
        else:
            self.best_var.set("-")

        lines: List[str] = []
        for res in sorted(self.results, key=lambda r: r.cost):
            status = "OK" if res.success else "Fail"
            lines.append(
                f"{res.name}: cost={res.cost:.3f}, nodes={res.explored_nodes}, "
                f"time={res.duration:.4f}s, {status}"
            )
        self.visualization_frame.write_results_text("\n".join(lines))
        self.visualization_frame.update_analytics_button_state(bool(self.results))
    
    # === Weight Editing ===
    
    def toggle_weight_edit_mode(self) -> None:
        """Toggle weight edit mode from the UI."""
        self.set_weight_edit_mode(bool(self.weight_edit_var.get()))
    
    def set_weight_edit_mode(self, enabled: bool) -> None:
        """Enable or disable weight editing mode."""
        self.editing_weight = enabled
        self.last_painted_cell = None
        if enabled:
            self.status_var.set("Weight edit mode ON — click or drag to cycle weights.")
        else:
            self.status_var.set("Weight edit mode OFF.")
    
    def reset_all_weights(self) -> None:
        """Reset all editable cells to weight 1."""
        if self.current_grid is None:
            messagebox.showinfo("No grid", "Build or load a grid first.")
            return
        changed = False
        for pos, cell in list(self.current_grid.cells.items()):
            if cell.obstacle:
                continue
            if math.isclose(cell.weight, 1.0):
                self.current_grid.cells.pop(pos, None)
                continue
            if pos in (self.current_grid.start, self.current_grid.goal):
                continue
            self.current_grid.cells.pop(pos, None)
            changed = True
        if changed:
            self.weights_dirty = True
            self.visualization_frame.update_analytics_button_state(False)
            self.draw_grid(self.current_grid)
            self.status_var.set("Weights reset. Re-run to apply changes.")
            self.setup_frame._update_summary()
        else:
            self.status_var.set("Weights are already at default.")
        self.set_weight_edit_mode(False)
    
    def cycle_cell_weight(self, pos: Tuple[int, int]) -> float:
        """Cycle a cell through the configured weight values."""
        if self.current_grid is None:
            return 1.0
        current = self.current_grid.get_weight(pos)
        new_value = next_weight_value(current, WEIGHT_CYCLE_VALUES)
        self.set_cell_weight(pos, new_value)
        return new_value
    
    def set_cell_weight(self, pos: Tuple[int, int], weight: float) -> None:
        """Set a cell's weight in the grid model."""
        if self.current_grid is None:
            return
        cell = self.current_grid.cells.get(pos)
        if cell and cell.obstacle:
            return
        if math.isclose(weight, 1.0):
            self.current_grid.cells.pop(pos, None)
        else:
            self.current_grid.cells[pos] = Cell(weight=weight, obstacle=False)
    
    def _apply_weight_edit(self, pos: Tuple[int, int]) -> None:
        """Apply a weight cycle edit to the specified position."""
        if self.current_grid is None:
            return
        if not self.current_grid.in_bounds(pos):
            return
        if pos in (self.current_grid.start, self.current_grid.goal):
            self.status_var.set("Start and goal cells are locked.")
            return
        cell = self.current_grid.cells.get(pos)
        if cell and cell.obstacle:
            self.status_var.set("Cannot edit walls.")
            return
        if self.last_painted_cell == pos:
            return
        self.last_painted_cell = pos
        new_value = self.cycle_cell_weight(pos)
        self._redraw_cell(pos)
        self.weights_dirty = True
        self.visualization_frame.update_analytics_button_state(False)
        self.status_var.set(f"Set weight at {pos} to {new_value}. Re-run to apply.")
        self.viz_info_var.set("Weights changed. Click Re-run to recompute results.")
        self.setup_frame._update_summary()
    
    def _redraw_cell(self, pos: Tuple[int, int]) -> None:
        """Redraw a single cell to reflect its current state."""
        if self.current_grid is None:
            return
        grid = self.current_grid
        canvas = self.visualization_frame.grid_canvas
        cell_size = CANVAS_SIZE / max(grid.rows, grid.cols)
        r, c = pos
        x1, y1 = c * cell_size, r * cell_size
        x2, y2 = x1 + cell_size, y1 + cell_size
        cell = grid.cells.get(pos, Cell())
        color = "white"
        if cell.obstacle:
            color = "#1f2937"
        elif pos == grid.start:
            color = "#16a34a"
        elif pos == grid.goal:
            color = "#dc2626"
        elif cell.weight > 1:
            if cell.weight <= 2:
                color = "#fed7aa"
            elif cell.weight <= 3:
                color = "#fdba74"
            elif cell.weight <= 5:
                color = "#fb923c"
            else:
                color = "#f97316"
        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#e5e7eb")
        if self.show_weights_var.get():
            w_text = f"{cell.weight:.0f}" if cell.weight.is_integer() else f"{cell.weight:.1f}"
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=w_text,
                fill="#111827",
                font=("Arial", max(8, int(cell_size // 5))),
            )
    
    def on_canvas_click(self, event) -> None:
        """Handle canvas click for weight editing or selection."""
        if self.current_grid is None:
            return
        grid = self.current_grid
        cell_size = CANVAS_SIZE / max(grid.rows, grid.cols)
        c = int(event.x // cell_size)
        r = int(event.y // cell_size)
        pos = (r, c)
        if not grid.in_bounds(pos):
            return

        if self.editing_weight:
            self._apply_weight_edit(pos)
        else:
            # Select the clicked cell
            self.selected_cell = pos
    
    def on_canvas_drag(self, event) -> None:
        """Handle click-drag painting while in weight edit mode."""
        if not self.editing_weight or self.current_grid is None:
            return
        grid = self.current_grid
        cell_size = CANVAS_SIZE / max(grid.rows, grid.cols)
        c = int(event.x // cell_size)
        r = int(event.y // cell_size)
        pos = (r, c)
        if not grid.in_bounds(pos):
            return
        self._apply_weight_edit(pos)
    
    def on_canvas_release(self, _event) -> None:
        """Reset drag tracking when mouse button is released."""
        self.last_painted_cell = None


def run() -> None:
    root = tk.Tk()
    SimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run()
