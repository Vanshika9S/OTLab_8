# Viva Cheat-Sheet: Key Concepts, Functions & Likely Questions
## Assignment 8: Optimize Anything (Tracks A through J)

> **Purpose**: Essential review guide for live oral defense and code-modification examination.  
> **Rule**: You must be able to explain every line, identify invariants, and modify parameters live without AI assistance.

---

# Track A: Continuous Optimization & Loss Landscapes

### Key Functions to Explain & Modify
- [`track_A_continuous/code/continuous_optimizers.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_A_continuous/code/continuous_optimizers.py):
  - `AdamOptimizer.step(grad)`: Updates first moment $m_t$ and second raw moment $v_t$, applies bias corrections $\hat{m}_t = \frac{m_t}{1-\beta_1^t}, \hat{v}_t = \frac{v_t}{1-\beta_2^t}$, and steps $\theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{\hat{v}_t}+\epsilon}\hat{m}_t$.
  - `NewtonRaphson.step(grad, hessian)`: Inverts or solves $H \Delta \theta = \nabla f$ with damping $\lambda I$ to prevent singularity.
- [`track_A_continuous/code/neural_net_backprop.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_A_continuous/code/neural_net_backprop.py):
  - `backward(x, y)`: Hand-derived analytical Jacobian backprop with chain rule.

### Algorithmic Invariants
1. In Newton's method, if the Hessian is not positive definite (e.g. at a saddle point where eigenvalues are negative), pure Newton steps in an ascent direction. Damping or trust-region modifications are required.
2. In Adam, bias corrections prevent severe step-size suppression during the initial iterations ($t \to 1$).

### Likely Viva Questions & Model Answers
1. **Q: Why does standard Newton-Raphson fail or diverge near a saddle point like $f(x, y) = x^2 - y^2$?**  
   *Answer*: At a saddle point, the Hessian matrix has both positive and negative eigenvalues (indefinite). The standard update $\Delta \theta = -H^{-1} \nabla f$ follows the negative curvature direction upward rather than downward, causing divergence. We resolve this by adding Levenberg-Marquardt damping $(H + \lambda I)$ to enforce positive definiteness.
2. **Q: How does Nesterov Accelerated Gradient (NAG) differ mathematically from classical Polyak momentum?**  
   *Answer*: Classical momentum computes the gradient at the current position $\theta_t$ and adds decayed velocity: $v_{t+1} = \gamma v_t + \eta \nabla f(\theta_t)$. NAG computes the gradient at the "lookahead" point $\theta_t - \gamma v_t$: $v_{t+1} = \gamma v_t + \eta \nabla f(\theta_t - \gamma v_t)$, acting as an anticipatory brake that reduces overshooting in narrow curved valleys like Rosenbrock.
3. **Q: What is the computational advantage of computing Hessian-Vector Products (HVP) over instantiating the full Hessian?**  
   *Answer*: For dimension $d$, storing and inverting the explicit Hessian requires $\mathcal{O}(d^2)$ memory and $\mathcal{O}(d^3)$ compute. An HVP computes the directional derivative $[H v] = \lim_{\epsilon \to 0} \frac{\nabla f(\theta + \epsilon v) - \nabla f(\theta)}{\epsilon}$ using only two gradient evaluations in $\mathcal{O}(d)$ time and space without storing the matrix.

---

# Track B: Discrete Optimization & QUBO Formulations

### Key Functions to Explain & Modify
- [`track_B_discrete/code/knapsack_solvers.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_B_discrete/code/knapsack_solvers.py):
  - `knapsack_branch_and_bound(...)`: Explores binary decision tree pruning subtrees whose fractional continuous relaxation upper bound is $\le \text{best\_val}$.
  - `knapsack_dp(...)`: Tabulates 2D state $DP[i][w] = \max(DP[i-1][w], DP[i-1][w-w_i] + v_i)$.
- [`track_B_discrete/code/qubo_maxcut.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_B_discrete/code/qubo_maxcut.py):
  - `build_maxcut_qubo(edges, num_nodes)`: Constructs matrix $Q$ where diagonal is $-\text{deg}(i)$ and off-diagonals are $+2 A_{ij}$.

### Algorithmic Invariants
1. In 0-1 Knapsack Branch-and-Bound, sorting items by density $v_i/w_i$ in descending order guarantees that the greedy linear relaxation provides a valid, tight upper bound for pruning.

