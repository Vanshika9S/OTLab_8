# Track E: Examination Timetabling Dataset Documentation

This document describes the synthetic dataset generator and the public benchmark instance suite for the University Examination Timetabling optimization problem.

---

## 1. Synthetic Dataset Architecture

The generator in [`dataset_generator.py`](../code/dataset_generator.py) creates realistic university enrollment networks by modeling student academic majors and departmental structures.

### Generation Logic:
1. **Academic Department Clustering**:
   - Courses are partitioned into departments (e.g., Computer Science, Electrical Engineering, Mathematics, Humanities).
   - Each student is assigned a primary major and enrolls in 3–4 courses from their major department.
   - The student completes their study plan with 1–2 elective courses from other departments.
   - Total courses per student is bounded between **4 and 6**.
   - This replicates realistic academic co-enrollment: dense clique-like conflicts within disciplines and sparser cross-departmental edges.
2. **Venues and Seating Capacities**:
   - Each time slot has a finite physical seating capacity $C_{\text{max}} = \sum_{r \in R} C_r$.
   - Prevents unconstrained overbooking of examination halls.
3. **Reproducibility**:
   - Fixed random seeds are used throughout.

---

## 2. Generated Benchmark Datasets

| Dataset File | Students ($|U|$) | Courses ($|E|$) | Slots ($|S|$) | Days ($|D|$) | Slot Capacity ($C_{\text{max}}$) | Conflict Edges | Graph Density | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`synthetic_primary_300.json`](./synthetic_primary_300.json) | 300 | 40 | 12 | 4 | 300 seats | 740 | 0.9487 | **Primary Reference Benchmark** |
| [`synthetic_scale_100.json`](./synthetic_scale_100.json) | 100 | 40 | 12 | 4 | 100 seats | 563 | 0.7218 | Scaling Study: Small cohort |
| [`synthetic_scale_300.json`](./synthetic_scale_300.json) | 300 | 40 | 12 | 4 | 300 seats | 740 | 0.9487 | Scaling Study: Baseline |
| [`synthetic_scale_1000.json`](./synthetic_scale_1000.json) | 1,000 | 40 | 12 | 4 | 1,000 seats | 780 | 1.0000 | Scaling Study: Dense medium campus |
| [`synthetic_scale_3000.json`](./synthetic_scale_3000.json) | 3,000 | 40 | 12 | 4 | 3,000 seats | 780 | 1.0000 | Scaling Study: Large university |

---

## 3. Public Toronto Benchmark (Carter et al. 1996)

To test on real-world historical university examination data, use [`toronto_parser.py`](../code/toronto_parser.py).

### How to Download:
Download the benchmark instances from:
- **University of Nottingham Operational Research Archive**:  
  `http://www.cs.nott.ac.uk/~pszrq/data.htm`
- **GitHub Benchmark Repository**:  
  `https://github.com/chkwon/exam-timetabling-benchmark`

### Instance Reference:
- `hec-s-92`: 81 exams, 2,823 students, 18 slots (Compact business school instance).
- `ear-f-83`: 190 exams, 1,125 students, 24 slots (High school / college instance).
- `sta-f-83`: 139 exams, 611 students, 13 slots (Dense university instance).
- Place `<instance>.crs` and `<instance>.stu` in `track_E_case_study/data/toronto/` and call:
  ```python
  from track_E_case_study.code.toronto_parser import parse_toronto_instance
  instance = parse_toronto_instance("track_E_case_study/data/toronto/hec-s-92.crs", "track_E_case_study/data/toronto/hec-s-92.stu")
  ```
