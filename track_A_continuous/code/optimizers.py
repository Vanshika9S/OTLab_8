"""
optimizers.py
-------------
Pure NumPy Implementations of Core Continuous Optimization Algorithms.

First-Order Methods:
  1. GradientDescent (GD): Full-batch gradient descent.
  2. SGD: Single-sample stochastic gradient descent.
  3. MiniBatchSGD: Mini-batch stochastic gradient descent.
  4. Momentum: Polyak heavy-ball acceleration.
  5. NAG: Nesterov Accelerated Gradient.
  6. AdaGrad: Adaptive subgradient method (accumulated squared gradients).
  7. RMSProp: Root Mean Square Propagation (exponentially decaying squared gradients).
  8. Adam: Adaptive Moment Estimation (first and second biased-corrected moments).

Second-Order / Curvature Methods:
  9. NewtonRaphson: Exact second-order update with Hessian damping.
  10. GaussNewton: Non-linear least squares curvature approximation (J^T J).

Each optimizer is implemented cleanly with explicit update equations for viva explanation.
"""

import numpy as np
from typing import Callable, Tuple, List, Dict, Any, Optional


class GradientDescent:
    """
    Standard Full-Batch Gradient Descent.
    Update Rule:
        theta_{t+1} = theta_t - eta * grad(theta_t)
    """

    def __init__(self, lr: float = 0.01):
        self.lr = lr

    def reset(self):
        pass

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        return theta - self.lr * grad


class SGD:
    """
    Stochastic Gradient Descent (single sample / noisy gradient).
    Update Rule:
        theta_{t+1} = theta_t - eta * g_t
    """

    def __init__(self, lr: float = 0.01):
        self.lr = lr

    def reset(self):
        pass

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        return theta - self.lr * grad


class MiniBatchSGD:
    """
    Mini-Batch Stochastic Gradient Descent.
    Update Rule:
        theta_{t+1} = theta_t - eta * (1/|B| sum_{i in B} grad_i(theta_t))
    """

    def __init__(self, lr: float = 0.01):
        self.lr = lr

    def reset(self):
        pass

    def step(self, theta: np.ndarray, batch_grad: np.ndarray) -> np.ndarray:
        return theta - self.lr * batch_grad


class Momentum:
    """
    Polyak Heavy-Ball Momentum.
    Update Rule:
        v_{t+1} = beta * v_t + grad(theta_t)
        theta_{t+1} = theta_t - eta * v_{t+1}
    In plain words: Accumulates velocity in directions of consistent gradients,
    damping oscillations across steep ravines.
    """

    def __init__(self, lr: float = 0.01, beta: float = 0.9):
        self.lr = lr
        self.beta = beta
        self.v = None

    def reset(self):
        self.v = None

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        if self.v is None:
            self.v = np.zeros_like(theta)
        self.v = self.beta * self.v + grad
        return theta - self.lr * self.v