### Likely Viva Questions & Model Answers
1. **Q: How do you transform a binary 0-1 decision variable $x_i \in \{0, 1\}$ into an Ising spin variable $s_i \in \{-1, +1\}$?**  
   *Answer*: We apply the affine transformation $x_i = \frac{1 - s_i}{2}$. When $s_i = +1$, $x_i = 0$; when $s_i = -1$, $x_i = 1$. Substituting this into quadratic terms $x_i x_j$ yields $\frac{1 - s_i - s_j + s_i s_j}{4}$, converting the QUBO matrix into an Ising Hamiltonian with $J_{ij} s_i s_j$ interaction couplings and local magnetic fields $h_i s_i$.
2. **Q: Why is Dynamic Programming considered pseudo-polynomial for the 0-1 Knapsack problem?**  
   *Answer*: The time complexity is $\mathcal{O}(n W)$, where $W$ is the integer capacity. The input size of $W$ in binary representation is $\log_2(W)$ bits. Thus, the running time is exponential in the input bit-length $\mathcal{O}(n \cdot 2^b)$, which is not polynomial unless $W$ is bounded by a polynomial in $n$.
3. **Q: How are hard equality constraints $A x = b$ enforced in an unconstrained QUBO?**  
   *Answer*: We incorporate a quadratic penalty term $\lambda \|A x - b\|_2^2 = \lambda (x^T A^T A x - 2 b^T A x + b^T b)$ directly into the objective function. The penalty multiplier $\lambda > 0$ must be sufficiently large to ensure that any infeasible state has a higher energy than all feasible states.

---

# Track C: Quantum Optimization & Hybrid QAOA

### Key Functions to Explain & Modify
- [`track_C_quantum/code/qaoa_maxcut.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_C_quantum/code/qaoa_maxcut.py):
  - `qaoa_circuit(gamma, beta)`: Applies Hadamard layer $H^{\otimes n}$, alternating cost unitary $e^{-i \gamma C}$ ($R_{ZZ}$ rotations), and mixer unitary $e^{-i \beta B}$ ($R_X$ rotations).
- [`track_C_quantum/code/gradients.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_C_quantum/code/gradients.py):
  - `parameter_shift_gradient(circuit, params, shift=np.pi/2)`: Computes exact analytical gradient $\frac{\langle H \rangle_{\theta + \pi/2} - \langle H \rangle_{\theta - \pi/2}}{2}$.

### Algorithmic Invariants
1. The transverse mixer Hamiltonian $H_M = \sum_i X_i$ does not commute with the cost Hamiltonian $H_C = \sum_{(u, v)} Z_u Z_v$. Alternating them allows quantum tunneling between candidate states.

### Likely Viva Questions & Model Answers
1. **Q: What is the parameter-shift rule and why is it superior to finite differences on real quantum hardware?**  
   *Answer*: Finite differences compute $\frac{f(\theta + \epsilon) - f(\theta)}{\epsilon}$ with small $\epsilon \ll 1$. On noisy quantum processors with finite shot noise, dividing by small $\epsilon$ amplifies measurement variance by $\mathcal{O}(1/\epsilon^2)$. The parameter-shift rule evaluates at macro shifts $\pm \pi/2$ and yields the exact analytical quantum gradient with bounded shot variance.
2. **Q: What is a barren plateau, and how does gradient variance scale with qubit count?**  
   *Answer*: In deep random parameterized quantum circuits, the Haar measure causes the gradient of the expectation value to concentrate exponentially around zero. By McClean et al.'s theorem, $\text{Var}[\partial_\theta \langle H \rangle] \in \mathcal{O}(2^{-n})$ or $\mathcal{O}(1/b^n)$. In our Track C experiments, variance dropped from $0.125$ at $n=2$ to $0.0019$ at $n=8$.
3. **Q: What would change if your QAOA code was executed on physical superconducting hardware instead of a simulator?**  
   *Answer*: On physical hardware (e.g. IBM Eagle), two-qubit CNOT gates have error rates of $0.5\% - 2\%$, coherence times $T_1, T_2$ are finite (~$100\mu\text{s}$), and all-to-all connectivity does not exist, requiring SWAP gate insertion. Furthermore, expectation values must be estimated through finite shot sampling (e.g., 4096 shots), introducing statistical projection noise $\mathcal{O}(1/\sqrt{\text{shots}})$.

