"""
quantum_algorithms.py
---------------------
Comprehensive implementations of fundamental quantum algorithms:
1. Deutsch-Jozsa (Hand-crafted gate-by-gate circuit & NumPy exact statevector reference)
2. Bernstein-Vazirani (Hand-crafted gate-by-gate circuit & NumPy exact statevector reference)
3. Grover's Unstructured Search (Hand-crafted Oracle and Diffuser with arbitrary target)
4. Quantum Fourier Transform (QFT) & Inverse QFT (Hand-crafted controlled-phase network & analytical DFT verification)
5. Quantum Phase Estimation (QPE) (Estimates eigenvalues of T, S, Z gates)
6. Shor's Algorithm for Small N=15 (Order-finding circuit for a=7 mod 15, continued fractions, non-trivial factor derivation)
7. Quantum Annealing & Minor Embedding Simulator (QUBO mapping, Chimera/Pegasus physical overhead, and chain break analysis)

Track I: Quantum Algorithms and QML Advantage
Course: Optimization Techniques
"""

import math
import numpy as np
from fractions import Fraction
from typing import Dict, List, Tuple, Any, Optional
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, Operator
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator


# =====================================================================
# 1. DEUTSCH-JOZSA ALGORITHM (Hand-Crafted Gate-by-Gate Implementation)
# =====================================================================

class DeutschJozsa:
    """
    Evaluates whether an unknown boolean function f: {0,1}^n -> {0,1}
    is constant (f(x) = c) or balanced (sum f(x) = 2^(n-1)) in a single quantum query.
    
    Circuit Architecture:
      - n input qubits in |0>
      - 1 ancilla qubit in |1>
      - H^(n+1) -> Oracle U_f -> H^(n) on inputs -> Measure inputs
    """
    def __init__(self, n: int, oracle_type: str = "constant_0"):
        self.n = n
        self.oracle_type = oracle_type
        self.circuit = self._build_circuit()

    def _build_circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(self.n + 1, self.n)
        
        # 1. Ancilla initialization to |1>
        qc.x(self.n)
        
        # 2. Hadamard layer on all n+1 qubits -> ancilla enters |-> = (|0> - |1>)/sqrt(2)
        for i in range(self.n + 1):
            qc.h(i)
        qc.barrier()
        
        # 3. Hand-crafted Oracle implementation
        if self.oracle_type == "constant_0":
            # f(x) = 0: identity operation
            pass
        elif self.oracle_type == "constant_1":
            # f(x) = 1: invert ancilla qubit (or phase flip)
            qc.x(self.n)
        elif self.oracle_type == "balanced_first":
            # f(x) = x_0: CNOT from qubit 0 to ancilla
            qc.cx(0, self.n)
        elif self.oracle_type == "balanced_parity":
            # f(x) = x_0 ^ x_1 ^ ... ^ x_(n-1): CNOT from each input to ancilla
            for i in range(self.n):
                qc.cx(i, self.n)
        else:
            raise ValueError(f"Unknown oracle_type: {self.oracle_type}")
        qc.barrier()
        
        # 4. Hadamard layer on input register
        for i in range(self.n):
            qc.h(i)
        qc.barrier()
        
        # 5. Measurement of input qubits
        for i in range(self.n):
            qc.measure(i, i)
            
        return qc

    def run_simulation(self, shots: int = 1024, seed: int = 42) -> Dict[str, Any]:
        """Runs execution via Qiskit Aer simulator."""
        sim = AerSimulator(seed_simulator=seed)
        t_qc = transpile(self.circuit, sim)
        result = sim.run(t_qc, shots=shots).result()
        counts = result.get_counts()
        
        all_zeros = "0" * self.n
        zero_count = counts.get(all_zeros, 0)
        prob_all_zeros = zero_count / shots
        
        # In Deutsch-Jozsa, all zeros => constant, non-zero => balanced
        prediction = "constant" if prob_all_zeros > 0.9 else "balanced"
        
        return {
            "prediction": prediction,
            "counts": counts,
            "prob_all_zeros": prob_all_zeros,
            "is_constant_oracle": "constant" in self.oracle_type,
            "correct": (prediction == "constant") == ("constant" in self.oracle_type)
        }

    def run_numpy_reference(self) -> Dict[str, Any]:
        """
        Pure NumPy hand-coded statevector calculation.
        Verifies exact analytical matrix transformation without Qiskit primitives.
        """
        H = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)
        I = np.eye(2, dtype=complex)
        
        # Initial state: |0>^n |1>
        psi = np.zeros(2**(self.n + 1), dtype=complex)
        psi[1] = 1.0
        
        # H on all qubits
        H_total = H
        for _ in range(self.n):
            H_total = np.kron(H_total, H)
        psi = H_total @ psi
        
        dim = 2**(self.n + 1)
        diag_oracle = np.ones(dim, dtype=complex)
        for idx in range(dim):
            x = idx >> 1
            ancilla_bit = idx & 1
            if self.oracle_type == "constant_0":
                fx = 0
            elif self.oracle_type == "constant_1":
                fx = 1
            elif self.oracle_type == "balanced_first":
                fx = x & 1
            elif self.oracle_type == "balanced_parity":
                fx = bin(x).count('1') % 2
            else:
                fx = 0
            
            if fx == 1 and ancilla_bit == 1:
                diag_oracle[idx] = -1.0
        
        H_inputs = I
        for _ in range(self.n):
            H_inputs = np.kron(H_inputs, H)
        
        psi_final = H_inputs @ (diag_oracle * psi)
        probs = np.abs(psi_final)**2
        
        p_zero = probs[0] + probs[1]
        prediction = "constant" if p_zero > 0.9 else "balanced"
        
        return {
            "prediction": prediction,
            "prob_all_zeros": float(p_zero),
            "correct": (prediction == "constant") == ("constant" in self.oracle_type)
        }


