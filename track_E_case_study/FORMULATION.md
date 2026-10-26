# Track E: Main Case Study Problem Formulation
## University Examination Timetabling Optimization

> **Status**: Problem Formulation & Strategy Selection  
> **Course**: Optimization Techniques (Assignment 8)  
> **Problem Domain**: Educational Operations Research / Resource Scheduling  
> **Frameworks Tested**: Exact Integer Linear Programming (ILP) vs Constructive / Metaheuristic Search (Greedy + Simulated Annealing)

---

## 1. Process Description

University examination scheduling is a mission-critical, large-scale administrative process conducted at the conclusion of every academic semester. The university must schedule $|E|$ examinations for $|U|$ enrolled students across a finite planning horizon of $|D|$ days, with each day partitioned into $K$ standardized examination time slots (yielding a total set of available time slots $S = \{1, 2, \dots, |S|\}$ where $|S| = |D| \times K$). Furthermore, the institution has a finite examination hall seating capacity $C_{\text{max}}$ per time slot (or a set of examination venues $R$ with capacities $C_r$ such that $\sum_{r \in R} C_r = C_{\text{max}}$).

In most real-world academic institutions, timetabling has historically been managed through legacy ad-hoc heuristics, department-by-department spreadsheets, or greedy first-fit scheduling. This manual/unoptimized process results in substantial systemic friction:
1. **Severe Student Schedule Clashes**: Students enrolled in multidisciplinary, elective, or cross-departmental courses are vulnerable to overlapping exam slots, forcing emergency rescheduling or deferred examinations.
2. **Acute Academic Stress & Fatigue**: Suboptimal slot assignments cluster exams together, causing students to take back-to-back examinations on the same day (e.g., Morning slot followed immediately by Afternoon slot) or endure 3 or more examinations within a single 24-to-48 hour window.
3. **Severe Campus Resource Inefficiency**: Inefficient slot packing prolongs the required examination period, incurring substantial facility overheads (heating/air conditioning, venue rental, proctoring/invigilator labor hours, security) and delaying subsequent grading workflows.

---

## 2. Evidence-of-Inefficiency Plan

To prove that the existing process genuinely requires mathematical optimization (as demanded by Section 4 & Section 11 of the Assignment Specification), we establish an empirical audit protocol comparing an unoptimized operational baseline against optimized formulations.

### Empirical Audit Dimensions
1. **Hard Conflict Count**: Total instances where a student is double-booked into the same time slot:
   $$\text{Violations}_{\text{hard}} = \sum_{u \in U} \sum_{s \in S} \max\left(0, \sum_{e \in E_u} x_{e,s} - 1\right)$$
   *(In legacy manual scheduling, this is often greater than zero before manual patch-ups, or forces extended examination calendars).*
2. **Back-to-Back Student Fatigue**: Total count of occurrences where an individual student must sit two consecutive exams within the same calendar day:
   $$\text{Penalty}_{\text{b2b}} = \sum_{u \in U} \sum_{s \in S_{\text{adjacent}}} \left(\sum_{e \in E_u} x_{e,s}\right) \left(\sum_{e' \in E_u} x_{e', s+1}\right)$$
3. **Overload Days (3+ Exams in a Single Day)**: Count of student-day pairs where an individual student faces 3 or more examinations in one calendar day:
   $$\text{Penalty}_{\ge 3} = \sum_{u \in U} \sum_{d \in D} \max\left(0, \sum_{s \in S_d} \sum_{e \in E_u} x_{e,s} - 2\right)$$
4. **Calendar Footprint & Proctoring Overhead**: Total active slots used:
   $$\text{Active Slots} = \sum_{s \in S} \mathbb{I}\left(\sum_{e \in E} x_{e,s} > 0\right)$$
   Unoptimized baselines leave sporadic underutilized slots, prolonging facility rental and invigilation schedules by up to 30–50%.

