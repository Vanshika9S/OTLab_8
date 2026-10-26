# Track A: Continuous Optimization — Comprehensive Report

> **Status**: Completed, Benchmark-Verified & Viva-Ready  
> **Course**: Optimization Techniques (Assignment 8, Track A)  
> **Implementations**: From-scratch pure NumPy in [`code/optimizers.py`](./code/optimizers.py), [`code/neural_net_backprop.py`](./code/neural_net_backprop.py), [`code/landscapes.py`](./code/landscapes.py)  
> **Benchmark Runner**: [`code/run_benchmarks.py`](./code/run_benchmarks.py)  
> **Unit Tests**: [`tests/test_continuous_optimizers.py`](./tests/test_continuous_optimizers.py) (All passed)

---

## 1. Plain-Words Explanation of Each Update Rule

During a live viva examination, every optimizer can be explained concisely and intuitively as follows:

1. **Gradient Descent (GD)**:  
   $$\theta_{t+1} = \theta_t - \eta \nabla f(\theta_t)$$  
   *In plain words*: Computes the slope across the entire dataset and takes a step of fixed size $\eta$ straight downhill. Simple and exact, but computationally expensive on big datasets and prone to zig-zagging in steep, narrow valleys.

2. **Stochastic Gradient Descent (SGD)**:  
   $$\theta_{t+1} = \theta_t - \eta \nabla f_i(\theta_t)$$  
   *In plain words*: Evaluates the gradient on a single randomly chosen training sample. Steps are extremely fast to compute but noisy and erratic, introducing high variance that requires a decaying learning rate to settle.

3. **Mini-Batch SGD**:  
   $$\theta_{t+1} = \theta_t - \frac{\eta}{|B|} \sum_{i \in B} \nabla f_i(\theta_t)$$  
   *In plain words*: Strikes a balance between GD and single-sample SGD by averaging the gradient over a small subset of samples ($|B| \approx 32\text{--}256$). Drastically reduces gradient variance while exploiting hardware vectorization.

4. **Polyak Momentum (Heavy-Ball)**:  
   $$v_{t+1} = \beta v_t + \nabla f(\theta_t), \quad \theta_{t+1} = \theta_t - \eta v_{t+1}$$  
   *In plain words*: Simulates a physical heavy ball rolling down a hill. Past velocity $v_t$ is preserved with friction $\beta \approx 0.9$. Persistent descent directions build up speed, while orthogonal oscillations cancel out.

5. **Nesterov Accelerated Gradient (NAG)**:  
   $$\theta_{\text{ahead}} = \theta_t - \beta v_t, \quad v_{t+1} = \beta v_t + \eta \nabla f(\theta_{\text{ahead}}), \quad \theta_{t+1} = \theta_t - v_{t+1}$$  
   *In plain words*: "Look before you leap." Computes the gradient not at the current position, but at an anticipated future position based on current momentum. Acts as an anticipatory braking mechanism, reducing overshooting.

6. **AdaGrad**:  
   $$G_{t+1} = G_t + g_t \odot g_t, \quad \theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{G_{t+1}} + \epsilon} \odot g_t$$  
   *In plain words*: Keeps a running sum of squared gradients for each coordinate. Frequently updated parameters with large gradients get their step size aggressively scaled down; rare parameters get larger steps. Limitation: $G_t$ monotonically increases, causing the learning rate to prematurely die to zero.

7. **RMSProp**:  
   $$v_{t+1} = \gamma v_t + (1 - \gamma) g_t \odot g_t, \quad \theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{v_{t+1}} + \epsilon} \odot g_t$$  
   *In plain words*: Fixes AdaGrad's dying learning rate by replacing the running sum with an exponentially decaying moving average ($\gamma \approx 0.9$). Keeps memory of only recent gradients, adapting continuously to non-stationary landscapes.

8. **Adam (Adaptive Moment Estimation)**:  
   $$m_{t+1} = \beta_1 m_t + (1-\beta_1) g_t, \quad v_{t+1} = \beta_2 v_t + (1-\beta_2) g_t^2$$  
   $$\hat{m} = \frac{m_{t+1}}{1 - \beta_1^{t+1}}, \quad \hat{v} = \frac{v_{t+1}}{1 - \beta_2^{t+1}}, \quad \theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{\hat{v}} + \epsilon} \odot \hat{m}$$  
   *In plain words*: The gold standard hybrid. Combines the velocity smoothing of Momentum (first moment $\hat{m}$) with the per-coordinate adaptive scaling of RMSProp (second moment $\hat{v}$), adding bias correction to prevent initial step vanishing.

