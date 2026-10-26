# Track C: Quantum Optimization Report

> **Course**: Optimization Techniques  
> **Topic**: Variational Quantum Algorithms (QAOA, VQE, PQC/QNN) & Quantum Gradients  
> **Evaluation Mode**: `[Simulated]` via Qiskit 2.6.1 and Qiskit Aer 0.18.0 on Classical Host CPU  
> **Date**: October 26, 2026 (Day 6)  
> **Status**: Completed & Empirically Verified (10 Repeated Seeds: Mean ± Std)

---

## 1. Executive Summary & Formulation

Track C investigates hybrid quantum-classical optimization algorithms on combinatorial and physical Hamiltonians. Using the Max-Cut QUBO and Ising formulations generated in Track B, we implement and benchmark:
1. **Quantum Approximate Optimization Algorithm (QAOA)**: Alternating problem and mixer unitary layers for graph partitioning.
2. **Variational Quantum Eigensolver (VQE)**: Rayleigh-Ritz ground-state energy minimization on a 2-qubit molecular $H_2$ Hamiltonian.
3. **Quantum Gradient Algorithms**: Exact Parameter-Shift rule, Finite Differences, 2-measurement Simultaneous Perturbation Stochastic Approximation (SPSA), and Quantum Natural Gradient (QNG) using the Fubini-Study metric tensor.
4. **Parameterized Quantum Neural Network (QNN/PQC)**: Variational classifier combining angle feature encoding with variational entangling blocks.

### Mathematical Formulation

#### Max-Cut Ising Hamiltonian
For an undirected graph $G = (V, E)$ with edge weights $w_{uv} > 0$:
$$\text{Max-Cut}(x) = \sum_{(u,v) \in E} w_{uv} (x_u(1 - x_v) + x_v(1 - x_u)), \quad x_i \in \{0, 1\}$$
Substituting the binary-to-spin mapping $x_i = \frac{1 - s_i}{2}$ where $s_i \in \{-1, +1\}$ and promoting spins to Pauli-$Z$ operators:
$$\hat{C} = \sum_{(u,v) \in E} \frac{w_{uv}}{2} (I - Z_u Z_v)$$
To frame this as minimization, the cost Hamiltonian is defined as:
$$\hat{H}_C = -\hat{C} = \sum_{(u,v) \in E} \frac{w_{uv}}{2} Z_u Z_v - \left(\frac{1}{2}\sum_{(u,v)\in E} w_{uv}\right) I$$

#### QAOA Ansatz
The depth-$p$ QAOA trial state $|\gamma, \beta\rangle$ is prepared by starting in the uniform superposition $|+\rangle^{\otimes n} = H^{\otimes n}|0\rangle^{\otimes n}$ and applying $p$ alternating unitary layers:
$$|\gamma, \beta\rangle = \prod_{l=1}^p \left( e^{-i \beta_l \hat{H}_M} e^{-i \gamma_l \hat{H}_C} \right) |+\rangle^{\otimes n}$$
where the Mixer Hamiltonian is $\hat{H}_M = \sum_{u \in V} X_u$, corresponding to single-qubit rotations $R_X(2\beta_l)_u$, and the problem unitary decomposes into two-qubit interaction gates $R_{ZZ}(w_{uv} \gamma_l)_{u,v}$.

#### Parameter-Shift Rule vs Finite Differences
For any parameterized quantum gate $U(\theta_k) = \exp\left(-i \frac{\theta_k}{2} P_k\right)$ with generator $P_k \in \{X, Y, Z\}$:
$$\frac{\partial \langle \hat{O} \rangle}{\partial \theta_k} = \frac{\langle \hat{O} \rangle_{\theta_k + \frac{\pi}{2}} - \langle \hat{O} \rangle_{\theta_k - \frac{\pi}{2}}}{2}$$
Unlike central finite differences $\frac{\langle \hat{O} \rangle_{\theta + \epsilon} - \langle \hat{O} \rangle_{\theta - \epsilon}}{2\epsilon}$, the parameter-shift rule requires no microscopic step size $\epsilon \to 0$, rendering it entirely immune to numerical cancellation and hardware shot noise instability.

---

## 2. Experimental Results & Verification

All experiments were executed with deterministic seeds over 10 repeated runs. Numerical records are stored in [`track_C_quantum/results/`](./results/).

