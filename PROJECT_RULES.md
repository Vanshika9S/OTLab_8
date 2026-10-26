# PROJECT RULES & OPERATIONAL PROTOCOLS

This document establishes the binding scientific, engineering, and ethical rules governing all work in this repository for **Assignment 8: Optimize Anything (14-Day Vibe-Coding Challenge)**.

---

## 1. Scientific Integrity & Data Truthfulness

1. **Zero Fabrication**: Never fabricate numbers, timings, metrics, or graphs. Every figure, table, and data point in every report must be produced directly by verifiable code executed in this environment.
2. **Transparent Fallbacks**: If a method or environment cannot run locally (e.g. quantum physical hardware access, specific kernel virtualization constraints), state the exact limitation explicitly, explain the barrier, and provide a valid simulated or fallback pipeline. Never fake hardware measurements.
3. **Rigorous Stochastic Reporting**: For all stochastic methods (e.g., SGD, simulated annealing, SPSA, randomized heuristics, noisy quantum circuits), execute at least **10 repeated runs** with deterministic fixed seeds. Always report **mean ± standard deviation** (not just the best run).
4. **Fair & Controlled Comparisons**: Baselines and optimized variants must share identical input datasets, identical stopping/convergence criteria, and identical hardware/OS environments. Any unavoidable discrepancies must be clearly disclosed.
5. **Precise Claim Labeling**: Every reported benchmark must be explicitly labeled as:
   - `[Theoretical]` (analytical bounds / big-O),
   - `[Simulated]` (e.g., Qiskit statevector or ideal/noisy simulator, QEMU software emulation), or
   - `[Hardware-Measured]` (physical CPU/GPU wall-clock or physical QPU execution).
   Never claim a speedup or quantum advantage that the data does not conclusively demonstrate. Honest negative results with rigorous analysis earn full credit.
6. **Assumption Testing for Guarantees**: Never claim an approximation guarantee (e.g., greedy $(1 - 1/e)$ for submodular maximization, Christofides 1.5, or 2-approximation for vertex cover) without explicitly testing and verifying that the objective and constraints satisfy the mathematical preconditions (submodularity, monotonicity, metric triangle inequality, etc.).

---

## 2. Code Quality & Viva Readiness

1. **Viva-Ready Code**: The student must be able to explain and modify any line of code live during a viva examination without any AI assistance. Components that cannot be explained receive zero credit.
2. **Concise, Transparent, and Documented**: Keep all code minimal, modular, well-commented, and readable. Avoid unnecessary abstractions, overly complex frameworks, or bloated boilerplate.
3. **Interactive Explanation**: As code is developed, the AI assistant must explain each piece to the student, highlighting the underlying optimization logic, key data structures, and algorithmic invariants.
4. **Complete Track Architecture**: Every track directory (Tracks A through J) must contain:
   - Clear statement of **Objective**,
   - Well-defined **Baseline**,
   - **Fair Comparison** methodology,
   - **Unit Tests** covering edge cases and correctness checks,
   - **Trade-off Analysis** (speed vs quality, overheads, scalability),
   - **Critical Review** identifying weaknesses and boundaries.

---

## 3. Version Control & Traceability Convention

1. **Commit Message Prefix**:
   - Every AI-assisted commit must strictly use the prefix: `[AI:tool-model]` (e.g., `[AI:gemini-3.8-flash] Add ILP solver for Track B`).
   - Manual edits made by the student must have **no prefix** (e.g., `Refine objective penalty weights in Track E`).
2. **Full Provenance**: Maintain exact correspondence between prompt logs, Git commits, and code changes to satisfy Section 8 disclosure requirements and avoid academic misconduct.

---

## 4. Daily Close Routine

At the end of every working day (or daily milestone), the following 7-step sequence **must** be executed before concluding the turn:

1. **Run All Tests**: Execute all unit and integration test suites across active tracks to verify zero regressions.
2. **Persist Results & Artifacts**: Save generated raw metrics, tables, and visualization plots with explicit units, seeds, and metadata into the respective `results/` folder.
3. **Record Prompt Logs**: Write/update track prompt logs in `prompts/track_X/` documenting:
   - Original user prompt,
   - AI response excerpt,
   - Revised prompt / follow-up,
   - Resulting code change (commit / file link),
   - Verification and correctness note.
4. **Update Registers & Checklists**:
   - Update the **AI Tools Register** table in `README.md`.
   - Update the **Chapter 6 Coverage Checklist** in `README.md`.
5. **Log AI Failures**: Append any observed AI errors, hallucinations, unsafe kernel logic, syntax regressions, or suboptimal formulations to `FAILURE_LOG.md` with:
   - Description of the failure,
   - Why it failed,
   - The verified fix,
   - The lesson learned.
6. **5-Line Skeptical Critical Review**: Provide a concise 5-line critical evaluation assessing:
   - Potential latent bugs / edge-case risks,
   - Benchmark overfitting risks,
   - Computational or memory overheads,
   - Failure modes where the method underperforms,
   - Limitations of the current assumptions.
7. **Handoff & Review Checklist**: State clearly what commands the student must execute manually or what data must be pasted back, then pause and wait for the student's review and approval.
