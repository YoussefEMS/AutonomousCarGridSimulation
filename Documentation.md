---

# Introduction to Artificial Intelligence

**C-AI311 — Fall 2025**

## Autonomous Car Grid Simulation

---

## Team Members

| Student Name     | Student ID |
| ---------------- | ---------- |
| Omar Mohamed     | 23-101149  |
| Maroska Osama    | 23-101209  |
| Youssef Ihab     | 23-101138  |
| Hamdy El Saeed   | 23-101232  |
| Jana Abdelmoniem | 23-101148  |
| Youssef Ashoush  | 23-101049  |

---

## Table of Contents

* Abstract
* Introduction
* Problem Definition
* Methodology
* Full Project Pipeline
* All Project Details
* Algorithms to Be Used
* Team Working Plan

---

## Abstract

This project introduces a GUI-based **Autonomous Car Grid Simulation** designed to automatically evaluate and identify the optimal path-planning strategy for navigating a grid-based environment. The system integrates multiple search algorithms—including uninformed, informed, and cost-based approaches—and executes them in parallel to determine the most efficient solution.

Algorithm performance is assessed using:

* Total path cost
* Execution time
* Number of explored nodes

The simulation selects and visualizes the algorithm producing the optimal result. The GUI provides step-by-step animations, highlights the final optimal path, and displays detailed performance statistics. The project serves as both an analytical and educational tool for understanding autonomous navigation and search algorithm trade-offs.

---

## Introduction

Autonomous navigation is a core capability of intelligent systems, requiring efficient route planning and obstacle avoidance. Path-planning algorithms enable this behavior, and comparing their performance is essential to determine optimal solutions.

This project presents a GUI-based simulation that runs multiple search algorithms—BFS, DFS, UCS, Greedy Best-First Search, and A*—on the same grid. It measures performance, identifies the optimal algorithm, visualizes search behavior, and displays metrics such as path cost, execution time, and explored nodes.

---

## Problem Definition

Autonomous systems must navigate grid environments efficiently while avoiding obstacles and minimizing travel cost. Different search algorithms perform differently depending on grid size, layout, and terrain, making manual selection inefficient.

### System Requirements

The system must:

1. Run seven search algorithms:

   * Breadth-First Search (BFS)
   * Depth-First Search (DFS)
   * Uniform Cost Search (UCS)
   * Greedy Best-First Search
   * A* Search
   * Iterative Deepening A* (IDA*)
   * Bidirectional Search (BDS)

2. Compute performance metrics:

   * Total path cost
   * Execution time
   * Number of explored nodes

3. Identify the optimal algorithm automatically.

4. Visualize search behavior, final path, and metrics via GUI.

---

## Methodology

### 1. Grid Environment Modeling

* **Preset grids**: 5×5, 10×10, 15×15, maze, weighted terrain
* **Custom grids**: user-defined size, obstacles, start/goal, terrain weights

Each cell represents:

* Free space
* Obstacle
* Weighted terrain

### 2. Algorithm Execution Pipeline

Algorithms are executed independently on the same grid.

* **BFS**: Shortest path in unweighted grids
* **DFS**: Deep exploration and backtracking
* **UCS**: Optimal cost path in weighted grids
* **Greedy Best-First**: Heuristic-driven, fast but not always optimal
* **A***: Cost + heuristic balance
* **IDA***: Memory-efficient A* variant
* **BDS**: Simultaneous search from start and goal

**Execution tracking includes**:

* Nodes explored
* Path generated
* Total cost
* Execution time
* Success/failure

### 3. Performance Evaluation & Selection

**Selection criteria**:

1. Lowest path cost
2. Fewest explored nodes (tie-breaker)
3. Shortest execution time

### 4. GUI-Based Visualization

* Grid display
* Step-by-step algorithm animation
* Highlighted final path
* Performance panel
* Controls: start, pause, resume, reset, speed

### 5. Validation and Testing

* Preset and custom grids
* Performance consistency
* GUI robustness

### 6. Final Output

* Optimal path
* Selected algorithm
* Visualized search process
* Detailed performance metrics

---

## Full Project Pipeline

### Week 1 — Planning & Documentation

* Define scope, methodology, pipeline, and roles
* Confirm algorithms and grid modes

**Deliverable**: Phase 1 report
**Team**: All members

### Week 2 — Grid & Algorithms (Part 1)

* Grid module
* BFS, DFS, UCS, Greedy

**Team**:

* Omar & Maroska: Grid
* Hamdy: BFS
* Jana: DFS
* Youssef & Youssef: UCS & Greedy

### Week 3 — Algorithms (Part 2) & Testing

* A*, IDA*, BDS
* Metrics collection

**Team**:

* Maroska & Jana: A*, IDA*
* Omar & Youssef: BDS & GUI
* All: Testing

### Week 4 — GUI & Final Validation

* GUI integration
* Final testing
* Report & presentation

---

## All Project Details — Autonomous Car Grid Simulation

### Project Objectives

* Simulate autonomous navigation
* Compare 7 algorithms
* Automatically select optimal solution
* Provide interactive visualization

### Functional Requirements

* Configurable grid
* Preset and custom modes
* Algorithm comparison
* GUI visualization

### Non-Functional Requirements

* Accuracy
* Reliability
* Modularity
* User-friendly interface

---

## Algorithms to Be Used

| Algorithm | Why Chosen                | Contribution             |
| --------- | ------------------------- | ------------------------ |
| BFS       | Simplicity, shortest path | Baseline correctness     |
| DFS       | Deep exploration          | Backtracking analysis    |
| UCS       | Weighted optimality       | Minimum-cost path        |
| Greedy    | Speed                     | Heuristic trade-offs     |
| A*        | Optimal + efficient       | Best overall performance |
| IDA*      | Memory efficiency         | Large grids              |
| BDS       | Reduced search space      | Faster convergence       |

---

## Input & Output

### Input

* Grid layout
* Start and goal
* Terrain costs

### Output

* Optimal path
* Selected algorithm
* Performance metrics
* Search animation

---

## GUI Features

* Grid visualization
* Step-by-step animation
* Performance panel
* Interactive controls

---

## Team Roles and Responsibilities

| Member  | Responsibility   | Algorithms  |
| ------- | ---------------- | ----------- |
| Omar    | Grid environment | —           |
| Hamdy   | BFS              | BFS         |
| Jana    | DFS              | DFS         |
| Youssef | UCS & Greedy     | UCS, Greedy |
| Maroska | A* & IDA*        | A*, IDA*    |
| Youssef | BDS & GUI        | BDS         |

All members participate in testing, documentation, and validation.

---

## Project Timeline (1 Month)

| Week | Tasks                         |
| ---- | ----------------------------- |
| 1    | Planning & documentation      |
| 2    | Grid + BFS, DFS, UCS, Greedy  |
| 3    | A*, IDA*, BDS + metrics       |
| 4    | GUI, validation, final report |

---

## Validation and Testing

* Preset and custom grids
* Consistent optimal selection
* Accurate GUI visualization
* Reliability and performance verification

---