---

# Track D: Submodular, Parallel & Distributed Optimization

### Key Functions to Explain & Modify
- [`track_D_submodular_parallel/code/submodular_max.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_D_submodular_parallel/code/submodular_max.py):
  - `greedy_submodular_selection(ground_set, k, objective_fn)`: Repeatedly selects $e^* = \arg\max_{e \notin S} (F(S \cup \{e\}) - F(S))$.
- [`track_D_submodular_parallel/code/parallel_work_stealing.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_D_submodular_parallel/code/parallel_work_stealing.py):
  - `WorkerThread.run()`: Pops tasks from local double-ended queue (LIFO); when empty, steals tasks from victim queues (FIFO) to balance makespan.
- [`track_D_submodular_parallel/code/fedavg_simulation.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_D_submodular_parallel/code/fedavg_simulation.py):
  - `aggregate_models(client_models, client_weights)`: Computes weighted average $w_{t+1} = \sum_{k=1}^K \frac{n_k}{n} w_{t+1}^k$.

### Algorithmic Invariants
1. Diminishing returns property: $F(A \cup \{x\}) - F(A) \ge F(B \cup \{x\}) - F(B)$ for all $A \subseteq B$. If this is violated, the $(1 - 1/e)$ approximation guarantee does not hold.

### Likely Viva Questions & Model Answers
1. **Q: Under what conditions does the greedy algorithm guarantee a $(1 - 1/e)$ approximation for submodular maximization?**  
   *Answer*: The objective function $F(S)$ must be: (1) submodular (satisfying diminishing returns), (2) monotone ($A \subseteq B \implies F(A) \le F(B)$), and (3) normalized ($F(\emptyset) = 0$), constrained by a uniform cardinality matroid $|S| \le k$.
2. **Q: How does Amdahl's Law differ from Gustafson's Law when evaluating parallel speedup?**  
   *Answer*: Amdahl's Law assumes a fixed problem size; as cores $P \to \infty$, speedup is bounded by $\frac{1}{s + (1-s)/P} \le \frac{1}{s}$, where $s$ is the serial fraction. Gustafson's Law assumes the problem size scales with available processors (weak scaling); speedup is given by $S(P) = P - s(P-1)$, which scales linearly with $P$.
3. **Q: Why does client drift occur in FedAvg under Non-IID data distributions, and how is it mitigated?**  
   *Answer*: When client data distributions $P_k(x, y)$ differ, local SGD steps optimize client-specific empirical losses $F_k(w)$, drifting local model weights toward local minima away from the global objective $\sum p_k F_k(w)$. This is mitigated by reducing local epochs $E$, or applying proximal penalties like FedProx $\frac{\mu}{2}\|w - w^t\|^2$.

---

# Track E: Main Case Study (University Exam Timetabling)

### Key Functions to Explain & Modify
- [`track_E_case_study/code/dsatur_solver.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_E_case_study/code/dsatur_solver.py):
  - `solve_dsatur(...)`: Dynamically computes saturation degree (count of unique timeslots assigned to conflicting neighbors) and colors the highest-saturation vertex first.
- [`track_E_case_study/code/ilp_solver.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_E_case_study/code/ilp_solver.py):
  - `build_milp_model(...)`: Encodes decision variables $x_{e, t, r}$ into sparse constraint matrix `coo_matrix` to prevent memory exhaustion, invoking `scipy.optimize.milp`.
- [`track_E_case_study/code/validator.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_E_case_study/code/validator.py):
  - `validate_schedule(...)`: Independent audit checking 0 clashes, 0 room overlaps, and calculating soft penalties.

### Algorithmic Invariants
1. Room exclusivity constraint: In any timeslot $t$, room $r$ can host at most one exam: $\sum_e x_{e, t, r} \le 1$.
2. Student clash constraint: If student $s$ is enrolled in both exam $e_1$ and $e_2$, then $x_{e_1, t, \cdot} + x_{e_2, t, \cdot} \le 1$ for all $t$.

### Likely Viva Questions & Model Answers
1. **Q: Why did exact ILP solve the 30-exam instance in 148 ms but time out on the Toronto `sta83` instance (139 exams)?**  
   *Answer*: The binary decision space scales as $|E| \times |T| \times |R|$. For 30 exams, 8 slots, 4 rooms, there are 960 binary variables. For `sta83` (139 exams, 13 slots, 10 rooms), there are $>18,000$ binary variables and hundreds of thousands of student conflict cuts. Branch-and-bound exhibits worst-case exponential complexity $\mathcal{O}(2^V)$, causing combinatorial explosion without aggressive domain-specific heuristics.
