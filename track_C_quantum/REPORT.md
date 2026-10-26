# Track C: Quantum Optimization — Report

## 1. Objective
Apply quantum optimization algorithms (QAOA, VQE, PQCs, parameter-shift rule, SPSA, quantum natural gradient) to solve the QUBO problem formulated in Track B (e.g. Max-Cut). Compare with the classical baseline and analyze the impact of finite measurement shots, hardware noise, and barren plateaus.

## 2. Algorithms Tested
- **QAOA (Quantum Approximate Optimization Algorithm)**: Parametric ansatz with problem and mixer Hamiltonians.
- **VQE (Variational Quantum Eigensolver)**: Ground-state energy estimation.
- **Gradient Strategies**: Parameter-shift rule vs Simultaneous Perturbation Stochastic Approximation (SPSA) vs Quantum Natural Gradient (QNG).
- **Physical Realities**: Shot noise (e.g. 100 vs 1000 vs 8192 shots), depolarizing noise channel modeling, and barren plateau scaling.

## 3. Baseline
Classical exact/simulated annealing solver from Track B.

## 4. Fair Comparison Protocol
- Identical QUBO graph instance.
- Explicit labeling: `[Simulated: Statevector]`, `[Simulated: Shot-noise]`, `[Simulated: Thermal/Depolarizing Noise]`.
- Wall-clock time vs circuit depth / two-qubit CNOT counts.

## 5. Experimental Results & Verification
*(To be populated following approved test runs)*

## 6. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
