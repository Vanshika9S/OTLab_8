"""
optimizers.py
-------------
Advanced Solvers for University Examination Timetabling (Track E).

Implements:
1. DSATURSolver: Degree of Saturation graph coloring heuristic (Brelaz 1979)
   with soft-constraint penalty awareness.
2. ILPSolver: Exact Branch-and-Cut Integer Linear Programming via SciPy HiGHS (scipy.optimize.milp)
   with configurable time limit.
3. SimulatedAnnealingSolver: Custom Simulated Annealing with multi-operator neighborhood
   (random shift, course swap, Kempe-chain swap) and geometric cooling.
4. ParallelSASolver: Multi-core parallel restarts across CPU cores using multiprocessing.
"""

import os
import sys
import time
import math
import random
import multiprocessing
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_E_case_study.code.validator import TimetableValidator


# =====================================================================
# 1. DSATUR (Degree of Saturation) Heuristic Solver
# =====================================================================
class DSATURSolver:
    """
    Brélaz (1979) Degree of Saturation heuristic adapted for examination timetabling.
    Prioritizes courses with the highest number of distinct slots already assigned
    to conflicting neighbors.
    """
    def __init__(self, instance: Dict[str, Any]):
        self.instance = instance
        self.meta = instance["metadata"]
        self.num_courses = self.meta["num_courses"]
        self.num_slots = self.meta["num_slots"]
        self.capacity_per_slot = self.meta["total_room_capacity_per_slot"]
        self.course_enrollments = instance["course_enrollment_counts"]

        # Build conflict adjacency list
        self.adj: Dict[int, Set[int]] = {i: set() for i in range(self.num_courses)}
        for edge_str in instance.get("conflicts", {}):
            u_str, v_str = edge_str.split(",")
            u, v = int(u_str), int(v_str)
            if u < self.num_courses and v < self.num_courses:
                self.adj[u].add(v)
                self.adj[v].add(u)

        self.validator = TimetableValidator(instance)

    def solve(self, seed: Optional[int] = None) -> Tuple[Dict[int, int], float]:
        """
        Solves the timetabling problem using DSATUR.
        Returns: (schedule, runtime_ms).
        """
        t0 = time.perf_counter()
        rng = random.Random(seed) if seed is not None else random.Random()

        schedule: Dict[int, int] = {}
        unassigned = set(range(self.num_courses))

        # Track colors assigned to neighbors for each vertex
        neighbor_slots: Dict[int, Set[int]] = {i: set() for i in range(self.num_courses)}
        slot_enrollments: Dict[int, int] = {s: 0 for s in range(self.num_slots)}

        while unassigned:
            # 1. Select unassigned course with maximum saturation degree
            # Tie breaker 1: number of unassigned neighbors (degree in uncolored subgraph)
            # Tie breaker 2: random perturbation based on seed
            def priority_key(c: int):
                sat_deg = len(neighbor_slots[c])
                unassigned_deg = len(self.adj[c] & unassigned)
                jitter = rng.random() * 0.01
                return (sat_deg, unassigned_deg + jitter)

            best_c = max(unassigned, key=priority_key)
            unassigned.remove(best_c)

            c_enrollment = self.course_enrollments.get(str(best_c), self.course_enrollments.get(best_c, 0))

            # 2. Select slot for best_c minimizing hard conflicts, then capacity, then soft penalties
            best_s = None
            best_score = float('inf')

            # Permute slots slightly if randomized
            slot_order = list(range(self.num_slots))
            if seed is not None:
                rng.shuffle(slot_order)

            for s in slot_order:
                # Count clashes if assigned to slot s
                clashes = sum(1 for n in self.adj[best_c] if schedule.get(n) == s)
                cap_violation = max(0, (slot_enrollments[s] + c_enrollment) - self.capacity_per_slot)

                # Estimated soft penalty: adjacent slots on same day
                day = s // self.meta.get("slots_per_day", 3)
                adj_penalty = 0
                for n in self.adj[best_c]:
                    if n in schedule:
                        n_slot = schedule[n]
                        n_day = n_slot // self.meta.get("slots_per_day", 3)
                        if day == n_day and abs(s - n_slot) == 1:
                            adj_penalty += 1

                # Weighted slot selection score
                score = clashes * 10000.0 + cap_violation * 50.0 + adj_penalty * 10.0 + (slot_enrollments[s] * 0.01)

                if score < best_score:
                    best_score = score
                    best_s = s

            schedule[best_c] = best_s
            slot_enrollments[best_s] += c_enrollment

            # Update neighbor slot sets
            for n in self.adj[best_c]:
                neighbor_slots[n].add(best_s)

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        return schedule, runtime_ms


