"""
test_quantum_smoke.py
---------------------
Unit test verifying quantum circuit execution for Bell State (|Phi+>).
"""

import pytest
from track_C_quantum.code.smoke_test_bell import run_bell_smoke_test


def test_bell_state_generation():
    """
    Verifies that Bell state generates approximately equal probabilities
    for |00> and |11>, and zero probability for |01> and |10>.
    """
    res = run_bell_smoke_test(shots=1000)
    counts = res["counts"]

    # Either Qiskit counts or probability dict
    total = sum(counts.values())
    p00 = counts.get("00", 0) / total
    p11 = counts.get("11", 0) / total

    # Check |00| and |11| each close to 0.5 (within sampling tolerance)
    assert 0.40 <= p00 <= 0.60, f"Expected p00 ~ 0.5, got {p00}"
    assert 0.40 <= p11 <= 0.60, f"Expected p11 ~ 0.5, got {p11}"

    # Check cross states |01> and |10> are strictly absent or zero in ideal statevector
    assert counts.get("01", 0) == 0
    assert counts.get("10", 0) == 0
