"""
neural_net_backprop.py
----------------------
Hand-Derived Backpropagation & Curvature Approximations in Pure NumPy.

Covers:
  1. Hand-Derived Analytical Backpropagation for a 2-Layer Neural Network.
     Emphasizes the fundamental distinction:
       - Backpropagation is purely the gradient evaluation mechanism (Reverse-mode AD / Chain Rule).
       - Optimizers (GD, Adam, Newton) determine the parameter update trajectory using those gradients.
  2. Numerical Finite-Difference Gradient Checking (|g_analytical - g_numerical| < 1e-6).
  3. Hessian-Vector Products (HVP): Directional curvature without forming the O(P^2) Hessian.
  4. Empirical Fisher Information Matrix (FIM).
  5. Diagonal and Low-Rank Curvature Approximations.
"""

import numpy as np
from typing import Dict, Tuple, List, Any


class SmallMLP:
    """
    Two-Layer Multilayer Perceptron:
      Input (d_in) -> Linear -> Tanh -> Linear -> Output (d_out)
    """

    def __init__(self, d_in: int = 2, d_hidden: int = 4, d_out: int = 1, seed: int = 42):
        rng = np.random.RandomState(seed)
        # Xavier / Glorot Initialization
        self.W1 = rng.randn(d_in, d_hidden) * np.sqrt(2.0 / (d_in + d_hidden))
        self.b1 = np.zeros(d_hidden)
        self.W2 = rng.randn(d_hidden, d_out) * np.sqrt(2.0 / (d_hidden + d_out))
        self.b2 = np.zeros(d_out)

    def get_params_flat(self) -> np.ndarray:
        return np.concatenate([
            self.W1.ravel(),
            self.b1.ravel(),
            self.W2.ravel(),
            self.b2.ravel(),
        ])

    def set_params_flat(self, theta: np.ndarray) -> None:
        idx = 0
        w1_size = self.W1.size
        self.W1 = theta[idx : idx + w1_size].reshape(self.W1.shape)
        idx += w1_size

        b1_size = self.b1.size
        self.b1 = theta[idx : idx + b1_size].reshape(self.b1.shape)
        idx += b1_size

        w2_size = self.W2.size
        self.W2 = theta[idx : idx + w2_size].reshape(self.W2.shape)
        idx += w2_size

        b2_size = self.b2.size
        self.b2 = theta[idx : idx + b2_size].reshape(self.b2.shape)

    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Forward Pass:
          z1 = X @ W1 + b1
          a1 = tanh(z1)
          z2 = a1 @ W2 + b2
          y_hat = z2
        """
        z1 = X @ self.W1 + self.b1
        a1 = np.tanh(z1)
        z2 = a1 @ self.W2 + self.b2
        cache = {"X": X, "z1": z1, "a1": a1, "z2": z2}
        return z2, cache

    def loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """Mean Squared Error Loss: L = (1 / 2N) * sum ||y_hat - y||^2"""
        y_hat, _ = self.forward(X)
        N = X.shape[0]
        return 0.5 * np.mean((y_hat - y) ** 2)

    def backward(self, y: np.ndarray, cache: Dict[str, np.ndarray]) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """
        Hand-Derived Backpropagation (Analytical Chain Rule):
          dL/dz2 = (y_hat - y) / N
          dL/dW2 = a1^T @ (dL/dz2)
          dL/db2 = sum(dL/dz2, axis=0)
          dL/da1 = (dL/dz2) @ W2^T
          dL/dz1 = dL/da1 * (1 - a1^2)  [derivative of tanh]
          dL/dW1 = X^T @ (dL/dz1)
          dL/db1 = sum(dL/dz1, axis=0)
        """
        X = cache["X"]
        a1 = cache["a1"]
        z2 = cache["z2"]
        N = X.shape[0]

        delta2 = (z2 - y) / N  # shape (N, d_out)
        dW2 = a1.T @ delta2
        db2 = np.sum(delta2, axis=0)

        delta1 = (delta2 @ self.W2.T) * (1.0 - a1 ** 2)  # shape (N, d_hidden)
        dW1 = X.T @ delta1
        db1 = np.sum(delta1, axis=0)

        grads = {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}
        grad_flat = np.concatenate([
            dW1.ravel(),
            db1.ravel(),
            dW2.ravel(),
            db2.ravel(),
        ])
        return grads, grad_flat

    def compute_gradient(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Helper to get flat gradient vector."""
        _, cache = self.forward(X)
        _, grad_flat = self.backward(y, cache)
        return grad_flat