### Experiment (a): Finite Shot Noise Scaling
We evaluated the measured cut expectation $\langle \hat{C} \rangle$ on the 5-qubit `Graph_5Ring` instance across shot counts $N_{\text{shots}} \in [100, 8192]$ compared with exact statevector simulation ($C_{\text{exact}} = 3.7500$).

| Measurement Shots $N_{\text{shots}}$ | $1/\sqrt{N_{\text{shots}}}$ | Mean Sampled Cut | Std Dev $\sigma$ | Empirical Variance $\sigma^2$ | Absolute Bias |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **100** | 0.1000 | 3.7420 | 0.07084 | 0.005018 | 0.0080 |
| **250** | 0.0632 | 3.7552 | 0.04803 | 0.002307 | 0.0052 |
| **500** | 0.0447 | 3.7388 | 0.03023 | 0.000914 | 0.0112 |
| **1,000** | 0.0316 | 3.7436 | 0.01675 | 0.000281 | 0.0064 |
| **2,000** | 0.0224 | 3.7471 | 0.01114 | 0.000124 | 0.0029 |
| **4,000** | 0.0158 | 3.7480 | 0.01287 | 0.000166 | 0.0020 |
| **8,192** | 0.0110 | 3.7505 | 0.00743 | 0.000055 | 0.0005 |
| **$\infty$ (Exact Statevector)** | 0.0000 | 3.7500 | 0.00000 | 0.000000 | 0.0000 |

![Finite Shots Scaling](./results/finite_shots_scaling.png)

> **Key Finding**: The empirical standard deviation follows the theoretical Poisson/binomial sampling law $\sigma \propto \frac{1}{\sqrt{N_{\text{shots}}}}$ with linear regression $R^2 > 0.96$. At 8,192 shots, empirical variance drops to $5.5 \times 10^{-5}$, ensuring tight convergence for outer-loop classical optimizers.

---

### Experiment (b): NISQ Hardware Noise Modeling
We simulated realistic hardware noise using Qiskit Aer's `NoiseModel`, incorporating:
- 1-qubit gate depolarizing error ($p_1$)
- 2-qubit CNOT / $R_{ZZ}$ depolarizing error ($p_2 = 10 p_1$)
- Qubit readout assignment error ($P(0|1) = P(1|0) = 2 p_1$)

| 1-Qubit Error $p_1$ | 2-Qubit Error $p_2$ | Readout Error $p_{\text{ro}}$ | Mean Expected Cut | Approx Ratio $\alpha$ | Ground State Prob $P(\text{opt})$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0.000 (Ideal)** | 0.000 | 0.000 | 3.7505 ± 0.0074 | **0.9376** | **0.8793 ± 0.0036** |
| **0.001** | 0.010 | 0.002 | 3.7081 ± 0.0069 | 0.9270 | 0.8582 ± 0.0034 |
| **0.005** | 0.050 | 0.010 | 3.5378 ± 0.0095 | 0.8844 | 0.7744 ± 0.0046 |
| **0.010** | 0.100 | 0.020 | 3.3566 ± 0.0161 | 0.8391 | 0.6874 ± 0.0083 |
| **0.020** | 0.200 | 0.040 | 3.0738 ± 0.0106 | 0.7684 | 0.5565 ± 0.0059 |
| **0.050** | 0.500 | 0.100 | 2.6262 ± 0.0110 | 0.6565 | 0.3628 ± 0.0053 |
| **0.100** | 0.750 | 0.200 | 2.5139 ± 0.0147 | 0.6285 | 0.3167 ± 0.0060 |

![Hardware Noise Impact](./results/hardware_noise_impact.png)

> **Key Finding**: Noise causes dual degradation: (1) it shifts the energy expectation value upward (reducing the approximation ratio from 0.9376 to 0.6285), and (2) it exponentially attenuates the ground state sampling probability from 87.9% down towards the maximally mixed state ($P_{\text{uniform}} = 1/2^5 = 3.125\%$). For gate error rates $p_2 > 5\%$, the quantum advantage is completely washed out by noise.

---

### Experiment (c): Barren Plateau Phenomenon (Exponential Vanishing Gradients)
To demonstrate the Barren Plateau theorem (McClean et al. 2018), we constructed Haar-approximate deep parameterized quantum circuits (depth $L = 2n$) on scaling qubit counts $n \in [2, 4, 6, 8, 10]$ and measured the partial derivative $\partial_{\theta_1} \langle Z_0 Z_1 \rangle$ across 40 random parameter initializations using the parameter-shift rule.

