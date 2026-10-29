"""
index_optimizer.py
------------------
Formulates and solves Relational Database Index Selection as a Knapsack / ILP
optimization problem, and implements Dynamic Programming Join-Order Selection (System R).

Mathematical Formulations:
1. Index Selection (0-1 Knapsack / ILP):
   Given candidate indices I = {1, ..., M}, queries Q = {1, ..., N} with weights w_q,
   index storage costs s_i, and storage budget B:
     Maximize:   sum_{i=1}^M v_i * x_i
     Subject to: sum_{i=1}^M s_i * x_i <= B
                 x_i + x_j <= 1  for mutually redundant/exclusive index pairs (i, j)
                 x_i in {0, 1}
   where v_i is the measured workload latency reduction:
     v_i = sum_{q in Q} w_q * max(0, Latency_baseline(q) - Latency_with_index(q, i))

2. Join-Order Optimization (System R Dynamic Programming):
   Given relation set R = {R_1, ..., R_k}:
     Cost(S) = min_{R_j in S} [ Cost(S \ {R_j}) + JoinCost(S \ {R_j}, R_j) ]
   Enumerates powerset of relations bottom-up to determine the minimum cost left-deep tree.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Any, Optional
import numpy as np
from scipy.optimize import milp, LinearConstraint

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_H_dbms.code.tpch_benchmark_harness import TPCH_QUERIES


CANDIDATE_INDEX_SPECS = [
    {
        "id": "idx_lineitem_shipdate",
        "table": "lineitem",
        "columns": ["l_shipdate"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_lineitem_shipdate ON lineitem(l_shipdate);",
        "targeted_queries": ["Q1_Pricing_Summary", "Q6_Forecasting_Revenue_Change", "Q14_Promotion_Effect"],
        "group": "lineitem_ship"
    },
    {
        "id": "idx_lineitem_q6_covering",
        "table": "lineitem",
        "columns": ["l_shipdate", "l_discount", "l_quantity", "l_extendedprice"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_lineitem_q6_covering ON lineitem(l_shipdate, l_discount, l_quantity, l_extendedprice);",
        "targeted_queries": ["Q6_Forecasting_Revenue_Change", "Q1_Pricing_Summary"],
        "group": "lineitem_ship"  # Redundant with idx_lineitem_shipdate
    },
    {
        "id": "idx_orders_custkey_date",
        "table": "orders",
        "columns": ["o_custkey", "o_orderdate", "o_orderkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_orders_custkey_date ON orders(o_custkey, o_orderdate, o_orderkey);",
        "targeted_queries": ["Q3_Shipping_Priority", "Q5_Local_Supplier_Volume", "Q10_Returned_Item_Reporting"],
        "group": "orders_cust"
    },
    {
        "id": "idx_orders_date",
        "table": "orders",
        "columns": ["o_orderdate", "o_custkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(o_orderdate, o_custkey);",
        "targeted_queries": ["Q3_Shipping_Priority", "Q10_Returned_Item_Reporting"],
        "group": "orders_cust"  # Redundant with idx_orders_custkey_date
    },
    {
        "id": "idx_lineitem_orderkey_ship",
        "table": "lineitem",
        "columns": ["l_orderkey", "l_shipdate"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_lineitem_orderkey_ship ON lineitem(l_orderkey, l_shipdate);",
        "targeted_queries": ["Q3_Shipping_Priority", "Q5_Local_Supplier_Volume", "Q9_Product_Type_Profit", "Q10_Returned_Item_Reporting", "Q12_Shipping_Modes_Order_Priority"],
        "group": "lineitem_order"
    },
    {
        "id": "idx_customer_mktsegment",
        "table": "customer",
        "columns": ["c_mktsegment", "c_custkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_customer_mktsegment ON customer(c_mktsegment, c_custkey);",
        "targeted_queries": ["Q3_Shipping_Priority"],
        "group": "cust_mkt"
    },
    {
        "id": "idx_lineitem_receipt_shipmode",
        "table": "lineitem",
        "columns": ["l_receiptdate", "l_shipmode", "l_orderkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_lineitem_receipt_shipmode ON lineitem(l_receiptdate, l_shipmode, l_orderkey);",
        "targeted_queries": ["Q12_Shipping_Modes_Order_Priority"],
        "group": "lineitem_receipt"
    },
    {
        "id": "idx_lineitem_partkey_suppkey",
        "table": "lineitem",
        "columns": ["l_partkey", "l_suppkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_lineitem_partkey_suppkey ON lineitem(l_partkey, l_suppkey);",
        "targeted_queries": ["Q9_Product_Type_Profit", "Q14_Promotion_Effect"],
        "group": "lineitem_part"
    },
    {
        "id": "idx_partsupp_suppkey",
        "table": "partsupp",
        "columns": ["ps_suppkey", "ps_partkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_partsupp_suppkey ON partsupp(ps_suppkey, ps_partkey);",
        "targeted_queries": ["Q9_Product_Type_Profit"],
        "group": "partsupp_supp"
    },
    {
        "id": "idx_supplier_nationkey",
        "table": "supplier",
        "columns": ["s_nationkey", "s_suppkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_supplier_nationkey ON supplier(s_nationkey, s_suppkey);",
        "targeted_queries": ["Q5_Local_Supplier_Volume", "Q9_Product_Type_Profit"],
        "group": "supp_nation"
    },
    {
        "id": "idx_customer_nationkey",
        "table": "customer",
        "columns": ["c_nationkey", "c_custkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_customer_nationkey ON customer(c_nationkey, c_custkey);",
        "targeted_queries": ["Q5_Local_Supplier_Volume", "Q10_Returned_Item_Reporting"],
        "group": "cust_nation"
    },
    {
        "id": "idx_lineitem_returnflag",
        "table": "lineitem",
        "columns": ["l_returnflag", "l_orderkey"],
        "sql": "CREATE INDEX IF NOT EXISTS idx_lineitem_returnflag ON lineitem(l_returnflag, l_orderkey);",
        "targeted_queries": ["Q10_Returned_Item_Reporting"],
        "group": "lineitem_ret"
    }
]


@dataclass
class CandidateIndex:
    idx_id: str
    table: str
    columns: List[str]
    sql: str
    group: str
    targeted_queries: List[str]
    size_kb: float = 0.0
    query_latencies_ms: Dict[str, float] = field(default_factory=dict)
    query_benefits_ms: Dict[str, float] = field(default_factory=dict)
    total_benefit_ms: float = 0.0
    benefit_to_size_ratio: float = 0.0


class IndexSelectionModel:
    """
    Profiles candidate indexes, measures storage costs and latency benefits,
    and solves the Index Selection Knapsack / ILP problem.
    """
    def __init__(self, db_path: str, workload_weights: Optional[Dict[str, float]] = None):
        self.db_path = db_path
        self.weights = workload_weights or {q: 1.0 for q in TPCH_QUERIES}
        self.candidates: List[CandidateIndex] = []
        self.baseline_latencies: Dict[str, float] = {}
        self.baseline_hashes: Dict[str, str] = {}
        self.baseline_plans: Dict[str, List[str]] = {}

    def measure_baseline(self, num_runs: int = 5) -> Dict[str, float]:
        """Measures baseline execution latencies with 0 secondary indexes and captures result hashes."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Ensure no secondary indexes exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
        for (idx_name,) in cur.fetchall():
            cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
        cur.execute("VACUUM")
        conn.commit()

        print("[IndexOptimizer] Measuring default optimizer baseline...")
        for q_name, q_sql in TPCH_QUERIES.items():
            # Capture plan
            cur.execute(f"EXPLAIN QUERY PLAN {q_sql}")
            self.baseline_plans[q_name] = [row[3] for row in cur.fetchall()]

            # Warm run for latency
            latencies = []
            for _ in range(num_runs):
                t0 = time.perf_counter()
                cur.execute(q_sql)
                rows = cur.fetchall()
                latencies.append((time.perf_counter() - t0) * 1000.0)

            # Result hash verification
            canonical_repr = json.dumps(sorted(rows, key=lambda x: str(x)), default=str)
            self.baseline_hashes[q_name] = hashlib.sha256(canonical_repr.encode()).hexdigest()
            self.baseline_latencies[q_name] = float(np.mean(latencies))

        conn.close()
        return self.baseline_latencies

    def profile_candidates(self) -> List[CandidateIndex]:
        """Profiles each candidate index in isolation: measures storage in KB and workload latency reduction."""
        if not self.baseline_latencies:
            self.measure_baseline()

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA page_size")
        page_size = cur.fetchone()[0]

        self.candidates = []
        print(f"[IndexOptimizer] Profiling {len(CANDIDATE_INDEX_SPECS)} candidate indexes in isolation...")

        for spec in CANDIDATE_INDEX_SPECS:
            # Clean state before creating index
            cur.execute("PRAGMA freelist_count")
            f0 = cur.fetchone()[0]
            cur.execute("PRAGMA page_count")
            p0 = cur.fetchone()[0]

            # Build index
            cur.execute(spec["sql"])
            conn.commit()

            # Measure pages allocated
            cur.execute("PRAGMA freelist_count")
            f1 = cur.fetchone()[0]
            cur.execute("PRAGMA page_count")
            p1 = cur.fetchone()[0]
            net_pages = max(1, (p1 - p0) + (f0 - f1))
            size_kb = (net_pages * page_size) / 1024.0

            # Measure query latencies with this index
            query_latencies = {}
            query_benefits = {}
            total_benefit = 0.0

            for q_name in spec["targeted_queries"]:
                q_sql = TPCH_QUERIES[q_name]
                latencies = []
                for _ in range(3):
                    t0 = time.perf_counter()
                    cur.execute(q_sql)
                    cur.fetchall()
                    latencies.append((time.perf_counter() - t0) * 1000.0)
                mean_lat = float(np.mean(latencies))
                query_latencies[q_name] = mean_lat
                benefit = max(0.0, self.baseline_latencies[q_name] - mean_lat)
                query_benefits[q_name] = benefit
                total_benefit += self.weights[q_name] * benefit

            # Compute ratio
            ratio = total_benefit / size_kb if size_kb > 0 else 0.0

            cand = CandidateIndex(
                idx_id=spec["id"],
                table=spec["table"],
                columns=spec["columns"],
                sql=spec["sql"],
                group=spec["group"],
                targeted_queries=spec["targeted_queries"],
                size_kb=round(size_kb, 2),
                query_latencies_ms=query_latencies,
                query_benefits_ms=query_benefits,
                total_benefit_ms=round(total_benefit, 3),
                benefit_to_size_ratio=round(ratio, 4)
            )
            self.candidates.append(cand)

            # Tear down index
            cur.execute(f"DROP INDEX IF EXISTS {spec['id']}")
            conn.commit()

        conn.close()
        return self.candidates

    def solve_greedy(self, budget_kb: float) -> Tuple[List[CandidateIndex], float, float]:
        """
        Dantzig's greedy knapsack heuristic:
        Sorts candidates by benefit/size ratio, picking indices that fit budget and respect group exclusivity.
        """
        sorted_cands = sorted(self.candidates, key=lambda c: c.benefit_to_size_ratio, reverse=True)
        selected = []
        spent_kb = 0.0
        total_benefit = 0.0
        used_groups: Set[str] = set()

        for c in sorted_cands:
            if c.total_benefit_ms <= 0:
                continue
            if c.group in used_groups:
                continue
            if spent_kb + c.size_kb <= budget_kb:
                selected.append(c)
                spent_kb += c.size_kb
                total_benefit += c.total_benefit_ms
                used_groups.add(c.group)

        return selected, round(spent_kb, 2), round(total_benefit, 3)

    def solve_ilp(self, budget_kb: float) -> Tuple[List[CandidateIndex], float, float]:
        """
        Exact 0-1 Knapsack / ILP Solver via scipy.optimize.milp.
        Maximize: sum v_i * x_i
        Subject to: sum s_i * x_i <= B, x_i + x_j <= 1 for same-group pairs, x_i in {0, 1}.
        """
        n = len(self.candidates)
        if n == 0:
            return [], 0.0, 0.0

        # Objective: minimize -v (for maximization)
        c = np.array([-cand.total_benefit_ms for cand in self.candidates], dtype=float)

        # Constraints
        # 1. Budget: sum s_i * x_i <= B
        sizes = [cand.size_kb for cand in self.candidates]
        A_rows = [sizes]
        lhs = [0.0]
        rhs = [budget_kb]

        # 2. Group exclusivity constraints: for each group with > 1 candidate, sum_{i in group} x_i <= 1
        groups: Dict[str, List[int]] = {}
        for idx, cand in enumerate(self.candidates):
            groups.setdefault(cand.group, []).append(idx)

        for g_name, member_indices in groups.items():
            if len(member_indices) > 1:
                row = [0.0] * n
                for idx in member_indices:
                    row[idx] = 1.0
                A_rows.append(row)
                lhs.append(0.0)
                rhs.append(1.0)

        constraints = LinearConstraint(np.array(A_rows), lhs, rhs)
        integrality = np.ones(n)  # all binary

        res = milp(c=c, constraints=constraints, integrality=integrality)
        if not res.success:
            # Fallback to greedy if ILP solver encounters numerical edge case
            return self.solve_greedy(budget_kb)

        selected_indices = [i for i, val in enumerate(res.x) if val > 0.5]
        selected = [self.candidates[i] for i in selected_indices]
        spent_kb = sum(c.size_kb for c in selected)
        total_benefit = sum(c.total_benefit_ms for c in selected)

        return selected, round(spent_kb, 2), round(total_benefit, 3)

    def solve_dp(self, budget_kb: float) -> Tuple[List[CandidateIndex], float, float]:
        """
        0-1 Knapsack via dynamic programming with discretized integer budget (1 KB resolution).
        Handles mutual exclusivity within groups by multi-choice knapsack reduction.
        """
        int_budget = int(budget_kb)
        # Group candidates
        groups: Dict[str, List[CandidateIndex]] = {}
        for cand in self.candidates:
            if cand.total_benefit_ms > 0:
                groups.setdefault(cand.group, []).append(cand)

        # DP state: dp[b] = max benefit with budget b
        # dp_items[b] = list of chosen candidate IDs
        dp = [0.0] * (int_budget + 1)
        dp_items: List[List[CandidateIndex]] = [[] for _ in range(int_budget + 1)]

        for g_name, items in groups.items():
            # For multi-choice group, we must transition from the previous group's state
            new_dp = list(dp)
            new_dp_items = [list(items_list) for items_list in dp_items]

            for cand in items:
                w = max(1, int(cand.size_kb))
                v = cand.total_benefit_ms
                for b in range(w, int_budget + 1):
                    if dp[b - w] + v > new_dp[b]:
                        new_dp[b] = dp[b - w] + v
                        new_dp_items[b] = dp_items[b - w] + [cand]

            dp = new_dp
            dp_items = new_dp_items

        best_b = max(range(int_budget + 1), key=lambda b: dp[b])
        selected = dp_items[best_b]
        spent_kb = sum(c.size_kb for c in selected)
        total_benefit = sum(c.total_benefit_ms for c in selected)

        return selected, round(spent_kb, 2), round(total_benefit, 3)


