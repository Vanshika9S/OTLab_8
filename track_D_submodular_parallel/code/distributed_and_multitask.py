"""
distributed_and_multitask.py
----------------------------
Distributed Optimization (Federated Learning / FedAvg) and Multi-Task Optimization (MGDA & GradNorm).

Mathematical Formulations:
  1. Federated Averaging (FedAvg, McMahan et al. 2017):
     Dataset partitioned across K clients: D = bigcup_{k=1}^K D_k with non-IID distributions.
     Global Objective: min_w F(w) = sum_{k=1}^K (n_k / n) F_k(w)
     In communication round r:
       - Server sends w^(r) to clients.
       - Each client performs E local SGD epochs on D_k.
       - Server computes weighted average: w^(r+1) = sum_k (n_k / n) w_k^(r)
     Client Drift Phenomenon: For non-IID partitions, large E causes local models
     to drift toward local minima, reducing global convergence speed.

  2. Multi-Task Optimization with Conflicting Gradients:
     Objective: Simultaneously minimize L_1(theta) and L_2(theta).
     Conflict: <grad L_1, grad L_2> < 0.
     - Baseline: Equal weighting L = 0.5 * L_1 + 0.5 * L_2.
     - MGDA (Multiple Gradient Descent Algorithm, Desideri 2012 / Sener & Koltun 2018):
       Finds the minimum-norm point in the convex hull of task gradients:
         min_{alpha in [0, 1]} || alpha * g_1 + (1 - alpha) * g_2 ||^2
       Guarantees simultaneous descent: <g_MGDA, g_1> >= 0 and <g_MGDA, g_2> >= 0.
     - GradNorm (Chen et al. 2018):
       Dynamically balances task loss weights w_i(t) based on gradient norms and
       relative loss training rates r_i(t) = (L_i(t) / L_i(0)) / mean_j(L_j(t) / L_j(0)).
"""

import sys
import os
import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ==============================================================================
# 1. FEDERATED AVERAGING (FedAvg) VS CENTRALIZED TRAINING
# ==============================================================================
class FederatedDataset:
    """
    Generates a non-IID partitioned dataset across K clients using Dirichlet distribution.
    Linear regression model: y = X @ w_true + noise.
    """
    def __init__(self, n_samples: int = 1000, n_features: int = 10, n_clients: int = 5, seed: int = 42):
        self.n_samples = n_samples
        self.n_features = n_features
        self.n_clients = n_clients
        
        rng = np.random.RandomState(seed)
        self.w_true = rng.randn(n_features)
        
        # Generate full dataset
        X_all = rng.randn(n_samples, n_features)
        y_all = X_all @ self.w_true + 0.2 * rng.randn(n_samples)
        
        # Partition data non-IID across clients based on feature 0 sorting
        sort_idx = np.argsort(X_all[:, 0])
        client_splits = np.array_split(sort_idx, n_clients)
        
        self.client_data = []
        for split in client_splits:
            self.client_data.append((X_all[split], y_all[split]))
            
        # Holdout test set
        self.X_test = rng.randn(300, n_features)
        self.y_test = self.X_test @ self.w_true + 0.2 * rng.randn(300)

    def evaluate_loss(self, w: np.ndarray) -> float:
        """Global test MSE loss."""
        preds = self.X_test @ w
        return float(np.mean((preds - self.y_test) ** 2))


def train_centralized(
    dataset: FederatedDataset,
    total_steps: int = 100,
    lr: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Centralized baseline: Direct gradient descent on unified pooled data.
    """
    X_pool = np.vstack([data[0] for data in dataset.client_data])
    y_pool = np.concatenate([data[1] for data in dataset.client_data])
    n = len(X_pool)

    rng = np.random.RandomState(seed)
    w = rng.randn(dataset.n_features) * 0.1
    history = [dataset.evaluate_loss(w)]

    t0 = time.perf_counter()
    for _ in range(total_steps):
        grad = (2.0 / n) * X_pool.T @ (X_pool @ w - y_pool)
        w -= lr * grad
        history.append(dataset.evaluate_loss(w))
    dt_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "paradigm": "Centralized",
        "final_loss": history[-1],
        "history": history,
        "runtime_ms": dt_ms,
        "optimal_w": w.tolist()
    }


def train_fedavg(
    dataset: FederatedDataset,
    num_rounds: int = 20,
    local_epochs: int = 5,
    lr: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Federated Averaging (FedAvg):
      In each round, clients perform local_epochs steps of SGD,
      then server aggregates client models via weighted average.
    """
    rng = np.random.RandomState(seed)
    w_global = rng.randn(dataset.n_features) * 0.1
    history = [dataset.evaluate_loss(w_global)]

    total_samples = dataset.n_samples
    t0 = time.perf_counter()

    for r in range(num_rounds):
        client_weights = []
        client_sizes = []

        # Local training on each client
        for X_c, y_c in dataset.client_data:
            w_local = w_global.copy()
            n_c = len(X_c)

            for _ in range(local_epochs):
                grad_c = (2.0 / n_c) * X_c.T @ (X_c @ w_local - y_c)
                w_local -= lr * grad_c

            client_weights.append(w_local)
            client_sizes.append(n_c)

        # Server aggregation: weighted average
        w_global = np.zeros_like(w_global)
        for w_c, n_c in zip(client_weights, client_sizes):
            w_global += (n_c / total_samples) * w_c

        history.append(dataset.evaluate_loss(w_global))

    dt_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "paradigm": f"FedAvg (Rounds={num_rounds}, Local={local_epochs})",
        "num_rounds": num_rounds,
        "local_epochs": local_epochs,
        "final_loss": history[-1],
        "history": history,
        "runtime_ms": dt_ms,
        "optimal_w": w_global.tolist()
    }