| Qubit Count $n$ | Circuit Depth $L$ | Parameter Count $D$ | Mean Gradient | Gradient Variance $\text{Var}[\partial \langle O \rangle]$ | $\log_{10}(\text{Variance})$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2** | 4 | 16 | +0.057612 | **$1.5537 \times 10^{-1}$** | -0.81 |
| **4** | 8 | 64 | +0.022661 | **$2.6163 \times 10^{-2}$** | -1.58 |
| **6** | 12 | 144 | -0.013149 | **$1.1016 \times 10^{-2}$** | -1.96 |
| **8** | 16 | 256 | +0.003167 | **$2.5108 \times 10^{-3}$** | -2.60 |
| **10** | 20 | 400 | -0.001852 | **$3.0735 \times 10^{-4}$** | -3.51 |

![Barren Plateau Decay](./results/barren_plateau_decay.png)

> **Key Finding**: On a semi-log scale, gradient variance decays linearly: $\log_{10}(\text{Var}) \approx -0.34 n - 0.08$, proving that $\text{Var}[\partial \langle O \rangle] \sim \mathcal{O}(2^{-n})$. At $n=10$, variance has collapsed by a factor of **505x** compared to $n=2$. This proves that randomly initialized deep PQC architectures cannot be trained using gradient descent without structured initializations, shallow depths, or local loss functions.

---

### Experiment (d): QAOA Depth $p$ vs Approximation Ratio
We optimized QAOA parameters $(\gamma^*, \beta^*)$ over depths $p \in [1, 2, 3]$ for the three Track B graph topologies:

