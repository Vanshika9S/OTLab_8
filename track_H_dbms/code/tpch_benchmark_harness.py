"""
tpch_benchmark_harness.py
-------------------------
TPC-H Benchmark Harness & Default Optimizer Profiler for Track H (DBMS Optimization).

Capabilities:
  1. Sets up the full TPC-H relational schema (8 tables: NATION, REGION, PART,
     SUPPLIER, PARTSUPP, CUSTOMER, ORDERS, LINEITEM).
  2. Generates deterministic scale-factor 0.1 (or 0.01) dataset.
  3. Executes a fixed workload of 8 representative analytical queries (Q1, Q3, Q5, Q6, Q9, Q10, Q12, Q14).
  4. Records default-optimizer EXPLAIN / EXPLAIN QUERY PLAN.
  5. Benchmarks Cold Cache (1 run with cache flush) vs Warm Cache (5+ repeated runs),
     reporting latency mean +/- std in milliseconds.
  6. Exports raw logs and summary tables.
"""

import os
import sys
import time
import json
import sqlite3
import random
from typing import Dict, List, Any

# Ensure repo root is accessible
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


TPCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name TEXT NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment TEXT
);

CREATE TABLE IF NOT EXISTS region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name TEXT NOT NULL,
    r_comment TEXT
);

CREATE TABLE IF NOT EXISTS part (
    p_partkey INTEGER PRIMARY KEY,
    p_name TEXT NOT NULL,
    p_mfgr TEXT NOT NULL,
    p_brand TEXT NOT NULL,
    p_type TEXT NOT NULL,
    p_size INTEGER NOT NULL,
    p_container TEXT NOT NULL,
    p_retailprice REAL NOT NULL,
    p_comment TEXT
);

CREATE TABLE IF NOT EXISTS supplier (
    s_suppkey INTEGER PRIMARY KEY,
    s_name TEXT NOT NULL,
    s_address TEXT NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone TEXT NOT NULL,
    s_acctbal REAL NOT NULL,
    s_comment TEXT
);