# ---------------------------------------------------------------------
# Finite-Difference Gradient Checking
# ---------------------------------------------------------------------
def numerical_gradient(mlp: SmallMLP, X: np.ndarray, y: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """
    Two-Sided Central Finite-Difference Gradient:
      g_i = [L(theta + eps * e_i) - L(theta - eps * e_i)] / (2 * eps)
    """
    theta = mlp.get_params_flat()
    grad_num = np.zeros_like(theta)

    for i in range(len(theta)):
        theta_plus = theta.copy()
        theta_plus[i] += eps
        mlp.set_params_flat(theta_plus)
        loss_plus = mlp.loss(X, y)

        theta_minus = theta.copy()
        theta_minus[i] -= eps
        mlp.set_params_flat(theta_minus)
        loss_minus = mlp.loss(X, y)

        grad_num[i] = (loss_plus - loss_minus) / (2.0 * eps)

    mlp.set_params_flat(theta)  # Restore original weights
    return grad_num


def verify_gradient(mlp: SmallMLP, X: np.ndarray, y: np.ndarray, tol: float = 1e-5) -> Tuple[bool, float]:
    """
    Computes relative error: ||g_analytic - g_numeric|| / (||g_analytic|| + ||g_numeric||)
    """
    g_analytic = mlp.compute_gradient(X, y)
    g_numeric = numerical_gradient(mlp, X, y)
    norm_diff = np.linalg.norm(g_analytic - g_numeric)
    norm_sum = np.linalg.norm(g_analytic) + np.linalg.norm(g_numeric) + 1e-12
    rel_error = norm_diff / norm_sum
    is_valid = rel_error < tol
    return is_valid, float(rel_error)


# ---------------------------------------------------------------------
# Curvature Approximations: HVP, Fisher, Diagonal, Low-Rank
# ---------------------------------------------------------------------
def hessian_vector_product(
    mlp: SmallMLP, X: np.ndarray, y: np.ndarray, v: np.ndarray, eps: float = 1e-5
) -> np.ndarray:
    """
    Hessian-Vector Product (HVP) via Finite-Difference of Gradients:
      H * v = [grad(theta + eps * v) - grad(theta - eps * v)] / (2 * eps)
    Computes directional curvature in O(P) time without materializing the P x P Hessian.
    """
    theta = mlp.get_params_flat()

    mlp.set_params_flat(theta + eps * v)
    grad_plus = mlp.compute_gradient(X, y)

    mlp.set_params_flat(theta - eps * v)
    grad_minus = mlp.compute_gradient(X, y)

    mlp.set_params_flat(theta)
    return (grad_plus - grad_minus) / (2.0 * eps)


def full_hessian_numerical(mlp: SmallMLP, X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Constructs full P x P numerical Hessian column by column using standard basis HVPs."""
    theta = mlp.get_params_flat()
    P = len(theta)
    H = np.zeros((P, P))
    for i in range(P):
        e_i = np.zeros(P)
        e_i[i] = 1.0
        H[:, i] = hessian_vector_product(mlp, X, y, e_i)
    return 0.5 * (H + H.T)  # Ensure exact symmetry


def empirical_fisher_matrix(mlp: SmallMLP, X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Empirical Fisher Information Matrix (FIM):
      F = (1 / N) * sum_{i=1}^N (grad_i)(grad_i)^T
    Under Gaussian log-likelihood, F approximates the expected Hessian of the loss.
    """
    N = X.shape[0]
    theta = mlp.get_params_flat()
    P = len(theta)
    F = np.zeros((P, P))

    for i in range(N):
        x_single = X[i : i + 1]
        y_single = y[i : i + 1]
        g_i = mlp.compute_gradient(x_single, y_single)
        F += np.outer(g_i, g_i)

    return F / N


def diagonal_curvature_approximation(matrix: np.ndarray) -> np.ndarray:
    """
    Diagonal Curvature: Keeps only diagonal elements (diag(H) or diag(F)).
    Enables O(P) storage and trivial O(P) matrix inversion.
    """
    return np.diag(np.diag(matrix))


def low_rank_curvature_approximation(matrix: np.ndarray, k: int = 3) -> np.ndarray:
    """
    Low-Rank Curvature Approximation via Truncated Eigen-Decomposition:
      H_k = sum_{i=1}^k lambda_i * u_i * u_i^T
    Captures the k principal directions of highest curvature while filtering flat subspaces.
    """
    evals, evecs = np.linalg.eigh(matrix)
    # Sort in descending order
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]

    k = min(k, len(evals))
    H_k = np.zeros_like(matrix)
    for i in range(k):
        if evals[i] > 1e-10:
            u_i = evecs[:, i : i + 1]
            H_k += evals[i] * (u_i @ u_i.T)

    return H_k