# ==============================================================================
# 2. MULTI-TASK OPTIMIZATION: EQUAL WEIGHTING VS MGDA VS GRADNORM
# ==============================================================================
class ConflictingMultiTaskProblem:
    """
    A 2-task optimization problem with controllable gradient conflict:
      Task 1: L_1(theta) = 0.5 * || theta - c_1 ||^2
      Task 2: L_2(theta) = 0.5 * (theta - c_2)^T A (theta - c_2)
      
      where c_1 = (+1, ..., +1), c_2 = (-1, ..., -1), and A is an ill-conditioned
      positive definite matrix with condition number kappa = 10.0.
      
      Between c_1 and c_2, <grad L_1, grad L_2> < 0 (conflicting gradients).
    """
    def __init__(self, dim: int = 10, seed: int = 42):
        self.dim = dim
        self.c1 = np.ones(dim)
        self.c2 = -np.ones(dim)
        
        rng = np.random.RandomState(seed)
        # Create ill-conditioned matrix A
        Q, _ = np.linalg.qr(rng.randn(dim, dim))
        evals = np.linspace(1.0, 10.0, dim)
        self.A = Q @ np.diag(evals) @ Q.T

    def evaluate_losses(self, theta: np.ndarray) -> Tuple[float, float]:
        diff1 = theta - self.c1
        diff2 = theta - self.c2
        l1 = 0.5 * float(np.sum(diff1 ** 2))
        l2 = 0.5 * float(diff2 @ self.A @ diff2)
        return l1, l2

    def evaluate_gradients(self, theta: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        g1 = theta - self.c1
        g2 = self.A @ (theta - self.c2)
        return g1, g2


def solve_mgda_2task(g1: np.ndarray, g2: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Solves the Multiple Gradient Descent Algorithm (MGDA) quadratic program for 2 tasks:
      min_{alpha in [0, 1]} || alpha * g1 + (1 - alpha) * g2 ||^2
    
    Analytical 1D solution:
      alpha* = clip( (g2 - g1)^T g2 / ||g1 - g2||^2, 0, 1 )
      g_MGDA = alpha* * g1 + (1 - alpha*) * g2
    
    Guarantees:
      <g_MGDA, g1> >= 0 and <g_MGDA, g2> >= 0 (common descent direction).
    """
    diff = g1 - g2
    denom = float(np.sum(diff ** 2))
    if denom < 1e-12:
        return 0.5 * (g1 + g2), 0.5

    # Optimal unconstrained alpha
    alpha_unconstrained = float(np.dot(g2 - g1, g2) / denom)
    alpha_opt = float(np.clip(alpha_unconstrained, 0.0, 1.0))

    g_mgda = alpha_opt * g1 + (1.0 - alpha_opt) * g2
    return g_mgda, alpha_opt


def optimize_multitask(
    problem: ConflictingMultiTaskProblem,
    method: str = "equal",
    steps: int = 100,
    lr: float = 0.02,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Optimizes the 2-task conflicting problem using:
      1. 'equal': Uniform scalarization L = 0.5 * L1 + 0.5 * L2
      2. 'mgda': Multiple Gradient Descent Algorithm (Pareto descent)
      3. 'gradnorm': Gradient Normalization with dynamic loss balancing
    """
    rng = np.random.RandomState(seed)
    theta = rng.randn(problem.dim) * 0.5

    l1_0, l2_0 = problem.evaluate_losses(theta)
    weights = np.array([0.5, 0.5])
    
    history_l1 = [l1_0]
    history_l2 = [l2_0]
    gradient_angles = []

    t0 = time.perf_counter()

    for t in range(steps):
        l1, l2 = problem.evaluate_losses(theta)
        g1, g2 = problem.evaluate_gradients(theta)

        # Compute cosine similarity between task gradients
        cos_sim = float(np.dot(g1, g2) / (np.linalg.norm(g1) * np.linalg.norm(g2) + 1e-12))
        gradient_angles.append(cos_sim)

        if method == "equal":
            # Baseline: equal weights 0.5 * g1 + 0.5 * g2
            g_step = 0.5 * g1 + 0.5 * g2

        elif method == "mgda":
            # MGDA Pareto descent direction
            g_mgda, alpha = solve_mgda_2task(g1, g2)
            g_step = g_mgda

        elif method == "gradnorm":
            # GradNorm loss balancing
            norm1 = np.linalg.norm(g1)
            norm2 = np.linalg.norm(g2)
            mean_norm = 0.5 * (norm1 + norm2)

            # Relative inverse training rates
            r1 = (l1 / max(l1_0, 1e-6))
            r2 = (l2 / max(l2_0, 1e-6))
            mean_r = 0.5 * (r1 + r2)

            target1 = mean_norm * ((r1 / mean_r) ** 1.5)
            target2 = mean_norm * ((r2 / mean_r) ** 1.5)

            # Update weights towards target gradient norms
            w1_raw = target1 / (norm1 + 1e-6)
            w2_raw = target2 / (norm2 + 1e-6)
            w_sum = w1_raw + w2_raw
            weights = np.array([w1_raw / w_sum, w2_raw / w_sum])

            g_step = weights[0] * g1 + weights[1] * g2

        else:
            raise ValueError(f"Unknown method: {method}")

        theta -= lr * g_step
        curr_l1, curr_l2 = problem.evaluate_losses(theta)
        history_l1.append(curr_l1)
        history_l2.append(curr_l2)

    dt_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "method": method,
        "final_l1": history_l1[-1],
        "final_l2": history_l2[-1],
        "history_l1": history_l1,
        "history_l2": history_l2,
        "mean_gradient_cosine": float(np.mean(gradient_angles)),
        "final_theta": theta.tolist(),
        "runtime_ms": dt_ms
    }