### Verification Dataset
Experiments will be conducted on:
- A realistic synthetic university cohort modeled on realistic registrar parameters: $|U| = 800$ to $1,500$ students, $|E| = 40$ to $80$ courses, $|S| = 18$ slots (6 days $\times$ 3 slots/day), with realistic clustered major/minor course enrollment distributions.
- A standardized benchmark instance drawn from the International Timetabling Competition (ITC) / Toronto Examination Timetabling Benchmark suite.

---

## 3. Mathematical Formulation

### 3.1 Sets and Indices
- $E = \{1, 2, \dots, |E|\}$: Set of all courses / examinations.
- $S = \{1, 2, \dots, |S|\}$: Chronologically ordered set of available time slots.
- $D = \{1, 2, \dots, |D|\}$: Set of calendar days.
- $S_d \subset S$: Subset of time slots occurring on day $d \in D$. ($|S_d| = K$, typically $K=3$: Morning, Afternoon, Evening).
- $S_{\text{adjacent}} = \{s \in S \mid s+1 \in S \text{ and } day(s) = day(s+1)\}$: Set of consecutive slot pairs occurring on the same calendar day.
- $U = \{1, 2, \dots, |U|\}$: Set of all enrolled students.
- $E_u \subseteq E$: Set of examinations that student $u \in U$ is registered to sit.
- $C = \{(e_1, e_2) \in E \times E \mid e_1 < e_2 \text{ and } E_u \cap \{e_1, e_2\} = \{e_1, e_2\} \text{ for some } u \in U\}$: Set of conflicting exam pairs sharing at least one common enrolled student.
- $c_{e_1, e_2} = |\{u \in U \mid e_1 \in E_u \text{ and } e_2 \in E_u\}|$: Conflict weight (number of students enrolled in both exam $e_1$ and exam $e_2$).
- $n_e = |\{u \in U \mid e \in E_u\}|$: Total student enrollment in exam $e$.
- $C_{\text{max}}$: Aggregate campus examination seating capacity per time slot.

---

### 3.2 Decision Variables

1. **Primary Assignment Variable**:
   $$x_{e,s} \in \{0, 1\}, \quad \forall e \in E, \; \forall s \in S$$
   Where:
   $$x_{e,s} = \begin{cases} 1 & \text{if examination } e \text{ is assigned to time slot } s \\ 0 & \text{otherwise} \end{cases}$$

2. **Slot Utilization Variable**:
   $$y_s \in \{0, 1\}, \quad \forall s \in S$$
   Where:
   $$y_s = \begin{cases} 1 & \text{if time slot } s \text{ has at least one examination scheduled} \\ 0 & \text{otherwise} \end{cases}$$

3. **Auxiliary Linearization Variables (for ILP)**:
   - For back-to-back conflict linearization:
     $$z_{e_1, e_2, s} \in \{0, 1\}, \quad \forall (e_1, e_2) \in C, \; \forall s \in S_{\text{adjacent}}$$
     Indicating whether both conflicting exams $e_1$ and $e_2$ are placed in adjacent slots $s$ and $s+1$.
   - For daily overload linearization:
     $$v_{u, d} \ge 0, \quad \forall u \in U, \; \forall d \in D$$
     Representing the excess examinations beyond 2 taken by student $u$ on day $d$.

---

### 3.3 Hard Constraints (Feasibility Requirements)

Every valid examination timetable **must** strictly satisfy the following hard constraints:

1. **Complete & Unique Assignment**:
   Every exam $e$ must be scheduled into exactly one time slot:
   $$\sum_{s \in S} x_{e,s} = 1, \quad \forall e \in E$$

2. **No Student Conflicts (Clash-Free Scheduling)**:
   No student may be assigned to two examinations in the same time slot:
   $$\sum_{e \in E_u} x_{e,s} \le 1, \quad \forall u \in U, \; \forall s \in S$$
   *Equivalent conflict-graph representation*: For every pair of exams $(e_1, e_2) \in C$ sharing students ($c_{e_1, e_2} \ge 1$):
   $$x_{e_1, s} + x_{e_2, s} \le 1, \quad \forall (e_1, e_2) \in C, \; \forall s \in S$$

