# Track D: Submodular, Parallel, and Distributed Optimization — Report

## 1. Objective
1. **Submodular Optimization**: Verify diminishing returns mathematically and empirically; test greedy selection and verify theoretical $(1 - 1/e)$ approximation conditions.
2. **Parallel Program Optimization**: Benchmark multi-core scaling (load balancing, work stealing, data/model/pipeline parallelism); measure speedup and efficiency; interpret with Amdahl's and Gustafson's laws.
3. **Distributed & Multi-Task Optimization**: Compare Federated Averaging (FedAvg) against centralized optimization across communication rounds and local steps; compare MGDA and GradNorm against equal task weighting in a multi-task learning setting.

## 2. Algorithms Tested
- **Submodular**: Greedy forward selection on coverage/information gain objective.
- **Parallel**: Multiprocessing pool / threaded work-stealing queue benchmarked across core counts (1, 2, 4, 8 cores).
- **Distributed**: Federated Averaging (`FedAvg`) with non-IID client partitions.
- **Multi-Task**: Multiple Gradient Descent Algorithm (MGDA) & Gradient Normalization (GradNorm) vs naive uniform scalarization.

## 3. Baseline
- Submodular: Random selection or naive thresholding.
- Parallel: Single-threaded sequential execution.
- Distributed/Multi-task: Standard centralized training and uniform equal weighting $\mathcal{L} = \mathcal{L}_1 + \mathcal{L}_2$.

## 4. Fair Comparison Protocol
- Same data splits, same total workload, and identical stopping thresholds.
- Hardware specifications reported explicitly.

## 5. Experimental Results & Verification
*(To be populated following approved test runs)*

## 6. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