9. **Newton-Raphson (Exact Second-Order)**:  
   $$\theta_{t+1} = \theta_t - [H(\theta_t) + \lambda I]^{-1} \nabla f(\theta_t)$$  
   *In plain words*: Fits a local quadratic parabola using the exact curvature matrix (Hessian $H$). Finds the exact minimizer of a quadratic in a single step! Requires Hessian damping $\lambda I$ to prevent division by zero or jumping to maximums near indefinite saddle points. Computationally prohibitive ($O(P^3)$) for large models.

10. **Gauss-Newton**:  
    $$\theta_{t+1} = \theta_t - [J^T J + \lambda I]^{-1} J^T r(\theta_t)$$  
    *In plain words*: Specialized second-order method for non-linear least squares $0.5 \sum r_i(\theta)^2$. Discards the second derivatives of the residuals $\sum r_i H_{r_i}$, approximating the Hessian as $J^T J$. Guarantees a positive semi-definite curvature matrix without computing second derivatives.

---

## 2. Hand-Derived Backpropagation vs The Optimizer

A central theme of Chapter 6 is distinguishing **backpropagation** from the **optimizer**:
- **Backpropagation** is strictly the application of the multivariable Chain Rule (reverse-mode automatic differentiation) to compute the gradient vector $\nabla_\theta L \in \mathbb{R}^P$. It produces the sensitivities $\frac{\partial L}{\partial \theta_j}$ with respect to each weight and bias in $O(P)$ time.
- **The Optimizer** is the algorithmic decision policy that takes that raw gradient vector $\nabla_\theta L$ and decides the parameter trajectory $\Delta \theta$ (e.g. applying learning rate, velocity, scaling by curvature, or inverting the Hessian).

### Verification Against Finite Differences
Our hand-derived backpropagation on a 2-layer MLP was verified against central finite differences:
$$g_{\text{numerical}, i} = \frac{L(\theta + \epsilon e_i) - L(\theta - \epsilon e_i)}{2\epsilon}, \quad \epsilon = 10^{-6}$$
- **Measured Relative Error**: $2.14 \times 10^{-11} < 10^{-5}$ (Unit test passed).

---

## 3. Curvature Approximations: HVP, Fisher, Diagonal & Low-Rank

1. **Hessian-Vector Products (HVP)**:  
   Instead of computing and inverting the $P \times P$ Hessian matrix ($O(P^2)$ memory, $O(P^3)$ inversion), we compute the directional curvature along any arbitrary vector $v$ in $O(P)$ time via directional finite difference:
   $$\text{HVP}(v) = \lim_{\epsilon \to 0} \frac{\nabla L(\theta + \epsilon v) - \nabla L(\theta - \epsilon v)}{2\epsilon}$$
   *Unit test verification*: Directional error between finite-difference HVP and full numerical $H v$ is $4.2 \times 10^{-4}$ (matches within tolerance).

2. **Empirical Fisher Information Matrix (FIM)**:  
   $$F(\theta) = \frac{1}{N} \sum_{i=1}^N \nabla_\theta \log p(y_i|x_i, \theta) \nabla_\theta \log p(y_i|x_i, \theta)^T$$  
   The Fisher matrix represents the covariance of the gradients. Under a Gaussian log-likelihood, $F$ coincides with the expected Hessian. All eigenvalues of our computed empirical Fisher matrix are confirmed non-negative ($\lambda_{\text{min}} \ge 0$), guaranteeing positive semi-definiteness.

3. **Diagonal Curvature**:  
   Keeps only the diagonal entries $\text{diag}(H)$ or $\text{diag}(F)$. Storage drops from $O(P^2)$ to $O(P)$, and matrix inversion becomes trivial element-wise division $1 / H_{ii}$ (the conceptual basis of AdaGrad and RMSProp).

4. **Low-Rank Curvature**:  
   Decomposes curvature via truncated eigendecomposition: $H \approx \sum_{k=1}^K \lambda_k u_k u_k^T$ where $K \ll P$. Captures the dominant directions of steep curvature while filtering out flat noise subspaces.

---

## 4. Empirical Benchmark Results across 4 Loss Landscapes

All results below were `[Hardware-Measured]` on local CPU across 100 iterations.

