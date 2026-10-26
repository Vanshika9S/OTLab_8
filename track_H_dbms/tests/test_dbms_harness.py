"""
test_dbms_harness.py
--------------------
Unit tests verifying the TPC-H query execution and schema integrity in Track H.
"""

import os
import sqlite3
import pytest
from track_H_dbms.code.tpch_benchmark_harness import TPCH_SCHEMA, TPCH_QUERIES, populate_synthetic_tpch


@pytest.fixture(scope="module")
def test_db(tmp_path_factory):
    db_file = str(tmp_path_factory.mktemp("db") / "test_tpch.db")
    populate_synthetic_tpch(db_file, scale_factor=0.005, seed=123)
    return db_file


def test_schema_and_tables_exist(test_db):
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    tables = [
        "nation", "region", "part", "supplier",
        "partsupp", "customer", "orders", "lineitem"
    ]
    for tbl in tables:
        cur.execute(f"SELECT count(*) FROM {tbl}")
        count = cur.fetchone()[0]
        assert count > 0, f"Table {tbl} is empty"
    conn.close()


def test_queries_execute_successfully(test_db):
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    for q_name, sql in TPCH_QUERIES.items():
        cur.execute(sql)
        rows = cur.fetchall()
        assert isinstance(rows, list)
    conn.close()
