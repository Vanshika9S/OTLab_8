# Day 12 Prompt Log: Track I — Quantum Algorithms & QML Advantage

## 1. Original User Prompt
```markdown
Day 12: Track I. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_I_quantum_algos/ on a simulator.
1. Implement every quantum algorithm my class taught (from my Day 1 answer): Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE, Shor (small N), and quantum annealing (with the limits of embedding QUBO on annealing hardware). Write at least two circuits by hand, without library implementations. Test each on known answers.
2. Run at least one experiment on a hardware noise model, or real hardware if I have access, and show how noise degrades the result.
3. QML vs classical: train a variational classifier, QNN or quantum kernel and an equivalent classical model on the same data. Report accuracy, training time, parameter count and number of circuit evaluations (10 seeds, mean and std).
4. Grover vs linear search: compare query counts, gate counts and wall-clock time. Make clear what is theoretical, what is simulated, and that simulation overhead hides any wall-clock advantage.
5. Write an honest analysis of where quantum does not help (simulation overhead, noise, barren plateaus, data loading), contrasted with the measured Track D parallel speedups. An honest negative result is acceptable.
6. Run DAILY CLOSE.
```

---

## 2. AI Execution Strategy & Trajectory
1. **Directory Alignment & Junction Configuration**:
   - Mapped `track_I_quantum_algos` to `track_I_quantum_advantage` via Windows NTFS junction so both path conventions resolve seamlessly.
2. **Algorithm Implementation**:
   - Implemented `track_I_quantum_advantage/code/quantum_algorithms.py`:
     - Hand-crafted Deutsch-Jozsa with gate-by-gate assembly and pure NumPy statevector reference.
     - Hand-crafted Bernstein-Vazirani with CNOT secret encoding.
     - Grover's unstructured search with multi-controlled phase oracle and inversion-about-the-mean diffuser.
     - Hand-crafted Quantum Fourier Transform with controlled phase rotations and swap network ($10^{-15}$ Frobenius error vs analytical DFT).
     - Quantum Phase Estimation estimating phases of $T$, $S$, and $Z$ gates with exact dyadic precision.
     - Shor's algorithm factoring $N=15$ with $a=7$, extracting period $r=4$ and factors $[3, 5]$.
     - Quantum annealing minor embedding simulator evaluating physical qubit blowup $\mathcal{O}(n^2)$ and chain break probabilities.
3. **Hardware Noise Model Benchmark**:
   - Implemented `track_I_quantum_advantage/code/noise_experiment.py` sweeping depolarizing gate errors and readout errors across 10 seeds, demonstrating exponential fidelity decay.
4. **QML vs Classical Comparison**:
   - Implemented `track_I_quantum_advantage/code/qml_benchmark.py` comparing a 2-qubit VQC against Classical Logistic Regression, a 2-Layer MLP, and an RBF SVM across 10 dataset seeds.
5. **Grover vs Linear Search Scaling**:
   - Implemented `track_I_quantum_advantage/code/grover_vs_linear_search.py` evaluating query complexity, gate counts, and CPU simulation wall-clock times.
6. **Master Experiment Runner & Visual Dashboard**:
   - Executed `run_track_i_benchmarks.py` generating 5 CSV summaries and publication-grade 4-panel figure `track_i_quantum_performance.png`.
7. **Verification & Testing**:
   - Created test suite `tests/test_quantum_algorithms.py` with 14 unit tests (100% passing). Monorepo suite: 67/67 passing.
8. **Failure Logging**:
   - Logged Case 9 in `FAILURE_LOG.md`: Grover amplitude over-rotation due to symmetric rounding instead of integer floor.

---

## 3. Resulting Code Changes & Artifacts
- **Core Library**: [`track_I_quantum_advantage/code/quantum_algorithms.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/code/quantum_algorithms.py)
- **Noise Experiment**: [`track_I_quantum_advantage/code/noise_experiment.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/code/noise_experiment.py)
- **QML Benchmark**: [`track_I_quantum_advantage/code/qml_benchmark.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/code/qml_benchmark.py)
- **Grover Scaling**: [`track_I_quantum_advantage/code/grover_vs_linear_search.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/code/grover_vs_linear_search.py)
- **Experiment Runner**: [`track_I_quantum_advantage/code/run_track_i_benchmarks.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/code/run_track_i_benchmarks.py)
- **Unit Tests**: [`track_I_quantum_advantage/tests/test_quantum_algorithms.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/tests/test_quantum_algorithms.py)
- **Technical Report**: [`track_I_quantum_advantage/REPORT.md`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/REPORT.md)
- **Failure Log**: [`FAILURE_LOG.md`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/FAILURE_LOG.md#L147-L160) (Case 9)