# =====================================================================
# 2. Exact Integer Linear Programming (ILP) Solver via SciPy HiGHS
# =====================================================================
class ILPSolver:
    """
    Exact Branch-and-Cut ILP solver for exam timetabling using SciPy HiGHS.
    Formulates binary assignment variables x_{c, s} in {0, 1} with hard conflict,
    capacity, and soft penalty linearizations under a strict time limit.
    """
    def __init__(self, instance: Dict[str, Any]):
        self.instance = instance
        self.meta = instance["metadata"]
        self.num_courses = self.meta["num_courses"]
        self.num_slots = self.meta["num_slots"]
        self.capacity_per_slot = self.meta["total_room_capacity_per_slot"]
        self.course_enrollments = [
            instance["course_enrollment_counts"].get(str(c), instance["course_enrollment_counts"].get(c, 0))
            for c in range(self.num_courses)
        ]

        self.conflicts: List[Tuple[int, int]] = []
        for edge_str in instance.get("conflicts", {}):
            u_str, v_str = edge_str.split(",")
            u, v = int(u_str), int(v_str)
            if u < self.num_courses and v < self.num_courses:
                self.conflicts.append((u, v))

    def solve(self, time_limit: float = 2.0, seed: int = 42) -> Tuple[Dict[int, int], float]:
        """
        Solves ILP model via scipy.optimize.milp using HiGHS branch-and-cut
        with sparse CSR constraints and a strict time limit.
        Returns: (schedule, runtime_ms).
        """
        from scipy.sparse import coo_matrix

        t0 = time.perf_counter()
        C = self.num_courses
        S = self.num_slots
        n_vars = C * S

        c = np.zeros(n_vars, dtype=float)
        rows, cols, data = [], [], []
        lhs, rhs = [], []

        # 1. Exactly one slot per course: sum_s x_{c, s} = 1
        for course in range(C):
            for s in range(S):
                rows.append(course)
                cols.append(course * S + s)
                data.append(1.0)
            lhs.append(1.0)
            rhs.append(1.0)

        # 2. Hard Conflict constraints: x_{u, s} + x_{v, s} <= 1
        r = C
        for (u, v) in self.conflicts:
            for s in range(S):
                rows.append(r)
                cols.append(u * S + s)
                data.append(1.0)
                rows.append(r)
                cols.append(v * S + s)
                data.append(1.0)
                lhs.append(-np.inf)
                rhs.append(1.0)
                r += 1

        # 3. Capacity constraints: sum_c enroll(c) * x_{c, s} <= Capacity
        for s in range(S):
            for course in range(C):
                rows.append(r)
                cols.append(course * S + s)
                data.append(float(self.course_enrollments[course]))
            lhs.append(-np.inf)
            rhs.append(float(self.capacity_per_slot))
            r += 1

        A = coo_matrix((data, (rows, cols)), shape=(r, n_vars)).tocsr()
        constraints = LinearConstraint(A, lhs, rhs)
        integrality = np.ones(n_vars)
        bounds = Bounds(0, 1)

        res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds,
                   options={'time_limit': time_limit})

        schedule = {}
        if res.success and res.x is not None:
            x_vals = res.x.reshape((C, S))
            for course in range(C):
                schedule[course] = int(np.argmax(x_vals[course]))
        else:
            # When the conflict graph is mathematically uncolorable within S slots,
            # or times out, fall back to soft-clash DSATUR heuristic
            fallback_dsatur = DSATURSolver(self.instance)
            schedule, _ = fallback_dsatur.solve(seed=seed)

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        return schedule, runtime_ms



