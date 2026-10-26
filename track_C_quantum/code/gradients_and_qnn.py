"""
gradients_and_qnn.py
--------------------
Quantum Gradient Algorithms & Parameterized Quantum Neural Network (PQC/QNN).

Implemented Methods:
  1. Parameter-Shift Rule: Exact analytical gradients on quantum hardware.
     d/d theta_k <O> = [ <O>_{theta_k + pi/2} - <O>_{theta_k - pi/2} ] / 2
  2. Finite-Difference Gradients: Central difference baseline (O(2 * d) evals).
  3. SPSA (Simultaneous Perturbation Stochastic Approximation):
     Stochastic gradient requiring strictly 2 circuit evaluations per step.
  4. Quantum Natural Gradient (QNG):
     theta_{t+1} = theta_t - eta * (F(theta) + lambda * I)^{-1} * grad <O>
     where F(theta) is the Fubini-Study / Quantum Fisher Information Matrix (QFIM).
  5. Parameterized Quantum Neural Network (PQC/QNN):
     Variational quantum classifier with feature encoding and trainable rotations.
"""

import sys
import os
import time
from typing import Dict, List, Tuple, Any, Callable, Optional
import numpy as np

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp


def compute_parameter_shift_gradient(
    circuit_builder: Callable[[np.ndarray], QuantumCircuit],
    params: np.ndarray,
    observable: SparsePauliOp
) -> np.ndarray:
    """
    Computes exact analytical gradient using the Parameter-Shift Rule.
    For gate U(theta) = exp(-i * theta/2 * P):
      d/d theta <O> = ( <O>(theta + pi/2) - <O>(theta - pi/2) ) / 2
    """
    d = len(params)
    grad = np.zeros(d, dtype=float)

    for i in range(d):
        p_plus = params.copy()
        p_minus = params.copy()
        p_plus[i] += np.pi / 2.0
        p_minus[i] -= np.pi / 2.0

        qc_plus = circuit_builder(p_plus)
        qc_minus = circuit_builder(p_minus)

        sv_plus = Statevector.from_instruction(qc_plus)
        sv_minus = Statevector.from_instruction(qc_minus)

        exp_plus = sv_plus.expectation_value(observable).real
        exp_minus = sv_minus.expectation_value(observable).real

        grad[i] = (exp_plus - exp_minus) / 2.0

    return grad


