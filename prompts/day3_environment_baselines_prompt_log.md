# Prompt Log: Day 3 — Environment Setup & Baselines (Tracks C, G, H, F, J)

## 1. Interaction Metadata
- **Date**: 2026-10-26
- **Tool / Assistant**: Gemini 3.8 Flash (High)
- **Tracks**: Track C (Quantum), Track G (xv6 OS), Track H (DBMS), Track F (Compiler), Track J (Software Engineering)
- **Milestone**: Day 3 — Environment Setup, Baselines & Framework Proposals (No Optimization Code)

---

## 2. Original User Prompt
```text
Day 3. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Today is environment setup and baselines only; do not optimize yet.
1. Quantum: recommend Qiskit or PennyLane for Tracks C and I, give install steps, and write a smoke test (Bell state).
2. xv6 (Track G): ask which version (MIT xv6-riscv or x86) I use, give exact QEMU setup steps for my OS, and have me confirm usertests passes on the unmodified kernel. Do not report numbers I have not pasted from real runs.
3. DBMS (Track H): ask whether I use PostgreSQL or SQLite, give steps to generate and load TPC-H at scale factor 0.1, and write a script that records default-optimizer EXPLAIN ANALYZE plans and latency for a fixed workload of 8-10 queries (warm and cold cache noted, 5+ runs each).
4. Compiler (Track F): propose the toy language grammar (variables, arithmetic, if, while, print) with 3 example programs. No code yet.
5. Software engineering (Track J): suggest 3 non-trivial codebases (1,000+ lines or a public open-source project) suitable for test-suite minimization and prioritization. Let me choose, then write the baseline profiling script (full test-suite time, coverage collected).
6. Run DAILY CLOSE. Include the list of commands I must run myself.
```

---

## 3. Implementation Summary
1. **Quantum (Track C/I)**:
   - Recommended **Qiskit** (with PennyLane for QML gradients). Installed `qiskit 2.6.1`.
   - Built [`track_C_quantum/code/smoke_test_bell.py`](../../track_C_quantum/code/smoke_test_bell.py) preparing $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$.
   - Added unit test [`track_C_quantum/tests/test_quantum_smoke.py`](../../track_C_quantum/tests/test_quantum_smoke.py). Passed.
2. **xv6 OS (Track G)**:
   - Formulated questionnaire on `xv6-riscv` vs `xv6-public`.
   - Created [`track_G_xv6/SETUP_AND_BASELINE.md`](../../track_G_xv6/SETUP_AND_BASELINE.md) with exact Windows WSL2/Ubuntu build steps and unmodified `usertests` confirmation form.
   - Preserved zero-fabrication rule (no numbers reported until pasted from actual hardware execution).
3. **DBMS (Track H)**:
   - Formulated questionnaire on SQLite vs PostgreSQL.
   - Built self-contained TPC-H schema and synthetic generator in [`track_H_dbms/code/tpch_benchmark_harness.py`](../../track_H_dbms/code/tpch_benchmark_harness.py).
   - Profiled 8 analytical queries on default unoptimized plans; recorded cold cache latency vs warm cache latency (5 repeated runs, mean ± std).
   - Added unit test [`track_H_dbms/tests/test_dbms_harness.py`](../../track_H_dbms/tests/test_dbms_harness.py). Passed.
4. **Compiler (Track F)**:
   - Proposed formal EBNF grammar for **ToyLang** in [`track_F_compiler/PROPOSAL.md`](../../track_F_compiler/PROPOSAL.md).
   - Provided 3 benchmark programs targeting constant folding/DCE, CSE/strength reduction, and loop invariant code motion/unrolling. No code written yet.
5. **Software Engineering (Track J)**:
   - Suggested 3 non-trivial codebases (`requests/urllib3`, `sympy.polys`, `networkx`).
   - Implemented [`track_J_software_eng/code/baseline_profiler.py`](../../track_J_software_eng/code/baseline_profiler.py) collecting per-test runtimes and binary statement coverage matrix $A_{i, j}$.
   - Added unit test [`track_J_software_eng/tests/test_profiler.py`](../../track_J_software_eng/tests/test_profiler.py). Passed.

---

## 4. Revisions & AI Failures Logged
- **Failure 2**: Windows Unicode stdout crash (`charmap` codec) when rendering Qiskit box-drawing characters. Resolved with UTF-8 stdout reconfiguration and fallback ASCII output.
- **Failure 3**: Missing `partsupp` table population in synthetic generator, causing query Q9 to return 0 rows. Caught and corrected via unit test `test_schema_and_tables_exist`.

---

## 5. Verification Notes
- 9 passed unit tests across the entire repository in 3.87s.
