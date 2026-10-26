# Prompt Log: Track E — Day 2 (Dataset Generation, Validator & Baselines)

## 1. Interaction Metadata
- **Date**: 2026-10-26
- **Tool / Assistant**: Gemini 3.8 Flash (High)
- **Track**: Track E (Main Real-Process Case Study: University Exam Timetabling)
- **Milestone**: Day 2 — Dataset Generation, Independent Validator, 10-Seed Baseline Benchmarking

---

## 2. Original User Prompt
```text
Day 2. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_E_case_study/.
1. Generate a synthetic dataset with a fixed seed: about 300 students, 40 courses, 12 slots, rooms with capacities, realistic enrollment (each student takes 4-6 courses). Also generate a scaling set (e.g. 100, 300, 1,000, 3,000 students). Document the generator and sizes. Tell me where to download a public Toronto exam-timetabling benchmark instance and add a parser for it.
2. Write an independent feasibility and objective checker (separate from any solver) with unit tests on hand-made tiny cases.
3. Implement the baselines: random schedule and first-fit. Report feasibility, clashes, back-to-back count, 3+ per day count, slots used, and runtime, over 10 seeds with mean and std. This is the evidence that the process needs optimization (Question 1).
4. Run DAILY CLOSE.
```

---

## 3. AI Response Summary & Excerpt
- Read `ASSIGNMENT_SPEC.md` and `PROJECT_RULES.md` completely.
- Implemented `track_E_case_study/code/dataset_generator.py` with departmental course clustering and fixed seed (42). Generated primary instance (300 students, 40 courses, 12 slots) and scaling instances (100, 300, 1000, 3000 students).
- Implemented `track_E_case_study/code/toronto_parser.py` supporting Carter et al. (1996) `.crs` and `.stu` benchmark formats, with download instructions from University of Nottingham and GitHub mirrors.
- Implemented `track_E_case_study/code/validator.py` as an independent verification engine checking assignment completeness, hard student clashes, venue capacity compliance, back-to-back exams on the same day, 3+ exams/day, and total penalty.
- Implemented `track_E_case_study/tests/test_validator.py` covering 5 tiny hand-crafted cases.
- Implemented `track_E_case_study/code/baselines.py` executing 10 repeated runs across seeds 0–9 for Random and Greedy First-Fit schedulers.
- Generated `results/baseline_summary.csv`, `results/baseline_experiments.json`, and `results/baseline_inefficiency_comparison.png`.
- Executed the 7-step Daily Close protocol.

---

## 4. Revisions & Corrections Made During Turn
- **AI Error Caught**: Direct execution of `python track_E_case_study/code/baselines.py` failed with `ModuleNotFoundError: No module named 'track_E_case_study'` due to Python's script directory resolution.
- **Correction**: Injected `sys.path` fallback dynamically pointing to repository root. Documented incident in `FAILURE_LOG.md` (Case 1).

---

## 5. Resulting Code Changes & Artifacts
- [`track_E_case_study/code/dataset_generator.py`](../../track_E_case_study/code/dataset_generator.py)
- [`track_E_case_study/code/toronto_parser.py`](../../track_E_case_study/code/toronto_parser.py)
- [`track_E_case_study/data/DATASET_DOCUMENTATION.md`](../../track_E_case_study/data/DATASET_DOCUMENTATION.md)
- [`track_E_case_study/code/validator.py`](../../track_E_case_study/code/validator.py)
- [`track_E_case_study/tests/test_validator.py`](../../track_E_case_study/tests/test_validator.py)
- [`track_E_case_study/code/baselines.py`](../../track_E_case_study/code/baselines.py)
- [`track_E_case_study/results/baseline_summary.csv`](../../track_E_case_study/results/baseline_summary.csv)
- [`track_E_case_study/results/baseline_experiments.json`](../../track_E_case_study/results/baseline_experiments.json)
- [`track_E_case_study/results/baseline_inefficiency_comparison.png`](../../track_E_case_study/results/baseline_inefficiency_comparison.png)
- [`track_E_case_study/REPORT.md`](../../track_E_case_study/REPORT.md)

---

## 6. Verification & Correctness Notes
- All 5 unit tests in `test_validator.py` passed with 100% success rate.
- Deterministic seeds 0..9 confirmed: exact reproducibility verified.
- Results confirmed zero feasibility for unoptimized baselines, establishing empirical baseline for Question 1.
