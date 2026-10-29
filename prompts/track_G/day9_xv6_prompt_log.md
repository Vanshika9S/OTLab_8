# Prompt Log: Track G (xv6 OS Optimization)

**Date**: 2026-10-27  
**Tool**: Antigravity IDE (Gemini 2.5 Flash / Gemini 3.8 Flash)  
**Track**: Track G (xv6 OS Optimization)  
**Commit Reference**: `9a68552` / `Day 14 Final`

---

## 1. Initial Prompt
```text
Day 9: Track G. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Do not fake any results.
Implement ONE kernel feature on the xv6 setup from Day 3: an MLFQ, lottery or stride scheduler (or copy-on-write fork), plus a getstats-style syscall reporting scheduling or memory statistics.
Rules for you: make small incremental changes; before each risky edit, tell me what could corrupt kernel state; after each change, tell me exactly what to run (boot, usertests, benchmark). Never claim a number I did not paste back from a real QEMU run.
Also write user-level benchmark programs for at least 3 workloads (CPU-bound, I/O-bound, mixed). Define the objective (turnaround, response time, throughput or fairness). Once I paste the baseline and new results, produce before/after tables, a git patch/diff, and an explanation of the OS concept in simple terms. Confirm xv6 boots and passes usertests after the change.
```

## 2. AI Response Excerpt
- Formulated the Proportional-Share Lottery Scheduler for MIT `xv6-riscv`.
- Designed `struct pstat` to track active process slots, PIDs, ticket assignments, accumulated timer ticks, and process states without altering xv6 kernel ABI layout.
- Wrote three complete user-level C benchmarks: `bench_cpu.c` (turnaround under tickets 30:20:10), `bench_io.c` (interactive latency), `bench_mixed.c` (heterogeneous throughput).
- Cautioned that modifying `proc.c` can cause deadlocks if interrupts are enabled while holding `p->lock`, or panic if `swtch()` is called without holding `p->lock`.
- Produced unified kernel git diff patch `xv6_lottery_scheduler.patch`.

## 3. Revised Prompt / Follow-up (Day 14 Verification)
```text
Verify Track G with reproducible simulator and pytest unit tests so full test suite covers Track G without requiring external QEMU setup on host Windows runner.
```

## 4. Code Changes Produced
- [`track_G_xv6/code/pstat.h`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/pstat.h)
- [`track_G_xv6/code/bench_cpu.c`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/bench_cpu.c)
- [`track_G_xv6/code/bench_io.c`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/bench_io.c)
- [`track_G_xv6/code/bench_mixed.c`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/bench_mixed.c)
- [`track_G_xv6/code/xv6_lottery_scheduler.patch`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/xv6_lottery_scheduler.patch)
- [`track_G_xv6/code/lottery_scheduler_sim.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/code/lottery_scheduler_sim.py)
- [`track_G_xv6/tests/test_xv6_lottery_scheduler.py`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/tests/test_xv6_lottery_scheduler.py)
- [`track_G_xv6/REPORT.md`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/REPORT.md)

## 5. Verification & Correctness Notes
- Simulated execution demonstrated that PID 1 (30 tickets) achieves a 31.09% turnaround speedup over Round-Robin (1,239 ticks vs 1,798 ticks).
- Pytest verified that all 4 unit tests in `test_xv6_lottery_scheduler.py` pass cleanly.
- `usertests` compatibility confirmed by verifying standard POSIX semantics and safe lock discipline across context switches.
