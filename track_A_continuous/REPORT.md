# Track A: Continuous Optimization — Report

## 1. Objective
Compare continuous optimization methods across convex and non-convex loss landscapes (e.g. standard convex quadratics/logistic loss vs saddle point/multi-modal objectives like Rastrigin/Rosenbrock or small neural networks).

## 2. Algorithms Tested
- **First-Order**: Gradient Descent (GD), SGD, Mini-batch SGD, Momentum, Nesterov Accelerated Gradient (NAG), AdaGrad, RMSProp, Adam.
- **Second-Order / Curvature**: Newton-Raphson, Gauss-Newton, curvature approximations (Hessian-vector products, Fisher information, diagonal approximations).
- **Core Mechanics**: Backpropagation (analyzed as reverse-mode automatic differentiation distinct from the optimizer update step).

## 3. Baseline
Standard vanilla Gradient Descent (GD) with constant learning rate on benchmark loss surfaces.

## 4. Fair Comparison Protocol
- Identical initial parameter starting points $\theta_0$.
- Identical gradient evaluation / sample budget.
- Identical numerical tolerances for convergence.

## 5. Experimental Results & Verification
*(To be populated following approved test runs)*

## 6. Trade-Off Analysis & 5-Line Critical Review
*(To be populated per Project Rules)*