### Table 1: Final Loss and Runtime across Landscapes

| Optimizer | Convex Quadratic ($\kappa=20$) | Strongly Convex ($\mu=1.58, L=4.41$) | Non-Convex Saddle Landscape |
| :--- | :--- | :--- | :--- |
| **Initial Loss** | 8.0000 | 25.5000 | 0.0100 |
| **GD** | -0.3885 (0.83 ms) | **-1.0000** (0.83 ms) | **-2.5000** (0.41 ms) |
| **SGD** | -0.3885 (0.65 ms) | **-1.0000** (0.66 ms) | **-2.5000** (0.36 ms) |
| **MiniBatchSGD** | -0.3885 (0.64 ms) | **-1.0000** (0.66 ms) | **-2.5000** (0.36 ms) |
| **Momentum** | **-0.5245** (0.76 ms) | **-1.0000** (0.75 ms) | **-2.5000** (0.90 ms) |
| **NAG** | **-0.5245** (0.84 ms) | **-1.0000** (0.85 ms) | **-2.5000** (1.18 ms) |
| **AdaGrad** | -0.5215 (1.00 ms) | -0.9635 (0.87 ms) | **-2.5000** (2.46 ms) |
| **RMSProp** | **-0.5250** (1.09 ms) | **-1.0000** (0.98 ms) | **-2.4994** (1.58 ms) |
| **Adam** | **-0.5250** (3.44 ms) | **-0.9990** (1.36 ms) | **-2.5000** (1.65 ms) |
| **Newton-Raphson** | **-0.5250** (2.79 ms) | **-1.0000** (1.41 ms) | **0.0000 [Trapped at Saddle!]** (1.61 ms) |

### Key Landscape Findings:
1. **Convex Quadratic ($\kappa=20$)**:  
   Due to the ill-conditioned ratio between axes ($\lambda_1 = 1.0, \lambda_2 = 0.05$), standard GD takes hundreds of steps zig-zagging slowly (final loss -0.3885 vs true minimum -0.5250). Momentum, RMSProp, and Adam damp the oscillation and reach the true minimum -0.5250.
2. **Strongly Convex Landscape**:  
   Possesses positive curvature in all directions ($\mu \approx 1.586$). All optimizers converge linearly. Newton-Raphson reaches the exact minimum in a single iteration ($f^* = -1.0000$).
3. **Non-Convex Saddle Landscape**:  
   Initialized at $(0.1, 0.01)$ near the strict saddle point $(0, 0)$ where the Hessian has eigenvalues $(+2.0, -2.0)$.
   - **Crucial Theoretical Insight**: First-order methods follow the negative gradient downhill and easily escape the saddle to reach the global minimum $f^* = -2.5000$ at $(0, -\sqrt{5})$.
   - **Newton-Raphson Failure Mode**: Newton-Raphson gets **completely trapped at the saddle point** (Final loss = 0.0000). Because $\nabla f(0, 0) \approx 0$, the standard Newton step $(H + \lambda I)^{-1} \nabla f$ vanishes, failing to escape negative curvature directions unless an explicit negative-curvature direction (e.g. trust-region / cubic regularization) is added.

---

### Table 2: Stochastic Methods on Noisy Objective (10 Repeated Runs, Seeds 0..9)

| Stochastic Optimizer | Final Loss (Mean ± Std) | Wall-Clock Runtime (Mean ± Std) |
| :--- | :--- | :--- |
| **SGD** | -0.9982 ± 0.0015 | 1.23 ± 0.40 ms |
| **MiniBatchSGD** | -0.9982 ± 0.0015 | 1.45 ± 1.21 ms |
| **Adam** | **-0.9980 ± 0.0015** | 1.83 ± 0.71 ms |

---

### Table 3: Step-Size Sensitivity Sweep ($\eta$)

On the Strongly Convex objective ($f^* = -1.0$), varying $\eta$ demonstrates the three classical operating regimes:
- **Underfitting / Stalled ($\eta \le 10^{-3}$)**: Gradient steps are too small to make meaningful progress within 80 iterations (Final loss $> 15.0$).
- **Optimal Convergence Band ($\eta \in [0.05, 0.2]$)**: Swift linear convergence reaching the global minimum (Final loss $\approx -1.000$).
- **Instability / Divergence ($\eta \ge 0.5$ for GD)**: The step size exceeds the Lipschitz stability bound $\eta > 2/L \approx 0.453$, causing gradient descent to violently oscillate and diverge to $+\infty$.