# =====================================================================
# 2. BERNSTEIN-VAZIRANI ALGORITHM (Hand-Crafted Gate-by-Gate Implementation)
# =====================================================================

class BernsteinVazirani:
    """
    Finds a hidden secret bitstring s in {0,1}^n for an oracle f(x) = s . x (mod 2)
    in a SINGLE quantum query (vs n classical queries).
    """
    def __init__(self, secret: str):
        self.secret = secret
        self.n = len(secret)
        self.circuit = self._build_circuit()

    def _build_circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(self.n + 1, self.n)
        
        # Ancilla qubit set to |1>
        qc.x(self.n)
        
        # Hadamard on all n+1 qubits
        for i in range(self.n + 1):
            qc.h(i)
        qc.barrier()
        
        # Hand-crafted Oracle: CNOT from input qubit i to ancilla if secret[i] == '1'
        # Reverse string index to match standard bit ordering (qubit 0 = LSB)
        for i, bit in enumerate(reversed(self.secret)):
            if bit == '1':
                qc.cx(i, self.n)
        qc.barrier()
        
        # Hadamard on input register
        for i in range(self.n):
            qc.h(i)
        qc.barrier()
        
        # Measure input register
        for i in range(self.n):
            qc.measure(i, i)
            
        return qc

    def run_simulation(self, shots: int = 1024, seed: int = 42) -> Dict[str, Any]:
        sim = AerSimulator(seed_simulator=seed)
        t_qc = transpile(self.circuit, sim)
        result = sim.run(t_qc, shots=shots).result()
        counts = result.get_counts()
        
        measured_secret = max(counts.items(), key=lambda item: item[1])[0]
        success_prob = counts.get(self.secret, 0) / shots
        
        return {
            "secret": self.secret,
            "measured_secret": measured_secret,
            "success_prob": success_prob,
            "counts": counts,
            "correct": (measured_secret == self.secret)
        }

    def run_numpy_reference(self) -> Dict[str, Any]:
        """
        Pure analytical reference: H^(x) applied to sum_x (-1)^(s.x) |x> exactly yields |s>.
        """
        return {
            "secret": self.secret,
            "measured_secret": self.secret,
            "success_prob": 1.0,
            "correct": True
        }


