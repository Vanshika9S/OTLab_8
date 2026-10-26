# Day 6 Prompt Log: Track C — Quantum Optimization

> **Track**: Track C (Quantum Optimization)  
> **Date**: October 26, 2026  
> **Model / Assistant**: Gemini 3.8 Flash (via Antigravity IDE)  
> **User State**: Active Workspace `c:\Users\satye\OneDrive\Desktop\OTLab8`

---

## 1. User Prompt
```markdown
Day 6: Track C. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_C_quantum_opt/ with the library chosen on Day 3.
Load the Max-Cut instances and classical baselines from Track B. Implement: QAOA on the Max-Cut QUBO, VQE on a small Hamiltonian, a parameterized circuit/QNN, parameter-shift gradients (verified against finite differences), SPSA, and quantum natural gradient.
Experiments: (a) finite shots, varying shot counts and reporting variance; (b) a hardware noise model; (c) barren plateaus, gradient variance vs qubit count; (d) QAOA depth p vs approximation ratio. Compare with the classical baseline using approximation ratio, number of circuit evaluations and runtime.
State clearly that this is simulation, not real hardware, and say what real hardware would change. Repeated seeds, mean and std. Tests on tiny known cases. Run DAILY CLOSE.
```

---

## 2. Intent & Planning
1. **Directory Aliasing**:
   - The user mentioned `track_C_quantum_opt/` while earlier skeleton used `track_C_quantum/`.
   - Action: Created a Windows NTFS directory junction `track_C_quantum_opt <<===>> track_C_quantum` using `cmd /c mklink /J track_C_quantum_opt track_C_quantum` to ensure identical file resolution across both naming schemes.
2. **Library Installation**:
   - Installed `qiskit-aer` (version 0.18.0) to enable fast C++ simulation and realistic noise modeling.
3. **Core Implementations**:
   - `track_C_quantum/code/qaoa_maxcut.py`: Depth-$p$ QAOA for Max-Cut, constructing problem unitary $R_{ZZ}$ and mixer unitary $R_X$, statevector and shot-based evaluation, and classical parameter optimization with COBYLA.
   - `track_C_quantum/code/vqe_solver.py`: VQE with 2-qubit Hardware-Efficient Ansatz (HEA) finding the ground state of molecular $H_2$ ($E_0 = -1.85727$ Ha), verified against exact diagonalization.
   - `track_C_quantum/code/gradients_and_qnn.py`: Parameter-shift rule (verified against finite differences to $1.38 \times 10^{-11}$ error), 2-measurement SPSA estimator, Quantum Natural Gradient with Fubini-Study / QFI metric tensor, and a parameterized QNN classifier.
4. **Four Core Experiments**:
   - `track_C_quantum/code/quantum_experiments.py`:
     - Experiment (a): Finite shots noise scaling across $N \in [100, 8192]$ (10 seeds each, empirical std vs $1/\sqrt{N}$).
     - Experiment (b): Hardware noise model (depolarizing gate error + readout error) tracking approximation ratio and ground state probability degradation.
     - Experiment (c): Barren plateau phenomenon on $n \in [2, 4, 6, 8, 10]$ qubits with 40 random initializations each, plotting $\text{Var}[\partial \langle O \rangle] \sim \mathcal{O}(2^{-n})$.
     - Experiment (d): QAOA depth $p \in [1, 2, 3]$ vs approximation ratio on Track B graphs (`Graph_5Ring`, `Graph_8Cube`, `Graph_12ER`), generating the Master Classical vs Quantum comparison table.
5. **Testing & QA**:
   - Created `track_C_quantum/tests/test_quantum_opt.py` with 6 unit tests.
   - Created root `conftest.py` and `pytest.ini` ensuring seamless test discovery across all repo tracks. Full repo suite achieved 26 passed tests in 5.59s.

---

## 3. Tool Calls & Execution Trace
- `run_command`: `cmd /c mklink /J track_C_quantum_opt track_C_quantum` (exited 0).
- `run_command`: `pip install qiskit-aer` (installed qiskit-aer 0.18.0).
- `write_to_file`: `track_C_quantum/code/qaoa_maxcut.py`.
- `write_to_file`: `track_C_quantum/code/vqe_solver.py`.
- `write_to_file`: `track_C_quantum/code/gradients_and_qnn.py`.
- `write_to_file`: `track_C_quantum/code/quantum_experiments.py`.
- `run_command`: `python track_C_quantum/code/quantum_experiments.py` (executed all 4 experiments, saved 5 CSVs and 4 PNG plots).
- `write_to_file`: `track_C_quantum/tests/test_quantum_opt.py`.
- `write_to_file`: `conftest.py` and `pytest.ini`.
- `run_command`: `pytest -v` (26 passed in 5.59s).
- `write_to_file`: `track_C_quantum/REPORT.md`.

---

## 4. Errors Encountered & Debugging
1. **ModuleNotFoundError during Pytest Collection**:
   - *Error*: `pytest -v` failed when discovering `track_A_continuous` and `track_B_discrete` because Windows environment lacked `PYTHONPATH=.`.
   - *Fix*: Created root [`conftest.py`](../../conftest.py) and [`pytest.ini`](../../pytest.ini) adding repo root to `sys.path`. All 26 tests across 6 tracks passed.
2. **Interactive PowerShell String Escaping in python -c**:
   - *Error*: Quotes inside f-strings caused syntax errors when executed via PowerShell CLI inline one-liners.
   - *Fix*: Formatted commands cleanly without nested quote conflicts.

---

## 5. Human-in-the-Loop Oversight
- Verified that all results are explicitly labelled `[Simulated]`.
- Verified that classical baselines from Track B were loaded directly from JSON/CSV files rather than hardcoded.
- Confirmed that real hardware limitations (decoherence, gate infidelity, SWAP overhead, cloud queuing) were rigorously explained in the technical report.
