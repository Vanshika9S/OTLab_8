"""
test_suite_optimizer.py
-----------------------
Algorithms for Test-Suite Minimization and Prioritization:
1. Naive Baseline (Full Execution & Arbitrary Subset Selection)
2. Greedy Weighted Set Cover (Chvatal 1979) with O(ln |S|) guarantee
3. Exact Integer Linear Programming (HiGHS Branch-and-Cut via scipy.optimize.milp)
4. Budget-Constrained Prioritization under CI/CD time limits

Track J: Software-Engineering Optimization
Course: Optimization Techniques
"""

import time
import numpy as np
import scipy.sparse as sp
from scipy.optimize import milp, LinearConstraint, Bounds
from typing import Dict, List, Set, Tuple, Any

from track_J_software_eng.code.test_suite_model import RegressionTestSuiteModel


class TestSuiteOptimizer:
    __test__ = False
    """
    Solves Test-Suite Minimization formulated as Weighted Set Cover:
      min  sum_{t in T} c_t * x_t
      s.t. sum_{t : s in Cover(t)} x_t >= 1,  for all statements s in S
           x_t in {0, 1}
    """
    def __init__(self, model: RegressionTestSuiteModel):
        self.model = model
        self.profile = model.get_full_test_suite_profile()
        self.tests = self.profile["tests_list"]
        self.statements = self.profile["statements_list"]
        self.costs = np.array([self.profile["test_runtimes"][t] for t in self.tests])
        self.coverage_map = self.profile["coverage_map"]
        self.A = self.profile["incidence_matrix"]  # Shape: (num_statements, num_tests)
        self.num_statements, self.num_tests = self.A.shape

    # -----------------------------------------------------------------
    # 1. Naive Baseline: Full Suite Execution
    # -----------------------------------------------------------------
    def solve_naive_full_suite(self) -> Dict[str, Any]:
        """Runs all available tests in default order."""
        t0 = time.perf_counter()
        selected = list(self.tests)
        solver_time = time.perf_counter() - t0
        
        covered_stmts = set()
        for t in selected:
            covered_stmts.update(self.coverage_map[t])
            
        suite_runtime = float(np.sum(self.costs))
        killed, total_mut, mut_score = self.model.evaluate_mutants_killed(selected)
        
        return {
            "method": "Naive Full Suite",
            "selected_tests": selected,
            "num_selected": len(selected),
            "suite_runtime_ms": round(suite_runtime, 3),
            "runtime_saved_pct": 0.0,
            "statements_covered": len(covered_stmts),
            "coverage_pct": (len(covered_stmts) / self.num_statements) * 100.0,
            "mutants_killed": killed,
            "total_mutants": total_mut,
            "mutation_score_pct": mut_score,
            "solver_overhead_ms": round(solver_time * 1000.0, 4),
        }

    # -----------------------------------------------------------------
    # 2. Greedy Weighted Set Cover (Chvatal 1979)
    # -----------------------------------------------------------------
    def solve_greedy_set_cover(self) -> Dict[str, Any]:
        r"""
        Greedy Set Cover with cost-effectiveness ratio:
          Select test t* = argmax |Cover(t) \cap Uncovered| / c_t
        Guarantees H(|S|) <= ln(|S|) + 1 approximation factor.
        """
        t0 = time.perf_counter()
        uncovered = set(self.statements)
        selected = []
        selected_set = set()
        
        while uncovered:
            best_test = None
            best_ratio = -1.0
            
            for t in self.tests:
                if t in selected_set:
                    continue
                new_covered = len(self.coverage_map[t].intersection(uncovered))
                if new_covered > 0:
                    cost = self.profile["test_runtimes"][t]
                    ratio = new_covered / cost
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_test = t
                        
            if best_test is None:
                # All reachable statements covered
                break
                
            selected.append(best_test)
            selected_set.add(best_test)
            uncovered.difference_update(self.coverage_map[best_test])
            
        solver_time = (time.perf_counter() - t0) * 1000.0
        
        selected_costs = [self.profile["test_runtimes"][t] for t in selected]
        suite_runtime = float(np.sum(selected_costs))
        full_runtime = float(np.sum(self.costs))
        saved_pct = ((full_runtime - suite_runtime) / full_runtime) * 100.0
        
        covered_stmts = set()
        for t in selected:
            covered_stmts.update(self.coverage_map[t])
            
        killed, total_mut, mut_score = self.model.evaluate_mutants_killed(selected)
        
        return {
            "method": "Greedy Weighted Set Cover",
            "selected_tests": selected,
            "num_selected": len(selected),
            "suite_runtime_ms": round(suite_runtime, 3),
            "runtime_saved_pct": round(saved_pct, 2),
            "statements_covered": len(covered_stmts),
            "coverage_pct": (len(covered_stmts) / self.num_statements) * 100.0,
            "mutants_killed": killed,
            "total_mutants": total_mut,
            "mutation_score_pct": mut_score,
            "solver_overhead_ms": round(solver_time, 4),
        }

    # -----------------------------------------------------------------
    # 3. Exact Integer Linear Programming (ILP via HiGHS)
    # -----------------------------------------------------------------
    def solve_ilp_exact_set_cover(self) -> Dict[str, Any]:
        """
        Exact minimum-cost set cover solved via SciPy HiGHS:
          min  c^T x
          s.t. A x >= 1
               x in {0, 1}
        """
        t0 = time.perf_counter()
        
        # c: vector of test runtimes
        c = self.costs
        # Integrality: all variables are binary (1 for integer)
        integrality = np.ones(self.num_tests, dtype=int)
        bounds = Bounds(lb=np.zeros(self.num_tests), ub=np.ones(self.num_tests))
        
        # Constraints: A x >= 1
        A_sparse = sp.csr_matrix(self.A)
        constraints = LinearConstraint(
            A_sparse,
            lb=np.ones(self.num_statements),
            ub=np.full(self.num_statements, np.inf)
        )
        
        res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)
        solver_time = (time.perf_counter() - t0) * 1000.0
        
        if not res.success:
            raise RuntimeError(f"ILP Set Cover solver failed: {res.status}")
            
        x_opt = np.round(res.x).astype(int)
        selected = [self.tests[j] for j in range(self.num_tests) if x_opt[j] == 1]
        
        suite_runtime = float(res.fun)
        full_runtime = float(np.sum(self.costs))
        saved_pct = ((full_runtime - suite_runtime) / full_runtime) * 100.0
        
        covered_stmts = set()
        for t in selected:
            covered_stmts.update(self.coverage_map[t])
            
        killed, total_mut, mut_score = self.model.evaluate_mutants_killed(selected)
        
        return {
            "method": "Exact ILP Set Cover (HiGHS)",
            "selected_tests": selected,
            "num_selected": len(selected),
            "suite_runtime_ms": round(suite_runtime, 3),
            "runtime_saved_pct": round(saved_pct, 2),
            "statements_covered": len(covered_stmts),
            "coverage_pct": (len(covered_stmts) / self.num_statements) * 100.0,
            "mutants_killed": killed,
            "total_mutants": total_mut,
            "mutation_score_pct": mut_score,
            "solver_overhead_ms": round(solver_time, 4),
        }

    # -----------------------------------------------------------------
    # 4. Budget-Constrained Prioritization (Knapsack Coverage)
    # -----------------------------------------------------------------
    def solve_budget_constrained_prioritization(self, budget_ratio: float = 0.50) -> Dict[str, Any]:
        """
        Maximizes covered statements subject to a strict time budget B:
          max  sum_s y_s
          s.t. sum_t c_t * x_t <= B
               y_s <= sum_t A_{s, t} * x_t,  for all s in S
               x_t in {0, 1}, y_s in {0, 1}
        """
        t0 = time.perf_counter()
        total_time = float(np.sum(self.costs))
        B = total_time * budget_ratio
        
        # Variables: x (tests, len m), y (statements, len n)
        # Total vars: m + n
        m, n = self.num_tests, self.num_statements
        
        # Objective: minimize -sum(y) = maximize sum(y)
        c_obj = np.zeros(m + n)
        c_obj[m:] = -1.0  # maximize y_s
        
        integrality = np.ones(m + n, dtype=int)
        bounds = Bounds(lb=np.zeros(m + n), ub=np.ones(m + n))
        
        # Constraint 1: sum_t c_t * x_t <= B
        # Constraint 2: y_s - sum_t A_{s, t} * x_t <= 0  ==>  [-A, I] [x; y] <= 0
        row_budget = np.zeros((1, m + n))
        row_budget[0, :m] = self.costs
        
        A_block = sp.hstack([-sp.csr_matrix(self.A), sp.eye(n, format="csr")], format="csr")
        full_A = sp.vstack([sp.csr_matrix(row_budget), A_block], format="csr")
        
        lhs_lb = np.full(1 + n, -np.inf)
        lhs_ub = np.zeros(1 + n)
        lhs_ub[0] = B
        
        constraints = LinearConstraint(full_A, lb=lhs_lb, ub=lhs_ub)
        res = milp(c=c_obj, integrality=integrality, bounds=bounds, constraints=constraints)
        solver_time = (time.perf_counter() - t0) * 1000.0
        
        if not res.success:
            raise RuntimeError(f"Budget Prioritization failed: {res.status}")
            
        x_opt = np.round(res.x[:m]).astype(int)
        selected = [self.tests[j] for j in range(m) if x_opt[j] == 1]
        
        selected_costs = [self.profile["test_runtimes"][t] for t in selected]
        suite_runtime = float(np.sum(selected_costs))
        saved_pct = ((total_time - suite_runtime) / total_time) * 100.0
        
        covered_stmts = set()
        for t in selected:
            covered_stmts.update(self.coverage_map[t])
            
        killed, total_mut, mut_score = self.model.evaluate_mutants_killed(selected)
        
        return {
            "method": f"Budget Prioritization ({int(budget_ratio * 100)}% Budget)",
            "budget_limit_ms": round(B, 3),
            "selected_tests": selected,
            "num_selected": len(selected),
            "suite_runtime_ms": round(suite_runtime, 3),
            "runtime_saved_pct": round(saved_pct, 2),
            "statements_covered": len(covered_stmts),
            "coverage_pct": round((len(covered_stmts) / n) * 100.0, 2),
            "mutants_killed": killed,
            "total_mutants": total_mut,
            "mutation_score_pct": mut_score,
            "solver_overhead_ms": round(solver_time, 4),
        }
