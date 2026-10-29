#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/pstat.h"

// Workload 3: Mixed Heterogeneous Benchmark
// Objective: System throughput and isolation across mixed CPU-heavy and I/O-heavy jobs.
// Expected Behavior:
//   - Tests scheduler balance when interactive tasks coexist with CPU hogs.
//   - Proportional share ensures CPU hogs cannot monopolize the system or starve I/O tasks.

void cpu_task(int id, int tickets, int loop_count) {
  settickets(tickets);
  int t0 = uptime();
  volatile double val = 1.0;
  for (int i = 0; i < loop_count; i++) {
    val = val * 1.00001;
  }
  int t1 = uptime();
  printf("[bench_mixed] CPU Worker %d (Tickets %d) done in %d ticks\n", id, tickets, t1 - t0);
}

void io_task(int id, int tickets, int sleep_count) {
  settickets(tickets);
  int t0 = uptime();
  for (int i = 0; i < sleep_count; i++) {
    sleep(2);
  }
  int t1 = uptime();
  printf("[bench_mixed] I/O Worker %d (Tickets %d) done in %d ticks\n", id, tickets, t1 - t0);
}

int main(int argc, char *argv[]) {
  printf("[bench_mixed] Starting mixed workload (2 CPU-bound workers + 2 I/O-bound workers)...\n");
  int start_time = uptime();

  // Worker 1: High-ticket CPU worker (30 tickets)
  if (fork() == 0) {
    cpu_task(1, 30, 40000000);
    exit(0);
  }

  // Worker 2: Low-ticket CPU worker (10 tickets)
  if (fork() == 0) {
    cpu_task(2, 10, 40000000);
    exit(0);
  }

  // Worker 3: High-ticket I/O worker (30 tickets)
  if (fork() == 0) {
    io_task(3, 30, 10);
    exit(0);
  }

  // Worker 4: Low-ticket I/O worker (10 tickets)
  if (fork() == 0) {
    io_task(4, 10, 10);
    exit(0);
  }

  // Wait for all 4 children
  for (int i = 0; i < 4; i++) {
    wait(0);
  }

  int total_time = uptime() - start_time;
  printf("[bench_mixed] All mixed workers finished. Total time: %d ticks\n", total_time);
  exit(0);
}