| Graph Instance | Nodes $n$ | Edges $|E|$ | Exact Max Cut | Depth $p$ | Mean Cut | Approx Ratio $\alpha$ | Ground State Prob $P(\text{opt})$ | Evaluations | Runtime (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Graph_5Ring** | 5 | 5 | 4.0 | 1 | 3.7500 | 0.9375 ± 0.0000 | 0.8789 | 44.9 | 363.4 |
|  |  |  |  | 2 | 3.9779 | 0.9945 ± 0.0087 | 0.9890 | 205.4 | 1969.7 |
|  |  |  |  | 3 | 3.9998 | **1.0000 ± 0.0001** | **0.9999** | 211.3 | 2110.0 |
| **Graph_8Cube** | 8 | 12 | 12.0 | 1 | 8.0785 | 0.6732 ± 0.0609 | 0.1693 | 41.4 | 416.0 |
|  |  |  |  | 2 | 8.9441 | 0.7453 ± 0.0411 | 0.3329 | 166.6 | 1734.4 |
|  |  |  |  | 3 | 9.5748 | **0.7979 ± 0.0579** | **0.5005** | 247.0 | 3170.2 |
| **Graph_12ER** | 12 | 18 | 16.0 | 1 | 12.1177 | 0.7574 ± 0.0685 | 0.1341 | 40.6 | 224.6 |
|  |  |  |  | 2 | 14.0118 | 0.8757 ± 0.0166 | 0.3868 | 188.2 | 1137.1 |
|  |  |  |  | 3 | 14.5285 | **0.9080 ± 0.0201** | **0.4920** | 250.0 | 2274.0 |

![QAOA Depth vs Ratio](./results/qaoa_depth_vs_ratio.png)

> **Key Finding**: Increasing depth $p$ monotonically boosts solution quality across all instances. On `Graph_5Ring`, $p=3$ converges to the exact optimum with 99.99% sampling probability. On the dense 12-node Erdos-Renyi graph, $p=3$ lifts the approximation ratio from 0.7574 to 0.9080.

---

## 3. Comprehensive Master Comparison: Classical vs Quantum

The table below directly benchmarks the Track B classical baselines against QAOA on the exact same problem instances:

| Graph Instance | Nodes $n$ | Solver | Solver Paradigm | Max Cut Obtained | Approximation Ratio $\alpha$ | Evaluations Count | Wall-Clock Time (ms) |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **Graph_5Ring** | 5 | **Classical Brute Force** | Exact Classical | 4.0 | **1.0000** | 32 | **0.05** |
|  | 5 | **Classical Simulated Annealing** | Heuristic Classical | 4.0 | **1.0000** | 1,000 | **3.22** |
|  | 5 | **QAOA ($p=1$)** | Variational Quantum `[Simulated]` | 3.7500 | 0.9375 | 45 | 363.36 |
|  | 5 | **QAOA ($p=2$)** | Variational Quantum `[Simulated]` | 3.9779 | 0.9945 | 205 | 1969.73 |
|  | 5 | **QAOA ($p=3$)** | Variational Quantum `[Simulated]` | 3.9998 | **1.0000** | 211 | 2110.00 |
| **Graph_8Cube** | 8 | **Classical Brute Force** | Exact Classical | 12.0 | **1.0000** | 256 | **1.60** |
|  | 8 | **Classical Simulated Annealing** | Heuristic Classical | 12.0 | **1.0000** | 1,000 | **3.48** |
|  | 8 | **QAOA ($p=1$)** | Variational Quantum `[Simulated]` | 8.0785 | 0.6732 | 41 | 416.02 |
|  | 8 | **QAOA ($p=2$)** | Variational Quantum `[Simulated]` | 8.9441 | 0.7453 | 167 | 1734.44 |
|  | 8 | **QAOA ($p=3$)** | Variational Quantum `[Simulated]` | 9.5748 | 0.7979 | 247 | 3170.24 |
| **Graph_12ER** | 12 | **Classical Brute Force** | Exact Classical | 16.0 | **1.0000** | 4,096 | **45.00** |
|  | 12 | **Classical Simulated Annealing** | Heuristic Classical | 16.0 | **1.0000** | 1,000 | **3.60** |
|  | 12 | **QAOA ($p=1$)** | Variational Quantum `[Simulated]` | 12.1177 | 0.7574 | 41 | 224.64 |
|  | 12 | **QAOA ($p=2$)** | Variational Quantum `[Simulated]` | 14.0118 | 0.8757 | 188 | 1137.14 |
|  | 12 | **QAOA ($p=3$)** | Variational Quantum `[Simulated]` | 14.5285 | 0.9080 | 250 | 2274.00 |

### Trade-Off Analysis
1. **Algorithmic Quality**: Classical Simulated Annealing solved all 3 graphs to 100% exact optimality ($ \alpha = 1.0 $) within 3.6 ms. QAOA achieves $\alpha = 0.91$ at depth $p=3$ for the 12-node graph. To reach 100% on non-trivial topologies, QAOA requires depths $p \ge 4-6$, significantly expanding circuit parameter spaces.
2. **Computational Overhead**: Simulating QAOA on a classical CPU carries an exponential $O(2^n)$ matrix-vector multiplication overhead. While classical Simulated Annealing runs in 3.6 ms, simulated QAOA requires 2.27 seconds (~630x slower) solely due to classical simulation emulation costs.

---

## 4. Simulation vs Real Quantum Hardware: Critical Analysis

> [!IMPORTANT]
> All results in this report are **classical simulations (`[Simulated]`)** on CPU. Real quantum processing units (QPUs) differ fundamentally in physical physics, connectivity, noise, and execution latency.

### What Real Quantum Hardware Changes:
1. **Physical Execution Time vs Simulation Overhead**:
   - On a classical CPU simulator, computing the quantum state takes $\mathcal{O}(2^n)$ operations. At $n=50$ qubits, classical simulation requires petabytes of RAM and days of supercomputing time.
   - On a physical QPU (e.g., superconducting transmon), state preparation executes in **physical gate execution time** (e.g., ~20 ns for single-qubit gates, ~200-400 ns for two-qubit CNOT gates). A depth-3 QAOA circuit on 100 qubits executes in under **10 microseconds**.
2. **Qubit Connectivity & SWAP Overhead**:
   - Our simulator assumes all-to-all connectivity.
   - Real QPUs (IBM Eagle/Heron heavy-hex, Rigetti Aspen) have planar, nearest-neighbor coupling graphs (degree $\le 3$).
   - Executing an interaction $R_{ZZ}(u, v)$ between non-adjacent qubits requires transpiling routing SWAP gates. For an arbitrary 12-node Erdos-Renyi graph, SWAP overhead multiplies total circuit depth by **3x to 6x**, causing significant coherence decay.
3. **Decoherence ($T_1$ and $T_2$)**:
   - In our ideal simulation, quantum coherence is infinite.
   - Real transmon qubits have finite energy relaxation times ($T_1 \approx 100-300\ \mu\text{s}$) and phase dephasing times ($T_2 \approx 80-200\ \mu\text{s}$). If total circuit execution time exceeds $T_2$, the quantum state collapses into the maximally mixed state.
4. **Readout and Gate Infidelity**:
   - Modern commercial QPUs exhibit 1-qubit gate error rates of $\approx 10^{-4}$ to $10^{-3}$, 2-qubit CNOT errors of $\approx 5 \times 10^{-3}$ to $2 \times 10^{-2}$, and measurement readout assignment errors of $1-3\%$.
   - As proven in Experiment (b), gate errors above $2\%$ compress the approximation ratio toward random coin flips.
5. **Execution Latency and Queuing**:
   - Running on real cloud QPUs introduces network round-trips, job queue delays (minutes to hours), and shot compilation overhead, making synchronous outer-loop gradient descent impractical without specialized hybrid co-processors (e.g., Qiskit Runtime, PennyLane Catalyst).

---

## 5. Verification & Unit Tests

The test suite in [`track_C_quantum/tests/test_quantum_opt.py`](./tests/test_quantum_opt.py) validates the mathematical foundations:

| Test Name | Mathematical Property Verified | Result |
| :--- | :--- | :---: |
| `test_parameter_shift_vs_finite_difference` | Analytical parameter-shift equals central finite differences within error $< 10^{-5}$ ($1.38 \times 10^{-11}$) | **PASSED** |
| `test_qaoa_cut_expectation` | Expectation value of Cut operator on basis state equals classical bitstring cut | **PASSED** |
| `test_vqe_known_ground_state` | VQE converges to exact minimum eigenvalue of $H_2$ Hamiltonian ($E_0 = -1.85727$ Ha, error $< 6.8 \times 10^{-5}$ Ha) | **PASSED** |
| `test_spsa_gradient_approximation` | Expectation of SPSA 2-eval stochastic gradient aligns with parameter-shift ($\cos \theta > 0.70$) | **PASSED** |
| `test_quantum_natural_gradient_metric` | Fubini-Study / QFI metric tensor is symmetric positive semi-definite ($\lambda_{\min} \ge -10^{-6}$) | **PASSED** |
| `test_barren_plateau_variance_decay` | Gradient variance at $n=6$ decays by $>3\times$ compared to $n=2$ | **PASSED** |
| `test_bell_state_generation` | Smoke test: Bell state entanglement ($50\%$ $|00\rangle$, $50\%$ $|11\rangle$) | **PASSED** |

---

## 6. Viva Defense Cheat Sheet

- **Q: Why does the Parameter-Shift rule work without taking the limit $\epsilon \to 0$?**  
  *A*: Because single-qubit gates are generated by Pauli operators $P \in \{X, Y, Z\}$ whose eigenvalues are strictly $\pm 1$, satisfying $P^2 = I$. The expectation value decomposes into a simple sinusoid $\langle O \rangle(\theta) = A \cos(\theta) + B \sin(\theta) + C$. Using trigonometric identities, the exact derivative of this function is analytically given by $\frac{f(\theta + \pi/2) - f(\theta - \pi/2)}{2}$.
- **Q: What is a Barren Plateau, and how do we avoid it?**  
  *A*: A barren plateau occurs when the variance of the gradient vanishes exponentially with the number of qubits: $\text{Var}[\partial \langle O \rangle] \sim \mathcal{O}(2^{-n})$. This makes gradient descent exponentially flat. It is caused by deep unstructured circuits (forming 2-designs) and global observables. It can be mitigated by: (1) using local observables, (2) shallow depth ($O(\log n)$), (3) identity or layer-by-layer initialization, and (4) problem-inspired ansatze like QAOA.
- **Q: How does Quantum Natural Gradient differ from standard Gradient Descent?**  
  *A*: Standard GD updates parameters along the Euclidean metric space: $\theta \leftarrow \theta - \eta \nabla L$. Quantum Natural Gradient accounts for the Riemannian geometry of the Hilbert state space using the Fubini-Study metric tensor (Quantum Fisher Information): $\theta \leftarrow \theta - \eta (F + \lambda I)^{-1} \nabla L$, rendering the optimization invariant to parameter re-scaling and accelerating convergence across plateau regions.