2. **Q: How does DSATUR determine which exam to schedule next?**  
   *Answer*: DSATUR (Degree of Saturation) calculates the number of different timeslots already used by an exam's conflicting neighbors. At each step, it selects the unscheduled exam with the highest saturation degree (the most constrained exam). In the case of a tie, it chooses the vertex with the highest degree in the uncolored subgraph.
3. **Q: In your parallel Simulated Annealing implementation, how do you prevent race conditions between the 6 workers?**  
   *Answer*: We use independent parallel restarts. Each CPU process runs an isolated instance of simulated annealing with a distinct random seed and private memory space using Python's `multiprocessing.Pool`. There is no shared memory or lock contention during annealing; workers simply return their best schedules at the end, and the master process selects the minimum-penalty feasible schedule.

---

# Track F: Compiler Optimization Passes & Register Allocation

### Key Functions to Explain & Modify
- [`track_F_compiler/code/passes.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_F_compiler/code/passes.py):
  - `dead_code_elimination(cfg)`: Iterates backward dataflow equations $\text{In}[B] = \text{Use}[B] \cup (\text{Out}[B] \setminus \text{Def}[B])$ until convergence, pruning dead instructions.
  - `loop_invariant_code_motion(cfg)`: Computes dominator tree; hoists definitions whose operands are invariant outside loop pre-headers.
- [`track_F_compiler/code/reg_alloc.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_F_compiler/code/reg_alloc.py):
  - `ilp_register_allocation(interference_graph, num_registers)`: Solves graph coloring ILP minimizing memory spill stores.

### Algorithmic Invariants
1. In Loop-Invariant Code Motion, an instruction $t = a + b$ can only be hoisted out of a loop if its definition dominates all loop exits and variable $t$ is not redefined elsewhere in the loop.

### Likely Viva Questions & Model Answers
1. **Q: Why does dead-code elimination require CFG liveness analysis rather than a simple top-to-bottom linear scan?**  
   *Answer*: A linear scan cannot handle loops or backwards control-flow edges. In a loop, a variable defined at line 10 might be read at line 5 in the next iteration. CFG iterative liveness analysis propagates $\text{Out}[B] = \bigcup_{S \in \text{succ}(B)} \text{In}[S]$ until a fixed point is reached, ensuring no variable needed in subsequent iterations is incorrectly removed.
2. **Q: How does graph-coloring register allocation map to an Integer Linear Program?**  
   *Answer*: Each virtual variable is a vertex; overlapping live ranges create interference edges $(u, v) \in E$. Binary variable $x_{v, r} = 1$ indicates assigning variable $v$ to physical register $r \in \{1, \dots, K\}$. The constraint $x_{u, r} + x_{v, r} \le 1$ ensures conflicting variables never share the same register. If $K$ is insufficient, spill indicator $y_v \in \{0, 1\}$ incurs a memory traffic penalty in the objective $\sum \text{Cost}(v) \cdot y_v$.
3. **Q: Give an example where an aggressive optimization pass could change program semantics if not carefully checked.**  
   *Answer*: Constant folding an expression like `x = 10 / 0` at compile time would eliminate a runtime division-by-zero exception. Similarly, dead-code eliminating `unused = print("Log")` would remove a critical side effect. Optimization passes must verify that candidate instructions are pure (side-effect free) before pruning or reordering.

---

# Track G: xv6 Operating-System Scheduling Optimization

### Key Functions to Explain & Modify
- [`track_G_xv6/code/xv6_lottery_scheduler.patch`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/xv6_lottery_scheduler.patch):
  - `scheduler(void)` in `kernel/proc.c`: Sums tickets of `RUNNABLE` processes, draws random ticket, and dispatches the winner.
  - `settickets(int number)`: Syscall setting process tickets, validating $n \ge 1$.
  - `getpstat(uint64 addr)`: Syscall copying `struct pstat` to user space via `copyout`.

### Algorithmic Invariants
1. `p->lock` invariant: The scheduler must hold `p->lock` when changing `p->state = RUNNING` and calling `swtch(&c->context, &p->context)`. The lock is released on the target process stack inside `sched()`.

