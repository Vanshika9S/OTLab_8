"""
write_cost_benchmark.py
-----------------------
Evaluates the Write-Cost Overhead of Secondary Indexes.
Measures the insertion latency, throughput (rows/sec), and write amplification factor
as secondary B-Tree indexes are progressively added to the LINEITEM table.

Demonstrates that while secondary indexes accelerate read-intensive analytical queries,
they introduce significant write penalties by requiring synchronous updates to multiple
underlying B-Trees on every INSERT/UPDATE operation.
"""

import os
import sys
import time
import sqlite3
import random
from typing import Dict, List, Any
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


INDEX_CONFIGURATIONS = [
    {
        "name": "Config_0_No_Secondary_Indexes",
        "description": "Baseline: Only primary key (l_orderkey, l_linenumber)",
        "indexes": []
    },
    {
        "name": "Config_1_Single_Index",
        "description": "1 secondary index: idx_lineitem_shipdate",
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_lineitem_shipdate ON lineitem(l_shipdate);"
        ]
    },
    {
        "name": "Config_2_Two_Indexes",
        "description": "2 secondary indexes: shipdate + receipt_shipmode",
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_lineitem_shipdate ON lineitem(l_shipdate);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_receipt_shipmode ON lineitem(l_receiptdate, l_shipmode, l_orderkey);"
        ]
    },
    {
        "name": "Config_3_Three_Indexes",
        "description": "3 secondary indexes: shipdate + receipt_shipmode + orderkey_ship",
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_lineitem_shipdate ON lineitem(l_shipdate);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_receipt_shipmode ON lineitem(l_receiptdate, l_shipmode, l_orderkey);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_orderkey_ship ON lineitem(l_orderkey, l_shipdate);"
        ]
    },
    {
        "name": "Config_5_Five_Indexes",
        "description": "5 secondary indexes: heavy indexing configuration",
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_lineitem_shipdate ON lineitem(l_shipdate);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_receipt_shipmode ON lineitem(l_receiptdate, l_shipmode, l_orderkey);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_orderkey_ship ON lineitem(l_orderkey, l_shipdate);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_partkey_suppkey ON lineitem(l_partkey, l_suppkey);",
            "CREATE INDEX IF NOT EXISTS idx_lineitem_returnflag ON lineitem(l_returnflag, l_orderkey);"
        ]
    }
]


def generate_batch_lineitems(batch_size: int = 3000, seed: int = 42) -> List[tuple]:
    """Generates a synthetic batch of lineitems for write-cost benchmarking."""
    rng = random.Random(seed)
    base_order = 800000
    rows = []
    shipmodes = ['REG AIR', 'AIR', 'RAIL', 'SHIP', 'TRUCK', 'MAIL', 'FOB']
    dates = ['1994-03-12', '1995-07-21', '1996-11-04', '1997-02-18']

    for i in range(batch_size):
        s_date = rng.choice(dates)
        rows.append((
            base_order + (i // 3),
            rng.randint(1, 2000),
            rng.randint(1, 100),
            (i % 3) + 1,
            rng.randint(1, 50),
            round(rng.uniform(50.0, 2000.0), 2),
            round(rng.choice([0.02, 0.05, 0.06, 0.08, 0.10]), 2),
            round(rng.uniform(0.01, 0.08), 2),
            rng.choice(['R', 'A', 'N']),
            'O',
            s_date, s_date, s_date,
            "TEST WRITE INSTRUCT",
            rng.choice(shipmodes),
            "benchmark insert comment"
        ))
    return rows


def run_write_cost_evaluation(
    db_path: str = "track_H_dbms/tpch_benchmark.db",
    batch_size: int = 3000,
    num_trials: int = 10,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """Evaluates insert latency across index configurations with 10 repeated trials."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Drop all existing secondary indexes
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
    for (idx_name,) in cur.fetchall():
        cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
    conn.commit()

    test_batches = [generate_batch_lineitems(batch_size, seed + t) for t in range(num_trials)]
    results = []
    base_latency = None

    print(f"\n[WriteCostBenchmark] Evaluating insert write overhead across {len(INDEX_CONFIGURATIONS)} configurations ({batch_size} rows per trial, {num_trials} trials)...")

    for cfg in INDEX_CONFIGURATIONS:
        cfg_name = cfg["name"]
        num_indexes = len(cfg["indexes"])

        # Setup indexes for this configuration
        # First drop any non-primary indexes
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
        for (idx_name,) in cur.fetchall():
            cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
        for idx_sql in cfg["indexes"]:
            cur.execute(idx_sql)
        conn.commit()

        latencies_ms = []
        for trial_idx in range(num_trials):
            batch = test_batches[trial_idx]
            # Time the batch insert with commit
            t0 = time.perf_counter()
            cur.executemany("INSERT INTO lineitem VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            conn.commit()
            t_insert = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(t_insert)

            # Clean up test rows
            cur.execute("DELETE FROM lineitem WHERE l_orderkey >= 800000")
            conn.commit()

        mean_lat = float(np.mean(latencies_ms))
        std_lat = float(np.std(latencies_ms))
        tput = (batch_size / (mean_lat / 1000.0))

        if base_latency is None:
            base_latency = mean_lat
            amp_factor = 1.00
        else:
            amp_factor = mean_lat / base_latency

        res = {
            "configuration": cfg_name,
            "num_secondary_indexes": num_indexes,
            "batch_size": batch_size,
            "insert_latency_mean_ms": round(mean_lat, 2),
            "insert_latency_std_ms": round(std_lat, 2),
            "throughput_rows_per_sec": round(tput, 1),
            "write_amplification_factor": round(amp_factor, 2)
        }
        results.append(res)
        print(f"  {cfg_name} ({num_indexes} indexes): {mean_lat:.2f} ms ± {std_lat:.2f} ms | Throughput: {tput:.0f} rows/s | Amplification: {amp_factor:.2f}x")

    # Clean up any leftover secondary indexes
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
    for (idx_name,) in cur.fetchall():
        cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
    conn.commit()
    conn.close()

    return results


if __name__ == "__main__":
    db = "track_H_dbms/tpch_benchmark.db"
    run_write_cost_evaluation(db)
