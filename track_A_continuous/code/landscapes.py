"""
landscapes.py
-------------
Objective Functions, Loss Landscapes, and Educational Demos for Track A.

Includes:
  1. ConvexQuadratic: Convex, ill-conditioned quadratic (elliptical contours).
  2. StronglyConvexQuadratic: Strictly positive-definite Hessian (mu > 0), unique global minimum.
  3. NonConvexSaddle: Multi-modal double-well potential with an exact saddle point at (0, 0)
     and two symmetric global minima at (0, +/- sqrt(5)).
  4. NoisyObjective: Stochastic gradient perturbation modeling noisy mini-batch observations.
  5. MLOptimizationDemo: Ridge regression (Loss + L2 Regularization), showing how lambda
     alleviates ill-conditioning.
  6. ContinuousVsDiscreteDemo: Contrasting polynomial gradient flow against exponential combinatorial search.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional


class ConvexQuadratic:
    """
    Convex Quadratic: f(x) = 0.5 * x^T A x - b^T x
    A = [[1.0, 0.0], [0.0, 0.05]] -> Condition number kappa = 20.
    Minimum at x* = [1.0, 1.0], f(x*) = -0.525.
    """

    def __init__(self):
        self.A = np.array([[1.0, 0.0], [0.0, 0.05]])
        self.b = np.array([1.0, 0.05])
        self.x_star = np.array([1.0, 1.0])
        self.f_star = -0.525

    def f(self, x: np.ndarray) -> float:
        return float(0.5 * x.T @ self.A @ x - self.b.T @ x)

    def grad(self, x: np.ndarray) -> np.ndarray:
        return self.A @ x - self.b

    def hessian(self, x: np.ndarray) -> np.ndarray:
        return self.A.copy()


class StronglyConvexQuadratic:
    """
    Strongly Convex Quadratic: f(x) = 0.5 * x^T A x - b^T x
    A = [[4.0, 1.0], [1.0, 2.0]], b = [1.0, 2.0].
    Eigenvalues: mu ~ 1.586, L ~ 4.414.
    Unique global minimum at x* = [0.0, 1.0], f(x*) = -1.0.
    """

    def __init__(self):
        self.A = np.array([[4.0, 1.0], [1.0, 2.0]])
        self.b = np.array([1.0, 2.0])
        self.x_star = np.array([0.0, 1.0])
        self.f_star = -1.0
        evals = np.linalg.eigvalsh(self.A)
        self.mu = float(np.min(evals))
        self.L = float(np.max(evals))

    def f(self, x: np.ndarray) -> float:
        return float(0.5 * x.T @ self.A @ x - self.b.T @ x)

    def grad(self, x: np.ndarray) -> np.ndarray:
        return self.A @ x - self.b

    def hessian(self, x: np.ndarray) -> np.ndarray:
        return self.A.copy()


class NonConvexSaddle:
    """
    Non-Convex Landscape with a Saddle Point and Local/Global Minima:
      f(x, y) = x^2 - y^2 + 0.1 * y^4 + 0.05 * x^4

    Stationary Points:
      1. Saddle Point at (0, 0):
         grad = [0, 0]
         Hessian = [[2.0, 0.0], [0.0, -2.0]] -> Evals: +2.0 (convex in x), -2.0 (concave in y).
         f(0, 0) = 0.0
      2. Two Symmetric Global Minima at (0, sqrt(5)) and (0, -sqrt(5)) ~ (0, +/- 2.236):
         grad = [0, 0]
         Hessian = [[2.0, 0.0], [0.0, 4.0]] -> Both evals positive.
         f(0, +/- 2.236) = -2.5
    """

    def __init__(self):
        self.saddle_point = np.array([0.0, 0.0])
        self.minima = [np.array([0.0, np.sqrt(5.0)]), np.array([0.0, -np.sqrt(5.0)])]
        self.f_star = -2.5

    def f(self, x: np.ndarray) -> float:
        px, py = x[0], x[1]
        return float(px ** 2 - py ** 2 + 0.1 * (py ** 4) + 0.05 * (px ** 4))

    def grad(self, x: np.ndarray) -> np.ndarray:
        px, py = x[0], x[1]
        gx = 2.0 * px + 0.2 * (px ** 3)
        gy = -2.0 * py + 0.4 * (py ** 3)
        return np.array([gx, gy])

    def hessian(self, x: np.ndarray) -> np.ndarray:
        px, py = x[0], x[1]
        hxx = 2.0 + 0.6 * (px ** 2)
        hyy = -2.0 + 1.2 * (py ** 2)
        return np.array([[hxx, 0.0], [0.0, hyy]])


class NoisyObjective:
    """
    Wraps any base objective function with additive Gaussian gradient noise:
      g_noisy(x) = grad(x) + N(0, sigma^2 * I)
    Models stochastic gradient mini-batch sampling.
    """

    def __init__(self, base_obj: Any, sigma: float = 0.2, seed: int = 42):
        self.base_obj = base_obj
        self.sigma = sigma
        self.rng = np.random.RandomState(seed)

    def set_seed(self, seed: int):
        self.rng = np.random.RandomState(seed)

    def f(self, x: np.ndarray) -> float:
        return self.base_obj.f(x)

    def grad(self, x: np.ndarray) -> np.ndarray:
        true_grad = self.base_obj.grad(x)
        noise = self.rng.randn(*true_grad.shape) * self.sigma
        return true_grad + noise

    def hessian(self, x: np.ndarray) -> np.ndarray:
        return self.base_obj.hessian(x)


# ---------------------------------------------------------------------
# Educational Demonstrations
# ---------------------------------------------------------------------
def ml_optimization_demo(
    N: int = 100, d: int = 5, lambda_reg: float = 0.1, seed: int = 42
) -> Dict[str, Any]:
    """
    Machine Learning as Optimization Demo:
      Loss + L2 Regularization (Ridge Regression):
        L(theta) = (1 / 2N) * ||X @ theta - y||_2^2 + (lambda / 2) * ||theta||_2^2

    Shows that adding L2 regularization strictly shifts the Hessian eigenvalues:
      H = (1 / N) * X^T X + lambda * I
      lambda_min(H) >= lambda > 0
    guaranteeing strong convexity even if the empirical covariance X^T X is rank-deficient.
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(N, d)
    true_theta = rng.randn(d)
    y = X @ true_theta + rng.randn(N) * 0.1

    # Unregularized Hessian
    H_unreg = (1.0 / N) * (X.T @ X)
    evals_unreg = np.linalg.eigvalsh(H_unreg)

    # Regularized Hessian
    H_reg = H_unreg + lambda_reg * np.eye(d)
    evals_reg = np.linalg.eigvalsh(H_reg)

    # Condition numbers
    cond_unreg = np.max(evals_unreg) / (np.min(evals_unreg) + 1e-12)
    cond_reg = np.max(evals_reg) / np.min(evals_reg)

    return {
        "N": N,
        "d": d,
        "lambda_reg": lambda_reg,
        "min_eval_unreg": float(np.min(evals_unreg)),
        "min_eval_reg": float(np.min(evals_reg)),
        "cond_unreg": float(cond_unreg),
        "cond_reg": float(cond_reg),
        "strong_convexity_guarantee": f"mu >= {lambda_reg}",
    }


def continuous_vs_discrete_demo() -> Dict[str, Any]:
    """
    Contrasting Continuous vs Discrete Optimization:
      Continuous:
        - Smooth gradient flow theta <- theta - eta * grad(theta).
        - Local gradient points downhill; polynomial-time convergence.
      Discrete (0-1 Combinatorial Selection):
        - Variables x in {0, 1}^d.
        - No gradient exists; landscape consists of isolated combinatorial points.
        - Brute-force exhaustive search requires 2^d evaluations.
    """
    d_values = [4, 8, 16, 32, 64]
    discrete_evaluations = [2 ** d for d in d_values]
    continuous_iterations = [100 for _ in d_values]  # Typical GD convergence iterations

    return {
        "d_values": d_values,
        "discrete_state_spaces": [f"2^{d} = {2**d:,}" if d <= 16 else f"2^{d} (~{2**d:.2e})" for d in d_values],
        "continuous_gradient_steps": continuous_iterations,
        "takeaway": "Continuous optimization utilizes first- and second-order curvature vectors to navigate polynomial paths, whereas discrete combinatorial optimization faces exponential 2^d state explosion without structural relaxations.",
    }