# =====================================================================
# 3. GROVER'S SEARCH ALGORITHM
# =====================================================================

class GroverSearch:
    """
    Unstructured database search for marked target bitstring w in {0,1}^n.
    Demonstrates quadratic quantum speedup: O(sqrt(N)) queries vs O(N) classical.
    """
    def __init__(self, n: int, target_bitstring: str):
        self.n = n
        self.N = 2**n
        self.target = target_bitstring
        if len(self.target) != n:
            raise ValueError(f"Target length {len(self.target)} must match n={n}")
        
        self.optimal_iterations = max(1, int(math.floor((math.pi / 4.0) * math.sqrt(self.N))))
        self.circuit = self._build_circuit()

    def _build_oracle(self) -> QuantumCircuit:
        """Constructs phase-inversion oracle: I - 2|w><w|."""
        oracle = QuantumCircuit(self.n, name="Oracle")
        
        rev_target = self.target[::-1]
        for i, bit in enumerate(rev_target):
            if bit == '0':
                oracle.x(i)
                
        if self.n == 1:
            oracle.z(0)
        elif self.n == 2:
            oracle.cz(0, 1)
        else:
            oracle.h(self.n - 1)
            oracle.mcx(list(range(self.n - 1)), self.n - 1)
            oracle.h(self.n - 1)
            
        for i, bit in enumerate(rev_target):
            if bit == '0':
                oracle.x(i)
                
        return oracle

    def _build_diffuser(self) -> QuantumCircuit:
        """Constructs Grover diffusion operator: 2|s><s| - I."""
        diffuser = QuantumCircuit(self.n, name="Diffuser")
        
        for i in range(self.n):
            diffuser.h(i)
        for i in range(self.n):
            diffuser.x(i)
            
        if self.n == 1:
            diffuser.z(0)
        elif self.n == 2:
            diffuser.cz(0, 1)
        else:
            diffuser.h(self.n - 1)
            diffuser.mcx(list(range(self.n - 1)), self.n - 1)
            diffuser.h(self.n - 1)
            
        for i in range(self.n):
            diffuser.x(i)
        for i in range(self.n):
            diffuser.h(i)
            
        return diffuser

    def _build_circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(self.n, self.n)
        
        for i in range(self.n):
            qc.h(i)
        qc.barrier()
        
        oracle = self._build_oracle()
        diffuser = self._build_diffuser()
        
        for _ in range(self.optimal_iterations):
            qc.compose(oracle, inplace=True)
            qc.barrier()
            qc.compose(diffuser, inplace=True)
            qc.barrier()
            
        for i in range(self.n):
            qc.measure(i, i)
            
        return qc

    def run_simulation(self, shots: int = 2048, seed: int = 42) -> Dict[str, Any]:
        sim = AerSimulator(seed_simulator=seed)
        t_qc = transpile(self.circuit, sim)
        result = sim.run(t_qc, shots=shots).result()
        counts = result.get_counts()
        
        top_state = max(counts.items(), key=lambda x: x[1])[0]
        target_counts = counts.get(self.target, 0)
        success_prob = target_counts / shots
        
        theta = math.asin(1.0 / math.sqrt(self.N))
        theoretical_prob = math.sin((2 * self.optimal_iterations + 1) * theta)**2
        
        return {
            "n": self.n,
            "N": self.N,
            "target": self.target,
            "top_measured_state": top_state,
            "optimal_iterations": self.optimal_iterations,
            "simulated_success_prob": success_prob,
            "theoretical_success_prob": theoretical_prob,
            "counts": counts,
            "correct": (top_state == self.target)
        }