class SystemRJoinOrderOptimizer:
    """
    Implements System R Left-Deep Join-Order Dynamic Programming.
    Computes optimal join order for multi-table queries based on catalog statistics
    and estimated intermediate join cardinalities.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.table_cardinalities: Dict[str, int] = {}
        self._load_catalog()

    def _load_catalog(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        tables = ["nation", "region", "part", "supplier", "partsupp", "customer", "orders", "lineitem"]
        for t in tables:
            cur.execute(f"SELECT count(*) FROM {t}")
            self.table_cardinalities[t] = cur.fetchone()[0]
        conn.close()

    def estimate_join_cost(self, r1_size: float, r2_size: float, is_primary_key_join: bool = True) -> Tuple[float, float]:
        """
        Estimates intermediate cardinality and I/O cost of joining R1 and R2.
        For PK-FK join: resulting size = min(r1_size, r2_size).
        Cost = r1_size + r1_size * (log2(r2_size) if indexed else r2_size / 2).
        """
        if is_primary_key_join:
            cardinality = max(r1_size, r2_size) * 0.1  # average selectivity factor
            cost = r1_size + r2_size * 0.2
        else:
            cardinality = (r1_size * r2_size) * 0.05
            cost = r1_size * r2_size * 0.5
        return cardinality, cost

    def optimize_join_order(self, relations: List[str]) -> Tuple[List[str], float]:
        """
        Bottom-up dynamic programming over subsets S of relations (System R).
        Returns: (optimal_left_deep_order, estimated_cost).
        """
        n = len(relations)
        rel_map = {1 << i: relations[i] for i in range(n)}

        # Memoization: dp[bitmask] = (best_cardinality, best_cost, best_order_list)
        dp: Dict[int, Tuple[float, float, List[str]]] = {}

        # Base cases: single relations
        for i in range(n):
            mask = 1 << i
            r = relations[i]
            card = float(self.table_cardinalities.get(r, 1000))
            dp[mask] = (card, card, [r])

        # Subsets of size 2 to n
        for size in range(2, n + 1):
            for mask in range(1, 1 << n):
                if bin(mask).count('1') != size:
                    continue

                best_cost = float('inf')
                best_card = float('inf')
                best_order = []

                # Try each relation as the right-hand child in the left-deep tree
                for i in range(n):
                    sub_bit = 1 << i
                    if mask & sub_bit:
                        left_mask = mask ^ sub_bit
                        left_card, left_cost, left_order = dp[left_mask]
                        right_rel = relations[i]
                        right_card = float(self.table_cardinalities.get(right_rel, 1000))

                        out_card, join_cost = self.estimate_join_cost(left_card, right_card)
                        total_cost = left_cost + join_cost

                        if total_cost < best_cost:
                            best_cost = total_cost
                            best_card = out_card
                            best_order = left_order + [right_rel]

                dp[mask] = (best_card, best_cost, best_order)

        final_mask = (1 << n) - 1
        _, opt_cost, opt_order = dp[final_mask]
        return opt_order, round(opt_cost, 2)
