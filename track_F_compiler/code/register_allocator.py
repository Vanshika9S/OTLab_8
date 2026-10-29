"""
register_allocator.py
---------------------
Register Allocation formulated as an Optimization Problem:
  Interference Graph Construction, Liveness Analysis, and Graph Coloring with Spill Minimization.

Mathematical Formulation:
  Variables/Temporaries: V = {v_1, ..., v_n}
  Physical Registers:    K (e.g. K = 3 or 4)
  Interference Graph:    G = (V, E) where (u, v) in E iff u and v are simultaneously live.
  Spill Cost:            w_v = uses(v) + defs(v) (memory traffic penalty if spilled)

  ILP Formulation (Chapter 6):
    Decision Variables:
      x_{v, r} in {0, 1} : 1 if variable v is assigned to physical register r in {1, ..., K}
      s_v in {0, 1}      : 1 if variable v is spilled to memory

    Objective:
      min sum_{v in V} w_v * s_v   (Minimize total spill cost)

    Constraints:
      1. Assignment:  sum_{r=1}^K x_{v, r} + s_v = 1      forall v in V
      2. Non-conflict: x_{u, r} + x_{v, r} <= 1           forall (u, v) in E, forall r in {1, ..., K}
      3. Binary:       x_{v, r}, s_v in {0, 1}

Solvers Compared:
  1. Exact ILP (SciPy HiGHS branch-and-cut)
  2. Greedy Chaitin-Briggs Graph Coloring Heuristic (degree-based simplification & greedy assign)
  3. Naive Baseline (spill all variables / no register reuse)
"""

import sys
import os
import time
from typing import Dict, List, Set, Tuple, Any, Optional
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_F_compiler.code.ir import Instruction


class LivenessAnalyzer:
    """Computes variable live ranges and constructs the interference graph G = (V, E)."""

    @staticmethod
    def analyze(instructions: List[Instruction]) -> Tuple[List[Set[str]], List[Set[str]], Set[str]]:
        """
        Backward dataflow liveness analysis:
          in[i] = use[i] union (out[i] \\ def[i])
          out[i] = in[i + 1] (for sequential execution)
        """
        n = len(instructions)
        in_sets: List[Set[str]] = [set() for _ in range(n)]
        out_sets: List[Set[str]] = [set() for _ in range(n)]
        all_variables: Set[str] = set()

        for inst in instructions:
            all_variables.update(inst.get_defs())
            all_variables.update(inst.get_uses())

        # Fixed point iteration
        changed = True
        while changed:
            changed = False
            for i in reversed(range(n)):
                inst = instructions[i]
                # out[i] is union of in[succ]
                new_out = set()
                if i + 1 < n:
                    new_out.update(in_sets[i + 1])

                defs = inst.get_defs()
                uses = inst.get_uses()
                new_in = uses | (new_out - defs)

                if new_in != in_sets[i] or new_out != out_sets[i]:
                    in_sets[i] = new_in
                    out_sets[i] = new_out
                    changed = True

        return in_sets, out_sets, all_variables

    @staticmethod
    def build_interference_graph(
        instructions: List[Instruction]
    ) -> Tuple[List[str], Set[Tuple[str, str]], Dict[str, int]]:
        """
        Builds interference graph G = (V, E) and calculates variable spill costs.
        """
        in_sets, out_sets, all_vars = LivenessAnalyzer.analyze(instructions)
        variables = sorted(list(all_vars))
        edges: Set[Tuple[str, str]] = set()

        # Two variables interfere if both appear in the same live_out or live_in set
        for i in range(len(instructions)):
            for s in (in_sets[i], out_sets[i]):
                s_list = sorted(list(s))
                for j in range(len(s_list)):
                    for k in range(j + 1, len(s_list)):
                        u, v = s_list[j], s_list[k]
                        edges.add((u, v))

        # Calculate spill costs: w_v = uses(v) + defs(v)
        spill_costs: Dict[str, int] = {v: 0 for v in variables}
        for inst in instructions:
            for d in inst.get_defs():
                spill_costs[d] += 1
            for u in inst.get_uses():
                spill_costs[u] += 1

        return variables, edges, spill_costs