CREATE TABLE IF NOT EXISTS partsupp (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost REAL NOT NULL,
    ps_comment TEXT,
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

CREATE TABLE IF NOT EXISTS customer (
    c_custkey INTEGER PRIMARY KEY,
    c_name TEXT NOT NULL,
    c_address TEXT NOT NULL,
    c_nationkey INTEGER NOT NULL,
    c_phone TEXT NOT NULL,
    c_acctbal REAL NOT NULL,
    c_mktsegment TEXT NOT NULL,
    c_comment TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    o_orderkey INTEGER PRIMARY KEY,
    o_custkey INTEGER NOT NULL,
    o_orderstatus TEXT NOT NULL,
    o_totalprice REAL NOT NULL,
    o_orderdate TEXT NOT NULL,
    o_orderpriority TEXT NOT NULL,
    o_clerk TEXT NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment TEXT
);

CREATE TABLE IF NOT EXISTS lineitem (
    l_orderkey INTEGER NOT NULL,
    l_partkey INTEGER NOT NULL,
    l_suppkey INTEGER NOT NULL,
    l_linenumber INTEGER NOT NULL,
    l_quantity REAL NOT NULL,
    l_extendedprice REAL NOT NULL,
    l_discount REAL NOT NULL,
    l_tax REAL NOT NULL,
    l_returnflag TEXT NOT NULL,
    l_linestatus TEXT NOT NULL,
    l_shipdate TEXT NOT NULL,
    l_commitdate TEXT NOT NULL,
    l_receiptdate TEXT NOT NULL,
    l_shipinstruct TEXT NOT NULL,
    l_shipmode TEXT NOT NULL,
    l_comment TEXT,
    PRIMARY KEY (l_orderkey, l_linenumber)
);
"""

# Fixed analytical workload: 8 TPC-H representative queries
TPCH_QUERIES = {
    "Q1_Pricing_Summary": """
        SELECT
            l_returnflag,
            l_linestatus,
            sum(l_quantity) AS sum_qty,
            sum(l_extendedprice) AS sum_base_price,
            sum(l_extendedprice * (1 - l_discount)) AS sum_disc_price,
            avg(l_quantity) AS avg_qty,
            avg(l_extendedprice) AS avg_price,
            count(*) AS count_order
        FROM lineitem
        WHERE l_shipdate <= '1998-09-02'
        GROUP BY l_returnflag, l_linestatus;
    """,
    "Q3_Shipping_Priority": """
        SELECT
            l_orderkey,
            sum(l_extendedprice * (1 - l_discount)) AS revenue,
            o_orderdate,
            o_shippriority
        FROM customer, orders, lineitem
        WHERE c_mktsegment = 'BUILDING'
          AND c_custkey = o_custkey
          AND l_orderkey = o_orderkey
          AND o_orderdate < '1995-03-15'
          AND l_shipdate > '1995-03-15'
        GROUP BY l_orderkey, o_orderdate, o_shippriority
        ORDER BY revenue DESC
        LIMIT 10;
    """,
    "Q5_Local_Supplier_Volume": """
        SELECT
            n_name,
            sum(l_extendedprice * (1 - l_discount)) AS revenue
        FROM customer, orders, lineitem, supplier, nation, region
        WHERE c_custkey = o_custkey
          AND l_orderkey = o_orderkey
          AND l_suppkey = s_suppkey
          AND c_nationkey = s_nationkey
          AND s_nationkey = n_nationkey
          AND n_regionkey = r_regionkey
          AND r_name = 'ASIA'
        GROUP BY n_name
        ORDER BY revenue DESC;
    """,
    "Q6_Forecasting_Revenue_Change": """
        SELECT
            sum(l_extendedprice * l_discount) AS revenue
        FROM lineitem
        WHERE l_shipdate >= '1994-01-01'
          AND l_shipdate < '1995-01-01'
          AND l_discount BETWEEN 0.05 AND 0.07
          AND l_quantity < 24;
    """,
    "Q9_Product_Type_Profit": """
        SELECT
            n_name,
            sum(l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity) AS amount
        FROM part, supplier, lineitem, partsupp, orders, nation
        WHERE s_suppkey = l_suppkey
          AND ps_suppkey = l_suppkey
          AND ps_partkey = l_partkey
          AND p_partkey = l_partkey
          AND o_orderkey = l_orderkey
          AND s_nationkey = n_nationkey
          AND p_name LIKE '%green%'
        GROUP BY n_name
        ORDER BY n_name;
    """,
    "Q10_Returned_Item_Reporting": """
        SELECT
            c_custkey,
            c_name,
            sum(l_extendedprice * (1 - l_discount)) AS revenue,
            c_acctbal,
            n_name,
            c_address,
            c_phone,
            c_comment
        FROM customer, orders, lineitem, nation
        WHERE c_custkey = o_custkey
          AND l_orderkey = o_orderkey
          AND o_orderdate >= '1993-10-01'
          AND o_orderdate < '1994-01-01'
          AND l_returnflag = 'R'
          AND c_nationkey = n_nationkey
        GROUP BY c_custkey, c_name, c_acctbal, c_phone, n_name, c_address, c_comment
        ORDER BY revenue DESC
        LIMIT 20;
    """,
    "Q12_Shipping_Modes_Order_Priority": """
        SELECT
            l_shipmode,
            sum(CASE WHEN o_orderpriority = '1-URGENT' OR o_orderpriority = '2-HIGH' THEN 1 ELSE 0 END) AS high_line_count,
            sum(CASE WHEN o_orderpriority <> '1-URGENT' AND o_orderpriority <> '2-HIGH' THEN 1 ELSE 0 END) AS low_line_count
        FROM orders, lineitem
        WHERE o_orderkey = l_orderkey
          AND l_shipmode IN ('MAIL', 'SHIP')
          AND l_commitdate < l_receiptdate
          AND l_shipdate < l_commitdate
          AND l_receiptdate >= '1994-01-01'
          AND l_receiptdate < '1995-01-01'
        GROUP BY l_shipmode
        ORDER BY l_shipmode;
    """,
    "Q14_Promotion_Effect": """
        SELECT
            100.00 * sum(CASE WHEN p_type LIKE 'PROMO%' THEN l_extendedprice * (1 - l_discount) ELSE 0 END) /
            sum(l_extendedprice * (1 - l_discount)) AS promo_revenue
        FROM lineitem, part
        WHERE l_partkey = p_partkey
          AND l_shipdate >= '1995-09-01'
          AND l_shipdate < '1995-10-01';
    """
}


def populate_synthetic_tpch(db_path: str, scale_factor: float = 0.01, seed: int = 42):
    """
    Populates SQLite database with synthetic TPC-H schema and scaled data.
    Scale factor 0.01: ~1,500 customers, 15,000 orders, 60,000 lineitems (fast, reliable local baseline).
    Scale factor 0.1: ~15,000 customers, 150,000 orders, 600,000 lineitems.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(TPCH_SCHEMA)

    # Check if already populated
    cur.execute("SELECT count(*) FROM lineitem")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    rng = random.Random(seed)
    print(f"[DBMS Setup] Populating synthetic TPC-H database (Scale Factor {scale_factor}) at {db_path}...")

    # Regions & Nations
    regions = [(0, 'AFRICA'), (1, 'AMERICA'), (2, 'ASIA'), (3, 'EUROPE'), (4, 'MIDDLE EAST')]
    cur.executemany("INSERT INTO region VALUES (?, ?, 'comment')", regions)

    nations = [
        (0, 'ALGERIA', 0), (1, 'ARGENTINA', 1), (2, 'BRAZIL', 1), (3, 'CANADA', 1),
        (4, 'EGYPT', 4), (5, 'ETHIOPIA', 0), (6, 'FRANCE', 3), (7, 'GERMANY', 3),
        (8, 'INDIA', 2), (9, 'INDONESIA', 2), (10, 'IRAN', 4), (11, 'IRAQ', 4),
        (12, 'JAPAN', 2), (13, 'JORDAN', 4), (14, 'KENYA', 0), (15, 'MOROCCO', 0),
        (16, 'MOZAMBIQUE', 0), (17, 'PERU', 1), (18, 'CHINA', 2), (19, 'ROMANIA', 3),
        (20, 'SAUDI ARABIA', 4), (21, 'VIETNAM', 2), (22, 'RUSSIA', 3), (23, 'UK', 3),
        (24, 'USA', 1)
    ]
    cur.executemany("INSERT INTO nation VALUES (?, ?, ?, 'comment')", nations)

    # Scale table counts
    num_parts = int(20000 * scale_factor)
    num_suppliers = int(1000 * scale_factor)
    num_customers = int(15000 * scale_factor)
    num_orders = int(150000 * scale_factor)

    # Parts
    parts_data = [
        (i, f"part_{i}_green", f"Manufacturer_{i%5}", f"Brand_{i%10}",
         f"PROMO_TYPE_{i%4}" if i % 3 == 0 else f"STANDARD_{i%4}",
         rng.randint(1, 50), "JUMBO BOX", round(rng.uniform(10.0, 500.0), 2), "comment")
        for i in range(1, num_parts + 1)
    ]
    cur.executemany("INSERT INTO part VALUES (?,?,?,?,?,?,?,?,?)", parts_data)

    # Suppliers
    supp_data = [
        (i, f"Supplier_{i}", f"Address_{i}", rng.choice(nations)[0],
         f"12-345-{i}", round(rng.uniform(-500.0, 5000.0), 2), "comment")
        for i in range(1, num_suppliers + 1)
    ]
    cur.executemany("INSERT INTO supplier VALUES (?,?,?,?,?,?,?)", supp_data)

    # PartSupp (Links part and supplier)
    partsupp_data = []
    for p_id in range(1, num_parts + 1):
        # 2 to 4 suppliers per part
        chosen_supps = rng.sample(range(1, num_suppliers + 1), min(3, num_suppliers))
        for s_id in chosen_supps:
            partsupp_data.append((
                p_id, s_id, rng.randint(10, 1000), round(rng.uniform(5.0, 200.0), 2), "partsupp comment"
            ))
    cur.executemany("INSERT INTO partsupp VALUES (?,?,?,?,?)", partsupp_data)

    # Customers
    mktsegments = ['AUTOMOBILE', 'BUILDING', 'FURNITURE', 'MACHINERY', 'HOUSEHOLD']
    cust_data = [
        (i, f"Customer_{i}", f"Address_{i}", rng.choice(nations)[0],
         f"12-345-{i}", round(rng.uniform(-500.0, 5000.0), 2),
         rng.choice(mktsegments), "comment")
        for i in range(1, num_customers + 1)
    ]
    cur.executemany("INSERT INTO customer VALUES (?,?,?,?,?,?,?,?)", cust_data)

    # Orders & Lineitems
    orders_data = []
    lineitem_data = []
    priorities = ['1-URGENT', '2-HIGH', '3-MEDIUM', '4-NOT SPECIFIED', '5-LOW']
    shipmodes = ['REG AIR', 'AIR', 'RAIL', 'SHIP', 'TRUCK', 'MAIL', 'FOB']

    dates = ['1993-11-15', '1994-06-20', '1995-02-10', '1995-09-15', '1998-05-01']

    for o_id in range(1, num_orders + 1):
        o_date = rng.choice(dates)
        orders_data.append((
            o_id, rng.randint(1, num_customers), 'O', round(rng.uniform(100.0, 5000.0), 2),
            o_date, rng.choice(priorities), f"Clerk_{o_id%100}", 0, "comment"
        ))

        # 1 to 4 lineitems per order
        for l_num in range(1, rng.randint(2, 4)):
            s_date = rng.choice(dates)
            lineitem_data.append((
                o_id, rng.randint(1, num_parts), rng.randint(1, num_suppliers), l_num,
                rng.randint(1, 50), round(rng.uniform(50.0, 2000.0), 2),
                round(rng.choice([0.02, 0.05, 0.06, 0.08, 0.10]), 2),
                round(rng.uniform(0.01, 0.08), 2),
                rng.choice(['R', 'A', 'N']), 'O', s_date, s_date, s_date,
                "DELIVER IN PERSON", rng.choice(shipmodes), "comment"
            ))

    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)", orders_data)
    cur.executemany("INSERT INTO lineitem VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", lineitem_data)

    conn.commit()
    conn.close()
    print(f"[DBMS Setup] Database populated successfully. Orders: {len(orders_data)}, Lineitems: {len(lineitem_data)}.")