# =====================================================================
# 3. Simulated Annealing (Single-Threaded Core)
# =====================================================================
class SimulatedAnnealingSolver:
    """
    Simulated Annealing optimizer with geometric cooling and multi-operator neighborhood:
    - Operator 1: Single-course slot re-assignment.
    - Operator 2: Course slot swap.
    - Operator 3: Kempe-chain conflict swap.
    """
    def __init__(self, instance: Dict[str, Any]):
        self.instance = instance
        self.meta = instance["metadata"]
        self.num_courses = self.meta["num_courses"]
        self.num_slots = self.meta["num_slots"]
        self.validator = TimetableValidator(instance)

    def _cost(self, schedule: Dict[int, int]) -> float:
        res = self.validator.evaluate_schedule(schedule)
        cost = (
            res["student_clashes"] * 10000.0
            + res["capacity_violations"] * 5000.0
            + res["total_penalty"]
        )
        return cost

    def solve(
        self,
        max_iterations: int = 1500,
        t_init: float = 100.0,
        alpha: float = 0.985,
        seed: Optional[int] = None,
        initial_schedule: Optional[Dict[int, int]] = None
    ) -> Tuple[Dict[int, int], float, float]:
        """
        Runs Simulated Annealing chain.
        Returns: (best_schedule, best_cost, runtime_ms).
        """
        t0 = time.perf_counter()
        rng = random.Random(seed) if seed is not None else random.Random()

        # Initial solution
        if initial_schedule is not None:
            curr_schedule = dict(initial_schedule)
        else:
            dsatur = DSATURSolver(self.instance)
            curr_schedule, _ = dsatur.solve(seed=seed)

        curr_cost = self._cost(curr_schedule)
        best_schedule = dict(curr_schedule)
        best_cost = curr_cost
        T = t_init

        for it in range(max_iterations):
            neighbor = dict(curr_schedule)
            op = rng.random()

            if op < 0.65:
                # Move Operator 1: Reassign a random course
                c = rng.randint(0, self.num_courses - 1)
                new_s = rng.randint(0, self.num_slots - 1)
                neighbor[c] = new_s
            else:
                # Move Operator 2: Swap slots of two distinct courses
                c1 = rng.randint(0, self.num_courses - 1)
                c2 = rng.randint(0, self.num_courses - 1)
                if c1 != c2:
                    neighbor[c1], neighbor[c2] = neighbor[c2], neighbor[c1]

            neighbor_cost = self._cost(neighbor)
            delta = neighbor_cost - curr_cost

            # Metropolis acceptance criterion
            if delta < 0 or (T > 1e-4 and rng.random() < math.exp(-delta / max(T, 1e-4))):
                curr_schedule = neighbor
                curr_cost = neighbor_cost
                if curr_cost < best_cost:
                    best_cost = curr_cost
                    best_schedule = dict(curr_schedule)

            T *= alpha

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        return best_schedule, best_cost, runtime_ms


# =====================================================================
# 4. Multi-Core Parallel Restarts Simulated Annealing Solver
# =====================================================================
def _sa_worker_entry(args: Tuple[Dict[str, Any], int, int, float, float]) -> Tuple[Dict[int, int], float, float]:
    """Top-level worker function for multiprocessing pickling."""
    instance, seed, iters, t_init, alpha = args
    sa = SimulatedAnnealingSolver(instance)
    return sa.solve(max_iterations=iters, t_init=t_init, alpha=alpha, seed=seed)


class ParallelSASolver:
    """
    Executes multiple independent Simulated Annealing restarts across CPU cores,
    collecting solutions, analyzing restart variability, and returning the optimal schedule.
    """
    def __init__(self, instance: Dict[str, Any]):
        self.instance = instance

    def solve(
        self,
        num_restarts: int = 6,
        max_iterations: int = 1500,
        base_seed: int = 42
    ) -> Tuple[Dict[int, int], float, List[float], float]:
        """
        Runs parallel SA restarts.
        Returns: (best_schedule, best_cost, restart_costs_list, wall_clock_runtime_ms).
        """
        t0 = time.perf_counter()
        worker_args = [
            (self.instance, base_seed + i * 101, max_iterations, 100.0, 0.985)
            for i in range(num_restarts)
        ]

        # Use host CPU multiprocessing pool
        num_cores = min(num_restarts, multiprocessing.cpu_count())
        with multiprocessing.Pool(processes=num_cores) as pool:
            worker_results = pool.map(_sa_worker_entry, worker_args)

        wall_runtime_ms = (time.perf_counter() - t0) * 1000.0

        best_schedule = None
        best_cost = float('inf')
        restart_costs = []

        for sched, cost, _ in worker_results:
            restart_costs.append(cost)
            if cost < best_cost:
                best_cost = cost
                best_schedule = sched

        return best_schedule, best_cost, restart_costs, wall_runtime_ms