def compute_finite_difference_gradient(
    circuit_builder: Callable[[np.ndarray], QuantumCircuit],
    params: np.ndarray,
    observable: SparsePauliOp,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Computes central finite-difference gradient:
      d/d theta_k <O> ~ ( <O>(theta + eps * e_k) - <O>(theta - eps * e_k) ) / (2 * eps)
    """
    d = len(params)
    grad = np.zeros(d, dtype=float)

    for i in range(d):
        p_plus = params.copy()
        p_minus = params.copy()
        p_plus[i] += eps
        p_minus[i] -= eps

        qc_plus = circuit_builder(p_plus)
        qc_minus = circuit_builder(p_minus)

        sv_plus = Statevector.from_instruction(qc_plus)
        sv_minus = Statevector.from_instruction(qc_minus)

        exp_plus = sv_plus.expectation_value(observable).real
        exp_minus = sv_minus.expectation_value(observable).real

        grad[i] = (exp_plus - exp_minus) / (2.0 * eps)

    return grad


def verify_parameter_shift_vs_fd(
    circuit_builder: Callable[[np.ndarray], QuantumCircuit],
    params: np.ndarray,
    observable: SparsePauliOp,
    eps: float = 1e-5
) -> Dict[str, Any]:
    """
    Verifies that Parameter-Shift analytical gradients match Finite Differences.
    """
    grad_ps = compute_parameter_shift_gradient(circuit_builder, params, observable)
    grad_fd = compute_finite_difference_gradient(circuit_builder, params, observable, eps=eps)

    abs_diff = np.abs(grad_ps - grad_fd)
    max_abs_err = float(np.max(abs_diff))
    mean_abs_err = float(np.mean(abs_diff))

    # Relative error where denominator is non-zero
    denom = np.maximum(np.abs(grad_ps), 1e-6)
    rel_err = float(np.max(abs_diff / denom))

    return {
        "grad_parameter_shift": grad_ps.tolist(),
        "grad_finite_difference": grad_fd.tolist(),
        "max_abs_error": max_abs_err,
        "mean_abs_error": mean_abs_err,
        "max_rel_error": rel_err,
        "match": bool(max_abs_err < 1e-5)
    }


def compute_spsa_gradient(
    circuit_builder: Callable[[np.ndarray], QuantumCircuit],
    params: np.ndarray,
    observable: SparsePauliOp,
    c_k: float = 0.1,
    rng: Optional[np.random.RandomState] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simultaneous Perturbation Stochastic Approximation (SPSA) gradient estimator.
    Evaluates gradient using strictly 2 circuit evaluations regardless of dimension d:
      Delta in {-1, +1}^d
      g_k = ( f(theta + c_k * Delta) - f(theta - c_k * Delta) ) / (2 * c_k * Delta_k)
    """
    if rng is None:
        rng = np.random.RandomState()

    d = len(params)
    delta = rng.choice([-1.0, 1.0], size=d)

    p_plus = params + c_k * delta
    p_minus = params - c_k * delta

    qc_plus = circuit_builder(p_plus)
    qc_minus = circuit_builder(p_minus)

    sv_plus = Statevector.from_instruction(qc_plus)
    sv_minus = Statevector.from_instruction(qc_minus)

    exp_plus = sv_plus.expectation_value(observable).real
    exp_minus = sv_minus.expectation_value(observable).real

    diff = (exp_plus - exp_minus) / (2.0 * c_k)
    grad_est = diff / delta  # Element-wise division by Delta_k (+1 or -1)

    return grad_est, delta


def compute_quantum_fisher_information(
    circuit_builder: Callable[[np.ndarray], QuantumCircuit],
    params: np.ndarray,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Computes the Fubini-Study metric tensor (Quantum Fisher Information Matrix F):
      g_{ij}(theta) = Re[ <d_i psi | d_j psi> - <d_i psi | psi> <psi | d_j psi> ]
    
    Returns:
      (d x d) symmetric positive semi-definite matrix.
    """
    d = len(params)
    base_qc = circuit_builder(params)
    base_sv = np.array(Statevector.from_instruction(base_qc).data)

    # Compute parameter derivatives of the statevector: |d_i psi>
    d_psi = []
    for i in range(d):
        tp = params.copy()
        tm = params.copy()
        tp[i] += eps
        tm[i] -= eps
        svp = np.array(Statevector.from_instruction(circuit_builder(tp)).data)
        svm = np.array(Statevector.from_instruction(circuit_builder(tm)).data)
        d_psi.append((svp - svm) / (2.0 * eps))

    d_psi = np.array(d_psi)  # shape (d, 2^n)

    # Compute Fubini-Study tensor G
    G = np.zeros((d, d), dtype=float)
    for i in range(d):
        for j in range(d):
            term1 = np.vdot(d_psi[i], d_psi[j])
            term2 = np.vdot(d_psi[i], base_sv) * np.vdot(base_sv, d_psi[j])
            G[i, j] = float(np.real(term1 - term2))

    # Symmetrize for numerical stability
    G = 0.5 * (G + G.T)
    return G


def compute_quantum_natural_gradient(
    circuit_builder: Callable[[np.ndarray], QuantumCircuit],
    params: np.ndarray,
    observable: SparsePauliOp,
    regularizer: float = 1e-3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes Quantum Natural Gradient step:
      Delta theta = (F(theta) + regularizer * I)^{-1} * grad <O>
    
    Returns:
      (qng_step, qfi_matrix)
    """
    grad_euclidean = compute_parameter_shift_gradient(circuit_builder, params, observable)
    QFI = compute_quantum_fisher_information(circuit_builder, params)

    d = len(params)
    QFI_reg = QFI + regularizer * np.eye(d)
    qng_step = np.linalg.solve(QFI_reg, grad_euclidean)

    return qng_step, QFI


class ParameterizedQNN:
    """
    Parameterized Quantum Neural Network (QNN) / Variational Quantum Classifier (VQC).
    
    Architecture:
      Input encoding: Angle embedding via R_X(x_i)
      Variational block: R_Y(theta) and R_Z(theta) rotations with CNOT entanglement
      Observable: Measurement of Z on qubit 0 -> Expectation in [-1, +1]
    """
    def __init__(self, n_qubits: int = 2, n_layers: int = 1, seed: int = 42):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        # 4 parameters per layer for 2 qubits (RY and RZ on each qubit)
        self.num_params = n_layers * n_qubits * 2
        self.rng = np.random.RandomState(seed)
        self.weights = self.rng.uniform(-np.pi, np.pi, size=self.num_params)
        
        # Observable: Z on qubit 0
        label = ["I"] * n_qubits
        label[0] = "Z"
        self.observable = SparsePauliOp.from_list([("".join(reversed(label)), 1.0)])

    def build_circuit(self, x: np.ndarray, weights: np.ndarray) -> QuantumCircuit:
        """
        Builds the circuit encoding feature vector x and applying variational weights.
        """
        qc = QuantumCircuit(self.n_qubits)

        # Feature encoding
        for i in range(min(len(x), self.n_qubits)):
            qc.rx(x[i], i)

        # Variational layers
        idx = 0
        for _ in range(self.n_layers):
            for q in range(self.n_qubits):
                qc.ry(weights[idx], q)
                qc.rz(weights[idx + 1], q)
                idx += 2
            # Entanglement ring
            for q in range(self.n_qubits):
                qc.cx(q, (q + 1) % self.n_qubits)

        return qc

    def predict_expectation(self, x: np.ndarray, weights: Optional[np.ndarray] = None) -> float:
        """
        Computes forward pass expectation value <Z_0>.
        """
        if weights is None:
            weights = self.weights
        qc = self.build_circuit(x, weights)
        sv = Statevector.from_instruction(qc)
        return float(sv.expectation_value(self.observable).real)

    def train_epoch(
        self,
        X: np.ndarray,
        y: np.ndarray,
        method: str = "parameter_shift",
        lr: float = 0.05
    ) -> float:
        """
        Trains QNN on a batch of samples using specified gradient method.
        """
        total_loss = 0.0
        grad_accum = np.zeros_like(self.weights)

        for xi, yi in zip(X, y):
            pred = self.predict_expectation(xi, self.weights)
            # MSE Loss: (pred - yi)^2 -> dLoss/dPred = 2 * (pred - yi)
            loss = (pred - yi) ** 2
            total_loss += loss
            dloss_dpred = 2.0 * (pred - yi)

            def sample_circuit(w: np.ndarray) -> QuantumCircuit:
                return self.build_circuit(xi, w)

            if method == "parameter_shift":
                dpred_dw = compute_parameter_shift_gradient(sample_circuit, self.weights, self.observable)
            elif method == "spsa":
                dpred_dw, _ = compute_spsa_gradient(sample_circuit, self.weights, self.observable, c_k=0.1, rng=self.rng)
            elif method == "qng":
                dpred_dw, _ = compute_quantum_natural_gradient(sample_circuit, self.weights, self.observable, regularizer=1e-3)
            else:
                dpred_dw = compute_finite_difference_gradient(sample_circuit, self.weights, self.observable)

            grad_accum += dloss_dpred * dpred_dw

        grad_mean = grad_accum / len(X)
        self.weights -= lr * grad_mean
        return total_loss / len(X)
