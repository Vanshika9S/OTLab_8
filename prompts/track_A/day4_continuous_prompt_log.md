# Prompt Log: Track A — Day 4 (Continuous Optimization)

## 1. Interaction Metadata
- **Date**: 2026-10-26
- **Tool / Assistant**: Gemini 3.8 Flash (High)
- **Track**: Track A (Continuous Optimization)
- **Milestone**: Day 4 — 10 Optimizers from scratch, Hand-Derived Backprop, Curvature Approximations (HVP, Fisher, Low-rank), 4 Landscapes, Step-Size Sweep, Quantum ML Notes.

---

## 2. Original User Prompt
```text
Day 4: Track A. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_A_continuous/.
Implement from scratch with NumPy: GD, SGD, mini-batch SGD, Momentum, NAG, AdaGrad, RMSProp, Adam, Newton, Gauss-Newton.
Also: backprop by hand for a small neural network (verified against finite-difference gradients), Hessian-vector products, Fisher and diagonal/low-rank curvature approximations.
Objectives: a convex quadratic, a strongly convex one, a non-convex function with a saddle and local minima, and a noisy objective. Show how each landscape changes the result and show local minima, global minima and saddle points on small examples. Include a small ML-as-optimization demo (loss plus regularization) and a discrete vs continuous contrast. Cover convergence behavior for convex, strongly convex and non-convex cases.
Report convergence plots, final loss, runtime, and sensitivity to step size (a sweep), with repeated runs for stochastic methods. Also include a short note on basic quantum computing concepts and the role of optimization in quantum ML (text only, no code).
Write pytest tests (gradient checks, known minima). Explain each update rule in plain words. Run DAILY CLOSE.
```

---

## 3. Implementation Summary
1. Implemented all 10 continuous optimizers in pure NumPy ([`track_A_continuous/code/optimizers.py`](../../track_A_continuous/code/optimizers.py)):
   - First-Order: `GradientDescent`, `SGD`, `MiniBatchSGD`, `Momentum`, `NAG`, `AdaGrad`, `RMSProp`, `Adam`.
   - Second-Order: `NewtonRaphson`, `GaussNewton`.
2. Hand-derived backpropagation for a 2-layer MLP in [`track_A_continuous/code/neural_net_backprop.py`](../../track_A_continuous/code/neural_net_backprop.py), verified against two-sided finite differences ($|g_{\text{analytic}} - g_{\text{numeric}}| = 2.14 \times 10^{-11}$).
3. Implemented Hessian-Vector Products (HVP) via directional finite differences, empirical Fisher Information Matrix (FIM), diagonal curvature, and truncated low-rank curvature.
4. Implemented 4 loss landscapes in [`track_A_continuous/code/landscapes.py`](../../track_A_continuous/code/landscapes.py):
   - Convex Quadratic ($\kappa = 20$).
   - Strongly Convex Quadratic ($\mu = 1.586, L = 4.414$).
   - Non-Convex Saddle Landscape with saddle point at $(0, 0)$ and symmetric minima at $(0, \pm \sqrt{5})$.
   - Noisy Objective with Gaussian gradient perturbation.
5. Implemented educational demos:
   - ML as Optimization: Ridge regression demonstrating eigenvalue shift $\lambda_{\text{min}}(H) \ge \lambda$.
   - Continuous vs Discrete: Polynomial gradient flow vs $2^d$ combinatorial curse of dimensionality.
6. Benchmarked all 10 algorithms in [`track_A_continuous/code/run_benchmarks.py`](../../track_A_continuous/code/run_benchmarks.py):
   - 10 repeated runs for stochastic methods (mean ± std).
   - Step-size sweep across $\eta \in [10^{-4}, 2.0]$.
   - Saved convergence curves and sensitivity plots in [`track_A_continuous/results/`](../../track_A_continuous/results/).
7. Wrote 5 unit tests in [`track_A_continuous/tests/test_continuous_optimizers.py`](../../track_A_continuous/tests/test_continuous_optimizers.py). All 5 pass.
8. Authored technical report [`track_A_continuous/REPORT.md`](../../track_A_continuous/REPORT.md) explaining all update rules and providing theoretical notes on Quantum ML.

---

## 4. Verification & Correctness Notes
- Hand-derived backprop matched numerical finite differences with $2.14 \times 10^{-11}$ error.
- Newton-Raphson reached exact quadratic minimum in 1 iteration.
- Demonstrates textbook saddle-point behavior: Newton gets trapped at $(0, 0)$ because $\nabla f = 0$, while gradient descent with perturbation escapes to global minima $f^* = -2.50$.