class NAG:
    """
    Nesterov Accelerated Gradient (NAG).
    Update Rule:
        theta_lookahead = theta_t - beta * v_t
        v_{t+1} = beta * v_t + eta * grad(theta_lookahead)
        theta_{t+1} = theta_t - v_{t+1}
    Equivalent form evaluated with current gradient:
        v_{t+1} = beta * v_t + grad(theta_t)
        theta_{t+1} = theta_t - eta * (grad(theta_t) + beta * v_{t+1})
    In plain words: Evaluates gradient at an anticipated future position,
    acting as an anticipatory braking mechanism.
    """

    def __init__(self, lr: float = 0.01, beta: float = 0.9):
        self.lr = lr
        self.beta = beta
        self.v = None

    def reset(self):
        self.v = None

    def step(self, theta: np.ndarray, grad_func: Callable[[np.ndarray], np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        if self.v is None:
            self.v = np.zeros_like(theta)
        # Lookahead evaluation point
        theta_ahead = theta - self.beta * self.v
        grad_ahead = grad_func(theta_ahead)
        self.v = self.beta * self.v + self.lr * grad_ahead
        new_theta = theta - self.v
        return new_theta, grad_ahead


class AdaGrad:
    """
    Adaptive Subgradient Method (AdaGrad).
    Update Rule:
        G_{t+1} = G_t + grad_t^2
        theta_{t+1} = theta_t - (eta / (sqrt(G_{t+1}) + eps)) * grad_t
    In plain words: Scales step size inversely with historical gradient magnitudes,
    giving larger updates to infrequent features and smaller updates to frequent ones.
    """

    def __init__(self, lr: float = 0.1, eps: float = 1e-8):
        self.lr = lr
        self.eps = eps
        self.G = None

    def reset(self):
        self.G = None

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        if self.G is None:
            self.G = np.zeros_like(theta)
        self.G += grad ** 2
        adjusted_grad = grad / (np.sqrt(self.G) + self.eps)
        return theta - self.lr * adjusted_grad


class RMSProp:
    """
    Root Mean Square Propagation (RMSProp).
    Update Rule:
        v_{t+1} = gamma * v_t + (1 - gamma) * grad_t^2
        theta_{t+1} = theta_t - (eta / (sqrt(v_{t+1}) + eps)) * grad_t
    In plain words: Replaces AdaGrad's monotonic sum with an exponentially decaying
    moving average, preventing the learning rate from vanishing prematurely.
    """

    def __init__(self, lr: float = 0.01, gamma: float = 0.9, eps: float = 1e-8):
        self.lr = lr
        self.gamma = gamma
        self.eps = eps
        self.v = None

    def reset(self):
        self.v = None

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        if self.v is None:
            self.v = np.zeros_like(theta)
        self.v = self.gamma * self.v + (1.0 - self.gamma) * (grad ** 2)
        adjusted_grad = grad / (np.sqrt(self.v) + self.eps)
        return theta - self.lr * adjusted_grad


class Adam:
    """
    Adaptive Moment Estimation (Adam).
    Update Rule:
        m_{t+1} = beta1 * m_t + (1 - beta1) * grad_t
        v_{t+1} = beta2 * v_t + (1 - beta2) * grad_t^2
        m_hat = m_{t+1} / (1 - beta1^{t+1})
        v_hat = v_{t+1} / (1 - beta2^{t+1})
        theta_{t+1} = theta_t - (eta / (sqrt(v_hat) + eps)) * m_hat
    In plain words: Combines momentum (first moment m) with RMSProp adaptive scaling
    (second moment v), with bias corrections for early initialization steps.
    """

    def __init__(self, lr: float = 0.01, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = None
        self.v = None
        self.t = 0

    def reset(self):
        self.m = None
        self.v = None
        self.t = 0

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        if self.m is None:
            self.m = np.zeros_like(theta)
            self.v = np.zeros_like(theta)
        self.t += 1

        self.m = self.beta1 * self.m + (1.0 - self.beta1) * grad
        self.v = self.beta2 * self.v + (1.0 - self.beta2) * (grad ** 2)

        # Bias correction
        m_hat = self.m / (1.0 - (self.beta1 ** self.t))
        v_hat = self.v / (1.0 - (self.beta2 ** self.t))

        return theta - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class NewtonRaphson:
    """
    Exact Second-Order Newton-Raphson Method.
    Update Rule:
        theta_{t+1} = theta_t - (H(theta_t) + lambda * I)^{-1} * grad(theta_t)
    In plain words: Fits a local quadratic Taylor model using the exact curvature (Hessian).
    Damping factor lambda ensures positive-definiteness when near saddle points or negative curvature.
    """

    def __init__(self, lr: float = 1.0, damping: float = 1e-4):
        self.lr = lr
        self.damping = damping

    def reset(self):
        pass

    def step(self, theta: np.ndarray, grad: np.ndarray, hessian: np.ndarray) -> np.ndarray:
        d = theta.shape[0]
        # Regularized Hessian inverse for numerical stability and saddle point escape
        H_reg = hessian + self.damping * np.eye(d)
        step_dir = np.linalg.solve(H_reg, grad)
        return theta - self.lr * step_dir


class GaussNewton:
    """
    Gauss-Newton Method for Non-Linear Least Squares:
        min_theta 0.5 * ||r(theta)||_2^2
    Where:
        grad = J^T * r
        Hessian approx = J^T * J
    Update Rule:
        theta_{t+1} = theta_t - (J^T * J + lambda * I)^{-1} * J^T * r
    In plain words: Approximates the true Hessian by neglecting higher-order residual
    curvatures sum r_i * H_{r_i}, guaranteeing a positive semi-definite curvature matrix.
    """

    def __init__(self, lr: float = 1.0, damping: float = 1e-4):
        self.lr = lr
        self.damping = damping

    def reset(self):
        pass

    def step(self, theta: np.ndarray, residuals: np.ndarray, jacobian: np.ndarray) -> np.ndarray:
        # Gradient = J^T * r
        grad = jacobian.T @ residuals
        # Gauss-Newton Hessian approximation = J^T * J
        d = theta.shape[0]
        H_gn = jacobian.T @ jacobian + self.damping * np.eye(d)
        step_dir = np.linalg.solve(H_gn, grad)
        return theta - self.lr * step_dir
