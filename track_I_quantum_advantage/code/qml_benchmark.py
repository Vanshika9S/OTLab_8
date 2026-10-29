"""
qml_benchmark.py
----------------
Empirical comparison of Quantum Machine Learning (Variational Quantum Classifier)
against equivalent Classical Models (Logistic Regression, 2-Layer MLP, and RBF SVM)
on identical binary classification data.

Features:
- Identical dataset: Scikit-Learn Make Moons (non-linear, 100 samples, 2 features, 70/30 split).
- VQC: Angle feature map + TwoLocal parameterized variational ansatz + Z expectation observable.
- Classical MLP: 2-layer neural network with comparable parameter budget (17 params).
- Classical RBF SVM & Logistic Regression.
- Rigorous statistical protocol: 10 seeds, reporting Train/Test Accuracy, Training Time,
  Parameter Count, and Number of Circuit Evaluations / Model Inferences.

Track I: Quantum Algorithms and QML Advantage
Course: Optimization Techniques
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator


class VariationalQuantumClassifier:
    """
    Variational Quantum Classifier (VQC) with SPSA optimizer.
    Qubits: 2.
    Feature encoding: Angle map [Ry(x0), Ry(x1)] + CX + Rz(x0 * x1).
    Ansatz: 2 variational layers of Ry, Rz rotations with circular entanglement.
    Total Trainable Parameters: 8.
    """
    def __init__(self, num_qubits: int = 2, num_layers: int = 2, seed: int = 42):
        self.n = num_qubits
        self.num_layers = num_layers
        self.num_params = num_qubits * num_layers * 2  # 2 * 2 * 2 = 8
        self.seed = seed
        np.random.seed(seed)
        self.theta = np.random.uniform(-np.pi, np.pi, self.num_params)
        self.circuit_evaluations = 0

    def _build_circuit(self, x: np.ndarray, theta: np.ndarray) -> QuantumCircuit:
        qc = QuantumCircuit(self.n)
        
        # 1. Feature Map (Angle Encoding)
        qc.ry(x[0], 0)
        qc.ry(x[1], 1)
        qc.cx(0, 1)
        qc.rz(x[0] * x[1], 1)
        qc.barrier()
        
        # 2. Variational Ansatz
        idx = 0
        for _ in range(self.num_layers):
            for q in range(self.n):
                qc.ry(theta[idx], q)
                qc.rz(theta[idx + 1], q)
                idx += 2
            qc.cx(0, 1)
            qc.barrier()
            
        return qc

    def _predict_single_expectation(self, x: np.ndarray, theta: np.ndarray) -> float:
        """Computes <Z_0> expectation via exact statevector."""
        self.circuit_evaluations += 1
        qc = self._build_circuit(x, theta)
        sv = Statevector.from_instruction(qc)
        # Pauli Z on qubit 0: Z (x) I
        z0 = SparsePauliOp(["IZ"]) # In Qiskit, rightmost character is qubit 0
        exp_val = float(np.real(sv.expectation_value(z0)))
        return exp_val

    def predict_expectations(self, X: np.ndarray, theta: Optional[np.ndarray] = None) -> np.ndarray:
        if theta is None:
            theta = self.theta
        return np.array([self._predict_single_expectation(x, theta) for x in X])

    def predict(self, X: np.ndarray, theta: Optional[np.ndarray] = None) -> np.ndarray:
        exp_vals = self.predict_expectations(X, theta)
        return np.where(exp_vals >= 0.0, 1, 0)

    def _compute_loss(self, X: np.ndarray, y_target: np.ndarray, theta: np.ndarray) -> float:
        """Mean squared error loss on {-1, +1} targets."""
        exp_vals = self.predict_expectations(X, theta)
        return float(np.mean((exp_vals - y_target)**2))

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, max_iter: int = 30, lr: float = 0.15) -> float:
        """
        Trains the VQC using Simultaneous Perturbation Stochastic Approximation (SPSA).
        Each SPSA step requires exactly 2 function evaluations across the batch.
        """
        start_time = time.perf_counter()
        # Convert {0, 1} targets to {-1, +1}
        y_pm = np.where(y_train == 1, 1.0, -1.0)
        
        c = 0.1  # perturbation magnitude
        for k in range(1, max_iter + 1):
            ak = lr / (k**0.602)
            ck = c / (k**0.101)
            
            # Rademacher perturbation vector (+-1 with equal probability)
            delta = 2 * np.random.randint(0, 2, size=self.num_params) - 1
            
            theta_plus = self.theta + ck * delta
            theta_minus = self.theta - ck * delta
            
            loss_plus = self._compute_loss(X_train, y_pm, theta_plus)
            loss_minus = self._compute_loss(X_train, y_pm, theta_minus)
            
            # SPSA gradient estimate
            grad = ((loss_plus - loss_minus) / (2.0 * ck)) * delta
            
            # Parameter update
            self.theta = self.theta - ak * grad
            
        elapsed = time.perf_counter() - start_time
        return elapsed


def run_qml_vs_classical_comparison(
    n_samples: int = 100,
    num_seeds: int = 10,
    vqc_iterations: int = 25
) -> pd.DataFrame:
    """
    Runs a rigorous benchmark comparing VQC vs Logistic Regression, Classical MLP,
    and Classical RBF SVM over 10 distinct dataset seeds.
    """
    all_results = []
    
    for seed in range(42, 42 + num_seeds):
        # 1. Generate Dataset
        X_raw, y = make_moons(n_samples=n_samples, noise=0.15, random_state=seed)
        # Normalize features to [-pi/2, pi/2] for quantum angle encoding
        X_norm = (X_raw - np.mean(X_raw, axis=0)) / (np.std(X_raw, axis=0) + 1e-8)
        X = np.clip(X_norm * (np.pi / 4.0), -np.pi / 2.0, np.pi / 2.0)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=seed, stratify=y
        )
        
        # Model 1: Variational Quantum Classifier (VQC)
        vqc = VariationalQuantumClassifier(num_qubits=2, num_layers=2, seed=seed)
        vqc_train_time = vqc.fit(X_train, y_train, max_iter=vqc_iterations, lr=0.2)
        vqc_train_acc = float(np.mean(vqc.predict(X_train) == y_train))
        vqc_test_acc = float(np.mean(vqc.predict(X_test) == y_test))
        vqc_evals = vqc.circuit_evaluations
        
        all_results.append({
            "seed": seed,
            "model": "Variational Quantum Classifier (VQC)",
            "paradigm": "Quantum",
            "train_acc": vqc_train_acc,
            "test_acc": vqc_test_acc,
            "train_time_sec": vqc_train_time,
            "param_count": vqc.num_params,
            "circuit_evaluations": vqc_evals
        })
        
        # Model 2: Classical Logistic Regression
        lr = LogisticRegression(max_iter=200, random_state=seed)
        t0 = time.perf_counter()
        lr.fit(X_train, y_train)
        lr_train_time = time.perf_counter() - t0
        lr_train_acc = float(lr.score(X_train, y_train))
        lr_test_acc = float(lr.score(X_test, y_test))
        lr_params = X_train.shape[1] + 1  # 2 weights + 1 bias = 3
        
        all_results.append({
            "seed": seed,
            "model": "Classical Logistic Regression",
            "paradigm": "Classical",
            "train_acc": lr_train_acc,
            "test_acc": lr_test_acc,
            "train_time_sec": lr_train_time,
            "param_count": lr_params,
            "circuit_evaluations": 0
        })
        
        # Model 3: Classical Multi-Layer Perceptron (2 inputs -> 4 hidden -> 1 output)
        mlp = MLPClassifier(hidden_layer_sizes=(4,), max_iter=250, random_state=seed, solver='adam')
        t0 = time.perf_counter()
        mlp.fit(X_train, y_train)
        mlp_train_time = time.perf_counter() - t0
        mlp_train_acc = float(mlp.score(X_train, y_train))
        mlp_test_acc = float(mlp.score(X_test, y_test))
        # Params: (2 * 4 + 4) + (4 * 1 + 1) = 17 params
        mlp_params = (2 * 4 + 4) + (4 * 1 + 1)
        
        all_results.append({
            "seed": seed,
            "model": "Classical MLP (1 Hidden Layer, 4 Units)",
            "paradigm": "Classical",
            "train_acc": mlp_train_acc,
            "test_acc": mlp_test_acc,
            "train_time_sec": mlp_train_time,
            "param_count": mlp_params,
            "circuit_evaluations": 0
        })
        
        # Model 4: Classical RBF SVM
        svm = SVC(kernel='rbf', C=1.0, random_state=seed)
        t0 = time.perf_counter()
        svm.fit(X_train, y_train)
        svm_train_time = time.perf_counter() - t0
        svm_train_acc = float(svm.score(X_train, y_train))
        svm_test_acc = float(svm.score(X_test, y_test))
        svm_params = len(svm.support_vectors_) * 2 + 1
        
        all_results.append({
            "seed": seed,
            "model": "Classical RBF SVM",
            "paradigm": "Classical",
            "train_acc": svm_train_acc,
            "test_acc": svm_test_acc,
            "train_time_sec": svm_train_time,
            "param_count": svm_params,
            "circuit_evaluations": 0
        })
        
    df_raw = pd.DataFrame(all_results)
    
    # Compute aggregate summary over 10 seeds (mean +- std)
    summary = []
    for model_name, grp in df_raw.groupby("model"):
        summary.append({
            "model": model_name,
            "paradigm": grp["paradigm"].iloc[0],
            "train_acc_mean": float(grp["train_acc"].mean()),
            "train_acc_std": float(grp["train_acc"].std()),
            "test_acc_mean": float(grp["test_acc"].mean()),
            "test_acc_std": float(grp["test_acc"].std()),
            "train_time_sec_mean": float(grp["train_time_sec"].mean()),
            "train_time_sec_std": float(grp["train_time_sec"].std()),
            "param_count": int(grp["param_count"].iloc[0]),
            "circuit_evaluations_mean": float(grp["circuit_evaluations"].mean()),
        })
        
    df_summary = pd.DataFrame(summary).sort_values(by="test_acc_mean", ascending=False)
    return df_raw, df_summary
