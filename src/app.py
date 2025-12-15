from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from src.grid import Grid, Cell
from src.evaluator import evaluate_algorithms
from src.presets import get_preset, list_presets
from src.algorithms import SearchResult


CANVAS_SIZE = 620
DEFAULT_SPEED_MS = 120
ALGORITHM_OPTIONS = [
    "Auto (best)",
    "BFS",
    "DFS",
    "Uniform Cost",
    "Greedy Best-First",
    "A*",
    "IDA*",
    "Bidirectional",
]


class SimulatorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Autonomous Car Grid Simulation")
        root.geometry("1000x720")

        self.grid_canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
        self.grid_canvas.pack(side=tk.RIGHT, padx=10, pady=10)

        self.control_frame = tk.Frame(root)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.control_frame, textvariable=self.status_var, font=("Arial", 12, "bold")).pack(pady=(0, 6))

        # Preset selection
        tk.Label(self.control_frame, text="Preset grid").pack(anchor="w")
        self.preset_var = tk.StringVar(value=list_presets()[0])
        self.preset_combo = ttk.Combobox(
            self.control_frame, textvariable=self.preset_var, values=list_presets(), state="readonly", width=20
        )
        self.preset_combo.pack(anchor="w", pady=4)

        tk.Label(self.control_frame, text="Algorithm").pack(anchor="w", pady=(8, 0))
        self.algorithm_var = tk.StringVar(value=ALGORITHM_OPTIONS[0])
        self.algorithm_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.algorithm_var,
            values=ALGORITHM_OPTIONS,
            state="readonly",
            width=20,
        )
        self.algorithm_combo.pack(anchor="w", pady=4)

        # Custom controls
        tk.Label(self.control_frame, text="Custom grid (rows, cols)").pack(anchor="w", pady=(10, 0))
        custom_frame = tk.Frame(self.control_frame)
        custom_frame.pack(anchor="w")
        self.rows_var = tk.StringVar(value="12")
        self.cols_var = tk.StringVar(value="12")
        tk.Entry(custom_frame, textvariable=self.rows_var, width=5).pack(side=tk.LEFT, padx=2)
        tk.Entry(custom_frame, textvariable=self.cols_var, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(self.control_frame, text="Obstacle ratio (0-0.5)").pack(anchor="w", pady=(8, 0))
        self.obstacle_var = tk.StringVar(value="0.18")
        tk.Entry(self.control_frame, textvariable=self.obstacle_var, width=8).pack(anchor="w")

        tk.Label(self.control_frame, text="Weighted ratio (0-0.5)").pack(anchor="w", pady=(8, 0))
        self.weight_var = tk.StringVar(value="0.18")
        tk.Entry(self.control_frame, textvariable=self.weight_var, width=8).pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(self.control_frame)
        btn_frame.pack(anchor="w", pady=12)
        tk.Button(btn_frame, text="Start", command=self.start_simulation, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Pause", command=self.pause_animation, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Resume", command=self.resume_animation, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Reset", command=self.reset, width=8).pack(side=tk.LEFT, padx=2)

        tk.Label(self.control_frame, text="Animation speed (ms)").pack(anchor="w", pady=(6, 0))
        self.speed_var = tk.IntVar(value=DEFAULT_SPEED_MS)
        tk.Scale(
            self.control_frame,
            from_=30,
            to=500,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            length=180,
        ).pack(anchor="w")

        # Info panel
        tk.Label(self.control_frame, text="Visualized algorithm", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.visualized_var = tk.StringVar(value="-")
        tk.Label(self.control_frame, textvariable=self.visualized_var, justify="left").pack(anchor="w")

        tk.Label(self.control_frame, text="Optimal algorithm", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.best_var = tk.StringVar(value="-")
        tk.Label(self.control_frame, textvariable=self.best_var, justify="left").pack(anchor="w")

        tk.Label(self.control_frame, text="All results", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.results_box = tk.Text(self.control_frame, height=18, width=38, state="disabled", wrap="word")
        self.results_box.pack(anchor="w")

        self.current_grid: Optional[Grid] = None
        self.best_result: Optional[SearchResult] = None
        self.visualized_result: Optional[SearchResult] = None
        self.results: List[SearchResult] = []
        self.running = False
        self.paused = False
        self.animation_job: Optional[str] = None
        self.animation_index = 0

    # Grid helpers
    def build_grid(self) -> Grid:
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            obstacle_ratio = float(self.obstacle_var.get())
            weight_ratio = float(self.weight_var.get())
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
            seed=42,  # deterministic for reproducibility
        )

    def draw_grid(self, grid: Grid) -> None:
        self.grid_canvas.delete("all")
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
                    color = "#fb923c"
                self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#e5e7eb")

    # Simulation lifecycle
    def start_simulation(self) -> None:
        if self.running:
            return
        self.running = True
        self.paused = False
        self.status_var.set("Running algorithms...")
        preset_name = self.preset_var.get()
        use_preset = messagebox.askyesno("Use preset?", f"Run preset '{preset_name}'? Choose No for custom grid.")
        try:
            grid = get_preset(preset_name) if use_preset else self.build_grid()
        except Exception:
            self.running = False
            return

        self.current_grid = grid
        self.draw_grid(grid)
        thread = threading.Thread(target=self._execute_algorithms, daemon=True)
        thread.start()

    def _execute_algorithms(self) -> None:
        grid = self.current_grid.clone() if self.current_grid else None
        if grid is None:
            return
        results, best = evaluate_algorithms(grid)
        self.results = results
        self.best_result = best
        self.root.after(0, self._after_algorithms)

    def _after_algorithms(self) -> None:
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
                    (
                        f"Algorithm '{selected_name}' did not produce a valid path. "
                        "Falling back to the optimal result."
                    ),
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

    # Animation
    def animate_exploration(self) -> None:
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
            # Draw final path
            for pos in self.visualized_result.path:
                self._highlight_cell(pos, "#fde047")
            self.running = False
            self.status_var.set(
                f"Finished. Visualized: {self.visualized_result.name} "
                f"(Optimal: {self.best_result.name if self.best_result else 'N/A'})"
            )

    def _highlight_cell(self, pos, color: str) -> None:
        grid = self.current_grid
        if grid is None:
            return
        cell_size = CANVAS_SIZE / max(grid.rows, grid.cols)
        r, c = pos
        x1, y1 = c * cell_size, r * cell_size
        x2, y2 = x1 + cell_size, y1 + cell_size
        self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#e5e7eb")

    # Controls
    def pause_animation(self) -> None:
        self.paused = True
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        self.status_var.set("Paused")

    def resume_animation(self) -> None:
        if not self.running:
            return
        if not self.paused:
            return
        self.paused = False
        self.status_var.set("Resumed")
        self.animate_exploration()

    def reset(self) -> None:
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
        self.running = False
        self.paused = False
        self.animation_job = None
        self.animation_index = 0
        self.best_result = None
        self.visualized_result = None
        self.results = []
        self.grid_canvas.delete("all")
        self.status_var.set("Ready")
        self.best_var.set("-")
        self.visualized_var.set("-")
        self._write_results_text("")

    # Rendering info
    def render_results(self) -> None:
        if self.visualized_result:
            viz = self.visualized_result
            viz_summary = (
                f"{viz.name}\n"
                f"Cost: {viz.cost}\n"
                f"Nodes: {viz.explored_nodes}\n"
                f"Time: {viz.duration:.4f}s\n"
            )
            self.visualized_var.set(viz_summary)
        else:
            self.visualized_var.set("-")

        if self.best_result:
            best = self.best_result
            best_summary = (
                f"{best.name}\n"
                f"Cost: {best.cost}\n"
                f"Nodes: {best.explored_nodes}\n"
                f"Time: {best.duration:.4f}s\n"
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
        self._write_results_text("\n".join(lines))

    def _write_results_text(self, text: str) -> None:
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", tk.END)
        self.results_box.insert(tk.END, text)
        self.results_box.configure(state="disabled")

    def _resolve_visualized_result(self) -> Optional[SearchResult]:
        selected = self.algorithm_var.get()
        if selected == "Auto (best)":
            return self.best_result
        return next((r for r in self.results if r.name == selected), None)


def run() -> None:
    root = tk.Tk()
    SimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run()