3. **Seating Capacity Constraint**:
   The total number of students sitting exams in slot $s$ cannot exceed the aggregate examination room capacity:
   $$\sum_{e \in E} n_e x_{e,s} \le C_{\text{max}} \cdot y_s, \quad \forall s \in S$$

4. **Slot Activation Coupling**:
   An exam can only be scheduled into slot $s$ if slot $s$ is activated:
   $$x_{e,s} \le y_s, \quad \forall e \in E, \; \forall s \in S$$

---

### 3.4 Soft Constraints & Objective Function

The objective function minimizes total penalty costs comprising student fatigue and institutional resource overhead:

$$\min Z = \alpha_1 Z_{\text{b2b}} + \alpha_2 Z_{\ge 3\text{/day}} + \alpha_3 Z_{\text{slots}}$$

#### Component 1: Back-to-Back Exam Penalty ($Z_{\text{b2b}}$)
Minimizes total student occurrences of consecutive exams on the same day:
$$Z_{\text{b2b}} = \sum_{(e_1, e_2) \in C} c_{e_1, e_2} \sum_{s \in S_{\text{adjacent}}} \left( x_{e_1, s} \cdot x_{e_2, s+1} + x_{e_2, s} \cdot x_{e_1, s+1} \right)$$
In linear ILP form:
$$Z_{\text{b2b}} = \sum_{(e_1, e_2) \in C} c_{e_1, e_2} \sum_{s \in S_{\text{adjacent}}} \left( z_{e_1, e_2, s} + z_{e_2, e_1, s} \right)$$
Subject to the McCormick linearization constraints:
$$z_{e_1, e_2, s} \ge x_{e_1, s} + x_{e_2, s+1} - 1, \quad z_{e_1, e_2, s} \ge 0, \quad \forall (e_1, e_2) \in C, \; s \in S_{\text{adjacent}}$$

#### Component 2: Daily Overload Penalty ($Z_{\ge 3\text{/day}}$)
Penalizes students scheduled for 3 or more examinations in a single calendar day:
$$Z_{\ge 3\text{/day}} = \sum_{u \in U} \sum_{d \in D} v_{u, d}$$
Subject to:
$$v_{u, d} \ge \left( \sum_{s \in S_d} \sum_{e \in E_u} x_{e,s} \right) - 2, \quad v_{u, d} \ge 0, \quad \forall u \in U, \; \forall d \in D$$

#### Component 3: Total Resource / Slot Footprint Penalty ($Z_{\text{slots}}$)
Encourages compact, efficient scheduling to minimize operational days and invigilation expenses:
$$Z_{\text{slots}} = \sum_{s \in S} \beta_s \, y_s$$
Where $\beta_s$ can be a monotonically increasing weight $\beta_s = 1 + \epsilon \cdot s$ to naturally pull exams toward earlier slots and free up later days entirely.

#### Priority Weighting
Typical academic weighting: $\alpha_1 = 10.0$ (high penalty per back-to-back student), $\alpha_2 = 50.0$ (very high penalty for 3 exams in one day), $\alpha_3 = 5.0$ (operational slot cost).

---

## 4. Key Assumptions

1. **Fixed Durations**: All exams fit cleanly within standardized slot durations (e.g., 2.5 hours per slot).
2. **Deterministic Enrolments**: Student enrollment records are finalized and static prior to solving.
3. **Room Pooling**: Aggregate seating capacity $C_{\text{max}}$ is enforced during slot assignment; individual room allocation is a polynomial-time bipartite matching post-processing step.
4. **Deterministic Travel**: All examination halls are located on the same primary university campus; transit between rooms during adjacent slots is negligible.

---

## 5. Evaluation Metrics