### Likely Viva Questions & Model Answers
1. **Q: What fatal kernel bug would occur if `settickets()` accepted negative ticket numbers?**  
   *Answer*: If a process holds negative tickets (e.g. -10), the total ticket sum $T_{\text{total}} = \sum T_p$ would decrease. If $T_{\text{total}} \le 0$, the pseudo-random generator `pseudo_rand(total_tickets)` triggers division by zero or negative bounds, causing an unhandled kernel panic and crashing the OS.
2. **Q: Why does xv6 hold `p->lock` across the `swtch()` context switch?**  
   *Answer*: To avoid race conditions where another CPU core sees `p->state == RUNNABLE` before the current CPU has finished saving its register state to `p->context`. Holding `p->lock` guarantees mutual exclusion until the context switch is completely finalized.
3. **Q: What is the main weakness of Lottery Scheduling compared to Stride Scheduling?**  
   *Answer*: Lottery scheduling is probabilistic; over short time horizons ($< 50$ ticks), random variance causes deviations from true proportional shares, leading to response time jitter. Stride Scheduling is a deterministic proportional-share algorithm using pass values $\text{pass} += \frac{\text{LargeConstant}}{\text{tickets}}$ in a priority queue, achieving zero variance.

---

# Track H: DBMS Workload Optimization & Index Selection

### Key Functions to Explain & Modify
- [`track_H_dbms/code/index_optimizer.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_H_dbms/code/index_optimizer.py):
  - `solve_index_knapsack_ilp(candidates, budget_kb)`: Solves 0-1 Knapsack via HiGHS ILP maximizing query benefit under B-tree storage budget.
- [`track_H_dbms/code/join_optimizer.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_H_dbms/code/join_optimizer.py):
  - `system_r_join_order(relations, join_predicates)`: Uses dynamic programming to find optimal left-deep join trees using intermediate cardinality estimates.

### Algorithmic Invariants
1. Correctness invariant: Every query plan must return an identical result set. Verified by hashing sorted rows: $\text{MD5}(\text{Rows}_{\text{unindexed}}) == \text{MD5}(\text{Rows}_{\text{indexed}})$.

### Likely Viva Questions & Model Answers
1. **Q: Why can't we simply build indexes on all columns of every table?**  
   *Answer*: B-tree indexes consume storage and must be updated synchronously on every `INSERT`, `UPDATE`, and `DELETE`. In our Track H write-cost benchmark, adding 5 indexes accelerated read queries by $84.45\%$ but reduced insert throughput by **$41.3\%$** due to B-tree node splits and disk write amplification.
2. **Q: How does System R Dynamic Programming determine join order?**  
   *Answer*: It uses bottom-up memoization over relations $S$. It first determines the cheapest access path for each single relation, then evaluates 2-way joins $C(\{R_1, R_2\}) = \min(R_1 \bowtie R_2, R_2 \bowtie R_1)$, pruning suboptimal sub-plans. It iterates up to $N$-way joins, pruning Cartesian products using join predicate availability.
3. **Q: How did you estimate the storage size of candidate indexes without PostgreSQL's `pg_relation_size`?**  
   *Answer*: In SQLite, we tracked physical database growth before and after index creation using `PRAGMA page_count` and `PRAGMA page_size` (4,096 bytes/page), accounting for free pages via `PRAGMA freelist_count`.

---

# Track I: Quantum Algorithms & Advantage