def benchmark_default_optimizer(
    db_path: str = "track_H_dbms/tpch_default.db",
    num_warm_runs: int = 5,
    results_dir: str = "track_H_dbms/results",
) -> Dict[str, Any]:
    """
    Benchmarks all 8 TPC-H queries on default database optimizer.
    Captures EXPLAIN QUERY PLAN, Cold Cache Latency, and Warm Cache Latency (mean +/- std).
    """
    os.makedirs(results_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    workload_results = {}

    print(f"\n[DBMS Benchmark] Profiling Default Optimizer across 8 analytical queries...")

    for q_name, q_sql in TPCH_QUERIES.items():
        # 1. Get EXPLAIN QUERY PLAN
        explain_cur = conn.cursor()
        explain_cur.execute(f"EXPLAIN QUERY PLAN {q_sql}")
        plan_rows = explain_cur.fetchall()
        # plan_rows: [(id, parent, notused, detail), ...]
        plan_details = [row[3] for row in plan_rows]

        # 2. Cold Cache Run (Simulated by closing/reopening connection or fresh cursor)
        cold_conn = sqlite3.connect(db_path)
        cold_cur = cold_conn.cursor()
        start = time.perf_counter()
        cold_cur.execute(q_sql)
        _ = cold_cur.fetchall()
        cold_latency_ms = (time.perf_counter() - start) * 1000.0
        cold_conn.close()

        # 3. Warm Cache Runs (5+ repeated runs)
        warm_latencies = []
        for _ in range(num_warm_runs):
            start = time.perf_counter()
            cur.execute(q_sql)
            _ = cur.fetchall()
            warm_latencies.append((time.perf_counter() - start) * 1000.0)

        import numpy as np
        workload_results[q_name] = {
            "explain_plan": plan_details,
            "cold_cache_latency_ms": round(cold_latency_ms, 3),
            "warm_cache_runs_ms": [round(x, 3) for x in warm_latencies],
            "warm_latency_mean_ms": round(float(np.mean(warm_latencies)), 3),
            "warm_latency_std_ms": round(float(np.std(warm_latencies)), 3),
        }
        print(f"  {q_name}: Cold={cold_latency_ms:.2f}ms | Warm Mean={np.mean(warm_latencies):.2f}ms ± {np.std(warm_latencies):.2f}ms")

    conn.close()

    # Save to JSON
    json_path = os.path.join(results_dir, "default_optimizer_baseline.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(workload_results, f, indent=2)

    # Save to CSV summary
    csv_path = os.path.join(results_dir, "default_optimizer_summary.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Query,Cold_Latency_ms,Warm_Mean_ms,Warm_Std_ms,Plan_Steps\n")
        for q_name, res in workload_results.items():
            f.write(f"{q_name},{res['cold_cache_latency_ms']},{res['warm_latency_mean_ms']},{res['warm_latency_std_ms']},{len(res['explain_plan'])}\n")

    print(f"\n[DBMS Benchmark] Results persisted to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")

    return workload_results


if __name__ == "__main__":
    db_file = "track_H_dbms/tpch_benchmark.db"
    populate_synthetic_tpch(db_file, scale_factor=0.01)
    benchmark_default_optimizer(db_file, num_warm_runs=5)