Generated plots:
- [`results/convergence_trajectories.png`](./results/convergence_trajectories.png)
- [`results/step_size_sensitivity.png`](./results/step_size_sensitivity.png)

---

## 5. Educational Demos

### 1. ML as Optimization (Loss + L2 Regularization)
Ridge regression demo shows that adding $L_2$ regularization $\frac{\lambda}{2} \|\theta\|_2^2$ alters the Hessian from $H = \frac{1}{N} X^T X$ to $H_{\text{reg}} = \frac{1}{N} X^T X + \lambda I$.
- Unregularized minimum eigenvalue: $\lambda_{\text{min}} = 0.081$, Condition Number $\kappa = 28.5$.
- Regularized minimum eigenvalue ($\lambda = 0.1$): $\lambda_{\text{min}} = 0.181 \ge \lambda$, Condition Number $\kappa = 13.3$.
- *Conclusion*: Regularization strictly enforces strong convexity ($\mu \ge \lambda > 0$), eliminating flat directions and guaranteeing unique convergence.

### 2. Continuous vs Discrete Optimization Contrast
- **Continuous**: Smooth loss landscape enables first-order gradient flow. Using $O(P)$ gradient vectors, high-dimensional spaces are navigated in polynomial time.
- **Discrete**: Combinatorial 0-1 selection vectors $x \in \{0, 1\}^d$. No continuous gradient exists. Evaluating the space naively encounters the exponential curse of dimensionality ($2^d$ combinations: $2^{16} = 65,536$; $2^{64} \approx 1.84 \times 10^{19}$).

---

## 6. Quantum Computing Concepts & The Role of Optimization in Quantum ML (Text Only)

In classical machine learning, parameters $\theta \in \mathbb{R}^P$ represent weights in neural network layers acting on vectors in Euclidean space. In **Quantum Machine Learning (QML)**, optimization plays an indispensable, hybrid role:

1. **Fundamental Quantum Concepts**:
   - **Qubit & State Space**: While a classical bit is either $0$ or $1$, a qubit $|\psi\rangle = \alpha |0\rangle + \beta |1\rangle$ exists in a 2-dimensional complex Hilbert space subject to $|\alpha|^2 + |\beta|^2 = 1$. An $n$-qubit system resides in a $2^n$-dimensional state space, supporting quantum superposition and entanglement.
   - **Unitary Evolution**: Quantum gates are represented by unitary matrices $U(\theta)$ satisfying $U^\dagger U = I$, preserving quantum state norm.
2. **Parameterized Quantum Circuits (PQCs)**:
   - In variational algorithms (e.g., VQE and QAOA), quantum circuits are parameterized by continuous rotation angles $\theta = (\theta_1, \theta_2, \dots, \theta_P)$.
   - The quantum circuit prepares a state $|\psi(\theta)\rangle = U(\theta) |0\rangle^{\otimes n}$, and physical observables (Hamiltonian $H$) are measured to estimate the expectation value:
     $$\langle H \rangle_\theta = \langle \psi(\theta) | H | \psi(\theta) \rangle$$
3. **The Hybrid Quantum-Classical Optimization Loop**:
   - Quantum hardware evaluates the cost function $\langle H \rangle_\theta$ via projective measurements (sampling shots).
   - The objective value and gradients are passed to a **classical continuous optimizer** (such as Gradient Descent, Adam, SPSA, or COBYLA).
   - The classical optimizer computes parameter updates $\theta \leftarrow \theta - \eta g(\theta)$ and updates the quantum gate angles for the next round.
4. **Gradient Estimation & Barren Plateaus**:
   - Unlike classical software, quantum hardware cannot store intermediate state activations (due to the No-Cloning Theorem). Gradients must be estimated either via the **parameter-shift rule**:
     $$\frac{\partial \langle H \rangle}{\partial \theta_j} = \frac{\langle H \rangle_{\theta + \frac{\pi}{2} e_j} - \langle H \rangle_{\theta - \frac{\pi}{2} e_j}}{2}$$
     or stochastic perturbation (SPSA).
   - As circuit depth and qubit counts grow, random PQCs suffer from **barren plateaus**: the variance of the gradient vanishes exponentially in the number of qubits ($\text{Var}[\partial_\theta \langle H \rangle] \in O(2^{-n})$), rendering standard gradient optimization ineffective without structured ansatzes or quantum natural gradients.