class ILPRegisterAllocator:
    """Exact register allocation via Mixed-Integer Linear Programming (HiGHS)."""

    @staticmethod
    def allocate(
        variables: List[str],
        edges: Set[Tuple[str, str]],
        spill_costs: Dict[str, int],
        K_registers: int = 3
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n = len(variables)
        var_to_idx = {v: i for i, v in enumerate(variables)}

        if n == 0:
            return {"allocation": {}, "spilled": [], "total_spill_cost": 0, "runtime_ms": 0.0}

        # Variables: for each v in V:
        # x_{v, 0}, ..., x_{v, K-1} (registers), and s_v (spill)
        # Total decision variables = n * (K + 1)
        num_vars = n * (K_registers + 1)

        def x_idx(v_i: int, r: int) -> int:
            return v_i * (K_registers + 1) + r

        def s_idx(v_i: int) -> int:
            return v_i * (K_registers + 1) + K_registers

        # Objective vector c: minimize sum w_v * s_v
        c = np.zeros(num_vars)
        for v_name, v_i in var_to_idx.items():
            c[s_idx(v_i)] = spill_costs.get(v_name, 1)

        rows = []
        lhs = []
        rhs = []

        # Constraint 1: sum_{r=0}^{K-1} x_{v, r} + s_v = 1 for each variable
        for v_i in range(n):
            row = np.zeros(num_vars)
            for r in range(K_registers):
                row[x_idx(v_i, r)] = 1.0
            row[s_idx(v_i)] = 1.0
            rows.append(row)
            lhs.append(1.0)
            rhs.append(1.0)

        # Constraint 2: x_{u, r} + x_{v, r} <= 1 for all (u, v) in E, for all r
        for u_name, v_name in edges:
            if u_name in var_to_idx and v_name in var_to_idx:
                u_i = var_to_idx[u_name]
                v_i = var_to_idx[v_name]
                for r in range(K_registers):
                    row = np.zeros(num_vars)
                    row[x_idx(u_i, r)] = 1.0
                    row[x_idx(v_i, r)] = 1.0
                    rows.append(row)
                    lhs.append(0.0)
                    rhs.append(1.0)

        A_mat = np.array(rows)
        constraints = LinearConstraint(A_mat, lhs, rhs)
        bounds = Bounds(0.0, 1.0)
        integrality = np.ones(num_vars)  # All variables are binary integer

        res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integrality)
        dt_ms = (time.perf_counter() - t0) * 1000.0

        allocation: Dict[str, str] = {}
        spilled: List[str] = []
        total_spill_cost = 0

        if res.success:
            sol = np.round(res.x).astype(int)
            for v_name, v_i in var_to_idx.items():
                is_spilled = bool(sol[s_idx(v_i)] == 1)
                if is_spilled:
                    spilled.append(v_name)
                    total_spill_cost += spill_costs[v_name]
                else:
                    assigned_r = None
                    for r in range(K_registers):
                        if sol[x_idx(v_i, r)] == 1:
                            assigned_r = f"R{r}"
                            break
                    allocation[v_name] = assigned_r or "R0"
        else:
            # Fallback if solver fails
            spilled = list(variables)
            total_spill_cost = sum(spill_costs.values())

        return {
            "method": "Exact ILP (HiGHS)",
            "allocation": allocation,
            "spilled": spilled,
            "total_spill_cost": total_spill_cost,
            "registers_used": len(set(allocation.values())),
            "runtime_ms": dt_ms,
            "success": res.success
        }


class GreedyChaitinBriggsAllocator:
    """Heuristic register allocation based on Chaitin-Briggs degree simplification."""

    @staticmethod
    def allocate(
        variables: List[str],
        edges: Set[Tuple[str, str]],
        spill_costs: Dict[str, int],
        K_registers: int = 3
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        adj: Dict[str, Set[str]] = {v: set() for v in variables}
        for u, v in edges:
            if u in adj and v in adj:
                adj[u].add(v)
                adj[v].add(u)

        degrees = {v: len(adj[v]) for v in variables}
        active_nodes = set(variables)
        stack = []
        spilled = set()

        # Simplification phase
        while active_nodes:
            # Find a node with degree < K
            low_degree_nodes = [v for v in active_nodes if degrees[v] < K_registers]
            if low_degree_nodes:
                # Pick low-degree node
                chosen = low_degree_nodes[0]
                stack.append(chosen)
                active_nodes.remove(chosen)
                for neighbor in adj[chosen]:
                    if neighbor in active_nodes:
                        degrees[neighbor] -= 1
            else:
                # Potential spill: pick node with minimum spill_cost / degree
                chosen = min(active_nodes, key=lambda v: spill_costs.get(v, 1) / (degrees[v] + 1e-6))
                stack.append(chosen)
                active_nodes.remove(chosen)
                for neighbor in adj[chosen]:
                    if neighbor in active_nodes:
                        degrees[neighbor] -= 1

        # Select & Color phase
        allocation: Dict[str, str] = {}
        available_colors = [f"R{r}" for r in range(K_registers)]

        while stack:
            v = stack.pop()
            neighbor_colors = {allocation[nb] for nb in adj[v] if nb in allocation}
            free_colors = [c for c in available_colors if c not in neighbor_colors]
            if free_colors:
                allocation[v] = free_colors[0]
            else:
                spilled.add(v)

        dt_ms = (time.perf_counter() - t0) * 1000.0
        total_spill_cost = sum(spill_costs[v] for v in spilled)

        return {
            "method": "Greedy Chaitin-Briggs",
            "allocation": allocation,
            "spilled": sorted(list(spilled)),
            "total_spill_cost": total_spill_cost,
            "registers_used": len(set(allocation.values())),
            "runtime_ms": dt_ms,
            "success": True
        }


class NaiveRegisterAllocator:
    """Baseline: spills all variables/temporaries to memory slots (zero register reuse)."""

    @staticmethod
    def allocate(
        variables: List[str],
        spill_costs: Dict[str, int]
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        total_spill_cost = sum(spill_costs.values())
        dt_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "method": "Naive Spill-All Baseline",
            "allocation": {},
            "spilled": list(variables),
            "total_spill_cost": total_spill_cost,
            "registers_used": 0,
            "runtime_ms": dt_ms,
            "success": True
        }