| Metric | Mathematical Definition | Ideal Target |
| :--- | :--- | :--- |
| **Hard Constraint Violations** | $\sum_{u, s} \max(0, \sum_{e \in E_u} x_{e,s} - 1) + \sum_{s} \max(0, \sum_e n_e x_{e,s} - C_{\text{max}})$ | **Strictly 0** |
| **Back-to-Back Count** | $\sum_{(e_1, e_2) \in C} c_{e_1, e_2} \sum_{s \in S_{\text{adjacent}}} (x_{e_1, s} x_{e_2, s+1} + x_{e_2, s} x_{e_1, s+1})$ | Minimize ($\to 0$) |
| **3+ Exams in a Day Count** | $\sum_{u, d} \max(0, \sum_{s \in S_d, e \in E_u} x_{e,s} - 2)$ | **Strictly 0** |
| **Total Slots Utilized** | $\sum_{s \in S} y_s$ | Compact packing ($\le 12$ slots) |
| **Solver Solve Time (s)** | Measured wall-clock runtime to reach optimality / stopping criterion | $< 60$ s |
| **Optimality Gap (%)** | $\frac{|\text{Objective} - \text{Lower Bound}|}{\text{Objective}} \times 100\%$ | $0.0\%$ (exact) / $< 5\%$ |

---

## 6. Strategy-Selection Table

Per Section 4 and Section 6 of the Assignment Specification, optimization methods must be systematically evaluated and justified based on variable types, scale, exactness, hardware requirements, and parallelizability:

| Strategy / Method | Variable Type | Problem Size Capacity | Exact vs Heuristic | Hardware Requirements | Parallelism Potential | Selection Verdict for Track E |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Greedy First-Fit (Baseline)** | Discrete / Categorical | $O(\|E\| \cdot \|S\|)$, virtually unlimited | Heuristic (Constructive) | Minimal CPU ($< 10$ MB RAM) | Trivially parallelizable across independent splits | **Selected as Operational Baseline**: Fast, but creates severe soft penalties and clashes under tight capacity. |
| **Integer Linear Programming (ILP)** | Binary $x_{e,s} \in \{0, 1\}$ | Up to $\approx 10^4$ variables, $10^5$ constraints | Exact (Branch-and-Cut) | Moderate CPU / Multi-core ($1$–$4$ GB RAM) | Multi-threaded tree search (Branch-and-Bound LP relaxations) | **Selected as Primary Exact Method**: Guarantees zero hard violations and mathematically provable optimality bounds. |
| **Simulated Annealing / ALNS** | Permutation / Discrete state | Large ($> 10^5$ variables) | Stochastic Metaheuristic | Low CPU ($< 100$ MB RAM) | Parallel independent restart chains / Island models | **Selected as Comparative Heuristic**: Highly scalable, explores non-convex discrete landscape, avoids memory explosion. |
| **Continuous Relaxation + Rounding (LP)** | Continuous $x_{e,s} \in [0, 1]$ | Very large | Approximation / Heuristic | Standard CPU | Highly parallel interior-point / simplex solvers | *Rejected for primary*: Fractional exam assignments require complex hypergraph rounding; often violates hard clashes. |
| **QUBO / QAOA (Quantum)** | Binary spin $\{-1, 1\}$ | $< 40$ variables on current NISQ simulators | Heuristic / Variational | High (Quantum simulator or QPU access) | Classical parameter optimization parallelizable; QPU is sequential shots | *Rejected for Track E main solver*: Embedding $O(\|E\| \cdot \|S\|)$ binary variables exceeds physical/simulated qubit limits (reserved for Track B/C/I). |

---

## 7. Comparative Experimental Plan

In accordance with Section 6 (Track E requirements):
1. **Method 1 (Baseline)**: Constructive Greedy Heuristic with Largest-Degree-First (LDF) graph ordering.
2. **Method 2 (Exact Chapter 6 Method)**: Integer Linear Programming (ILP) with branch-and-cut solver (CBC/SCIP via PuLP).
3. **Method 3 (Stochastic Metaheuristic)**: Simulated Annealing with adaptive neighborhood operators (Kempe chain slot swaps).
4. **Controlled Evaluation**: All three methods execute on identical student enrollment conflict graphs, enforce identical seating capacity limits, and report solution quality across runtime budgets (1s, 5s, 30s, 60s).