### Key Functions to Explain & Modify
- [`track_I_quantum_advantage/code/quantum_algorithms.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/code/quantum_algorithms.py):
  - `grover_search(target_index, num_qubits)`: Implements phase inversion oracle $I - 2|w\rangle\langle w|$ and diffusion operator $2|s\rangle\langle s| - I$, applying optimal rotation count $R = \lfloor \frac{\pi}{4}\sqrt{N} \rfloor$.
  - `qpe_algorithm(eigenphase, precision_qubits)`: Implements Quantum Phase Estimation using Hadamard gates, controlled-$U^{2^j}$ phase kickbacks, and inverse QFT.

### Algorithmic Invariants
1. Grover optimal rotation count: The angle between uniform superposition $|s\rangle$ and target state $|w\rangle$ is $\theta \approx 2/\sqrt{N}$. Each Grover iteration rotates the state vector by $2\theta$. To reach $\pi/2$ ($100\%$ target amplitude), the required iterations are $R \approx \frac{\pi/2}{2\theta} = \frac{\pi}{4}\sqrt{N}$. Exceeding this causes amplitude over-rotation and destroys success probability.

### Likely Viva Questions & Model Answers
1. **Q: Why was Grover search 60 times slower in wall-clock time on your laptop than linear search, despite evaluating fewer queries?**  
   *Answer*: Grover's algorithmic advantage is strictly in oracle query complexity ($\mathcal{O}(\sqrt{N})$ vs $\mathcal{O}(N)$). Simulating a quantum circuit on a classical CPU requires tracking a statevector of size $2^n$ complex amplitudes and multiplying $2^n \times 2^n$ unitary matrices. At $N=256$, classical linear search is simple memory iteration ($0.0004\text{ s}$), while quantum statevector simulation requires tens of thousands of floating-point operations ($0.024\text{ s}$).
2. **Q: How does phase kickback work in the Deutsch-Jozsa and Bernstein-Vazirani algorithms?**  
   *Answer*: An ancillary qubit is initialized in the state $|-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$. When an oracle performs $|x\rangle |y\rangle \to |x\rangle |y \oplus f(x)\rangle$, acting on $|-\rangle$ produces $(-1)^{f(x)} |x\rangle |-\rangle$. The function evaluation $f(x)$ is "kicked back" as a relative phase shift onto the input register $|x\rangle$, enabling constructive and destructive interference via Hadamard transforms.
3. **Q: In Shor's algorithm, how does Quantum Phase Estimation find prime factors of $N$?**  
   *Answer*: Factoring $N$ reduces to finding the order $r$ of a random coprime $a < N$ such that $a^r \equiv 1 \pmod{N}$. QPE applied to the unitary operator $U |y\rangle = |a y \pmod{N}\rangle$ recovers the eigenphase $\theta = s/r$. Continued fraction expansion reveals $r$. If $r$ is even, $\gcd(a^{r/2} \pm 1, N)$ yields non-trivial factors with high probability.

---

# Track J: Software-Engineering Bottleneck Optimization

### Key Functions to Explain & Modify
- [`track_J_software_eng/code/test_suite_optimizer.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_J_software_eng/code/test_suite_optimizer.py):
  - `minimize_suite_ilp(...)`: Formulates Weighted Set Cover as binary integer program $\min \sum c_j x_j$ subject to $A x \ge 1$ using `scipy.optimize.milp`.
  - `minimize_suite_greedy(...)`: Implements Chvátal's greedy heuristic, selecting tests maximizing uncovered statements per millisecond $\frac{|\text{Cov}(t) \setminus U_{\text{covered}}|}{\text{duration}(t)}$.

### Algorithmic Invariants
1. Full coverage preservation: The constraint matrix enforces that every statement $s_i$ must be covered by at least one selected test: $\sum_{j: s_i \in \text{Cov}(t_j)} x_j \ge 1$.

### Likely Viva Questions & Model Answers
1. **Q: What is the theoretical approximation ratio of Chvátal's Greedy Weighted Set Cover algorithm?**  
   *Answer*: Chvátal's greedy algorithm achieves an approximation ratio of $H_n = \sum_{k=1}^n \frac{1}{k} \le \ln(n) + 1$, where $n$ is the number of statements (elements to cover). In our Track J empirical benchmarks, greedy achieved a $24.28\%$ runtime reduction, whereas exact HiGHS ILP achieved a **$34.40\%$ reduction**.
2. **Q: What is mutation testing, and why is high statement coverage not sufficient by itself to prove test suite quality?**  
   *Answer*: Statement coverage only measures whether a line of code was executed; it does not measure whether assertions verify the output. Mutation testing injects artificial syntax faults (mutants), such as swapping `<` to `<=`, modifying return values, or inverting boolean conditions. If a test fails when the mutant is introduced, the mutant is "killed". High statement coverage with a low mutation score indicates weak or missing test assertions.
3. **Q: What trade-off is introduced when you replace a full regression test suite with an ILP-minimized test suite?**  
   *Answer*: The primary trade-off is fault localization and diagnostic granularity. In a full suite, if a regression bug is introduced, 5 different tests might fail simultaneously, pinpointing the root cause across different calling contexts. In a minimized suite, only 1 test might cover that statement, providing less immediate diagnostic information to the developer upon failure.