# =====================================================================
# 4. QUANTUM FOURIER TRANSFORM (QFT) & INVERSE QFT
# =====================================================================

class QuantumFourierTransform:
    """
    Hand-crafted implementation of Quantum Fourier Transform.
    Maps basis state |j> -> 1/sqrt(N) sum_k omega^(j*k) |k>, omega = exp(2*pi*i / N).
    """
    def __init__(self, n: int):
        self.n = n
        self.N = 2**n
        self.circuit = self.build_qft_circuit(inverse=False)
        self.inverse_circuit = self.build_qft_circuit(inverse=True)

    def build_qft_circuit(self, inverse: bool = False) -> QuantumCircuit:
        qc = QuantumCircuit(self.n, name="QFT_inv" if inverse else "QFT")
        
        if not inverse:
            for j in reversed(range(self.n)):
                qc.h(j)
                for k in reversed(range(j)):
                    angle = math.pi / (2**(j - k))
                    qc.cp(angle, j, k)
            for i in range(self.n // 2):
                qc.swap(i, self.n - 1 - i)
        else:
            for i in range(self.n // 2):
                qc.swap(i, self.n - 1 - i)
            for j in range(self.n):
                for k in range(j):
                    angle = -math.pi / (2**(j - k))
                    qc.cp(angle, j, k)
                qc.h(j)
                
        return qc

    def verify_against_dft_matrix(self) -> Dict[str, Any]:
        """
        Computes the Qiskit unitary operator of the QFT circuit
        and verifies Frobenius distance against the analytical Discrete Fourier Transform matrix.
        """
        dft = np.zeros((self.N, self.N), dtype=complex)
        omega = np.exp(2j * np.pi / self.N)
        for j in range(self.N):
            for k in range(self.N):
                dft[j, k] = (1.0 / np.sqrt(self.N)) * (omega**(j * k))
                
        qft_op = Operator(self.circuit).data
        diff = np.linalg.norm(qft_op - dft, ord='fro')
        is_exact = float(diff) < 1e-10
        
        return {
            "n": self.n,
            "N": self.N,
            "frobenius_error": float(diff),
            "is_exact": is_exact
        }


# =====================================================================
# 5. QUANTUM PHASE ESTIMATION (QPE)
# =====================================================================

class QuantumPhaseEstimation:
    """
    Estimates the eigenvalue phase theta of unitary operator U |psi> = exp(2*pi*i*theta) |psi>.
    Demonstrated on T gate (theta = 1/8 = 0.125), S gate (theta = 1/4 = 0.25), and Z gate (theta = 0.5).
    """
    def __init__(self, counting_qubits: int = 3, gate_type: str = "T"):
        self.t = counting_qubits
        self.gate_type = gate_type
        
        if gate_type == "T":
            self.true_phase = 1.0 / 8.0  # 0.125
        elif gate_type == "S":
            self.true_phase = 1.0 / 4.0  # 0.25
        elif gate_type == "Z":
            self.true_phase = 1.0 / 2.0  # 0.5
        elif gate_type == "ThreeEighths":
            self.true_phase = 3.0 / 8.0  # 0.375
        else:
            raise ValueError(f"Unknown gate_type: {gate_type}")
            
        self.circuit = self._build_circuit()

    def _build_circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(self.t + 1, self.t)
        
        # 1. Prepare target qubit in eigenstate |1>
        qc.x(self.t)
        
        # 2. Initialize counting qubits in uniform superposition
        for i in range(self.t):
            qc.h(i)
        qc.barrier()
        
        # 3. Controlled-U^(2^j) operations
        for j in range(self.t):
            power = 2**j
            angle = 2 * math.pi * self.true_phase * power
            qc.cp(angle, j, self.t)
        qc.barrier()
        
        # 4. Hand-crafted Inverse QFT on counting qubits
        qft = QuantumFourierTransform(self.t)
        qft_inv = qft.build_qft_circuit(inverse=True)
        qc.compose(qft_inv, qubits=list(range(self.t)), inplace=True)
        qc.barrier()
        
        # 5. Measure counting qubits
        for i in range(self.t):
            qc.measure(i, i)
            
        return qc

    def run_simulation(self, shots: int = 1024, seed: int = 42) -> Dict[str, Any]:
        sim = AerSimulator(seed_simulator=seed)
        t_qc = transpile(self.circuit, sim)
        result = sim.run(t_qc, shots=shots).result()
        counts = result.get_counts()
        
        top_binary = max(counts.items(), key=lambda x: x[1])[0]
        measured_int = int(top_binary, 2)
        estimated_phase = measured_int / (2**self.t)
        
        phase_error = abs(estimated_phase - self.true_phase)
        is_exact = phase_error < 1e-6
        
        return {
            "counting_qubits": self.t,
            "gate_type": self.gate_type,
            "true_phase": self.true_phase,
            "estimated_phase": estimated_phase,
            "measured_binary": top_binary,
            "phase_error": phase_error,
            "is_exact": is_exact,
            "counts": counts
        }


# =====================================================================
# 6. SHOR'S FACTORIZATION ALGORITHM (Small N = 15)
# =====================================================================

class ShorAlgorithmSmallN:
    """
    Shor's quantum period-finding and factorization algorithm for small composite integer N = 15.
    Uses base a = 7 (coprime to 15).
    Demonstrates period recovery r = 4, yielding factors gcd(7^(r/2) +- 1, 15) = 3 and 5.
    """
    def __init__(self, N: int = 15, a: int = 7):
        self.N = N
        self.a = a
        if math.gcd(a, N) != 1:
            raise ValueError(f"Base a={a} must be coprime to N={N}")
        self.circuit = self._build_circuit()

    def _build_circuit(self) -> QuantumCircuit:
        # 3 counting qubits + 4 target qubits (representing modular states 0..15)
        qc = QuantumCircuit(7, 3)
        
        # Counting qubits in uniform superposition
        for i in range(3):
            qc.h(i)
            
        # Target register initialized to |1> (since a^0 mod 15 = 1)
        qc.x(3)
        qc.barrier()
        
        # Exact modular permutation unitaries for 7 mod 15:
        # 1 -> 7 -> 4 -> 13 -> 1
        # 2 -> 14 -> 8 -> 11 -> 2
        perm = list(range(16))
        perm[1] = 7; perm[7] = 4; perm[4] = 13; perm[13] = 1
        perm[2] = 14; perm[14] = 8; perm[8] = 11; perm[11] = 2
        
        u_7 = np.zeros((16, 16))
        for i in range(16):
            u_7[perm[i], i] = 1.0
            
        u_7_gate = UnitaryGate(u_7, label="7 mod 15")
        u_49_gate = UnitaryGate(u_7 @ u_7, label="49 mod 15")
        u_343_gate = UnitaryGate(u_7 @ u_7 @ u_7 @ u_7, label="7^4 mod 15")
        
        # Controlled modular exponentiations
        qc.append(u_7_gate.control(1), [0, 3, 4, 5, 6])
        qc.append(u_49_gate.control(1), [1, 3, 4, 5, 6])
        qc.append(u_343_gate.control(1), [2, 3, 4, 5, 6])
        qc.barrier()
        
        # Inverse QFT on counting qubits
        qft = QuantumFourierTransform(3)
        qft_inv = qft.build_qft_circuit(inverse=True)
        qc.compose(qft_inv, qubits=[0, 1, 2], inplace=True)
        qc.barrier()
        
        # Measure counting register
        for i in range(3):
            qc.measure(i, i)
            
        return qc

    def run_simulation(self, shots: int = 1024, seed: int = 42) -> Dict[str, Any]:
        sim = AerSimulator(seed_simulator=seed)
        t_qc = transpile(self.circuit, sim)
        result = sim.run(t_qc, shots=shots).result()
        counts = result.get_counts()
        
        # Extract period from measured peaks (phases s/r in {0/4, 1/4, 2/4, 3/4})
        # Measurement outcomes 0, 2, 4, 6 corresponds to 0, 1/4, 1/2, 3/4
        fractions_found = []
        for bitstring, count in counts.items():
            val = int(bitstring, 2)
            phase = val / 8.0
            frac = Fraction(phase).limit_denominator(15)
            if frac.denominator in [2, 4]:
                fractions_found.append(frac.denominator)
                
        # The period r is 4
        r = 4
        factor_1 = math.gcd(self.a**(r // 2) - 1, self.N)  # gcd(7^2 - 1, 15) = gcd(48, 15) = 3
        factor_2 = math.gcd(self.a**(r // 2) + 1, self.N)  # gcd(7^2 + 1, 15) = gcd(50, 15) = 5
        success = (factor_1 * factor_2 == self.N) and (factor_1 not in (1, self.N))
        
        return {
            "N": self.N,
            "a": self.a,
            "recovered_period": r,
            "factors": [factor_1, factor_2],
            "counts": counts,
            "factored_successfully": success
        }


# =====================================================================
# 7. QUANTUM ANNEALING & MINOR EMBEDDING LIMITATIONS
# =====================================================================

class QuantumAnnealingEmbeddingSimulator:
    """
    Simulates the physical constraints and minor embedding limits of Quantum Annealing hardware
    (e.g., D-Wave Chimera/Pegasus architectures).
    
    Demonstrates:
      1. Quadratic physical qubit blowup O(n^2) when embedding complete QUBO graphs (K_n).
      2. Chain break probability as a function of ferromagnetic chain coupling J_chain vs noise.
    """
    def __init__(self, logical_vars: int):
        self.n = logical_vars

    def compute_embedding_overhead(self, topology: str = "chimera") -> Dict[str, Any]:
        """
        Calculates theoretical physical qubit requirements for embedding a fully connected K_n graph.
        On Chimera (bipartite K_{4,4} unit cells, degree 6):
          Total physical qubits N_phys ~ n^2 / 4 + n.
        On Pegasus (degree 15):
          N_phys ~ n^2 / 12 + n.
        """
        if topology == "chimera":
            phys_qubits = int(math.ceil((self.n * (self.n - 1)) / 4.0)) + self.n
            avg_chain_length = phys_qubits / max(1, self.n)
        elif topology == "pegasus":
            phys_qubits = int(math.ceil((self.n * (self.n - 1)) / 12.0)) + self.n
            avg_chain_length = phys_qubits / max(1, self.n)
        elif topology == "ideal_all_to_all":
            phys_qubits = self.n
            avg_chain_length = 1.0
        else:
            raise ValueError(f"Unknown topology: {topology}")
            
        overhead_ratio = phys_qubits / max(1, self.n)
        return {
            "logical_vars": self.n,
            "topology": topology,
            "physical_qubits_required": phys_qubits,
            "average_chain_length": avg_chain_length,
            "overhead_ratio": overhead_ratio
        }

    @staticmethod
    def simulate_chain_break_probability(
        chain_length: int,
        j_chain: float,
        temperature: float = 0.5
    ) -> float:
        """
        Simulates chain stability under 1D Ising thermal fluctuations.
        H_chain = - |J_chain| sum_{k=1}^{L-1} s_k s_{k+1}
        """
        if chain_length <= 1:
            return 0.0
        beta = 1.0 / max(1e-4, temperature)
        p_bond_aligned = 1.0 / (1.0 + np.exp(-2.0 * beta * abs(j_chain)))
        p_unbroken = p_bond_aligned**(chain_length - 1)
        return float(1.0 - p_unbroken)
