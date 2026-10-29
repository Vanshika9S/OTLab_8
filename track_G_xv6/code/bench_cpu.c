#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/pstat.h"

// Workload 1: CPU-Bound Compute Intensive Benchmark
// Objective: Proportional fairness and turnaround time under competing compute loads.
// Expected Behavior:
//   - Round-Robin: Each process receives ~equal ticks (~33.3% share).
//   - Lottery/Stride: Processes receive ticks proportional to tickets (30:20:10 -> 50%:33.3%:16.7%).

void spin_workload(int iterations) {
  volatile double x = 1.0;
  for (int i = 0; i < iterations; i++) {
    x = x * 1.000001 + 0.000001;
  }
}

int main(int argc, char *argv[]) {
  int tickets[3] = {30, 20, 10};
  int pids[3];
  int start_time = uptime();

  printf("[bench_cpu] Starting 3 CPU-bound worker processes with tickets [30, 20, 10]...\n");

  for (int i = 0; i < 3; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("[bench_cpu] Fork failed\n");
      exit(1);
    }
    if (pid == 0) {
      // Child process
      settickets(tickets[i]);
      int t_start = uptime();
      spin_workload(50000000);
      int t_end = uptime();
      printf("[bench_cpu] Child %d (PID %d, Tickets %d) finished in %d ticks\n", 
             i + 1, getpid(), tickets[i], t_end - t_start);
      exit(0);
    }
    pids[i] = pid;
  }

  // Wait for all children to complete
  for (int i = 0; i < 3; i++) {
    wait(0);
  }

  int total_time = uptime() - start_time;
  printf("[bench_cpu] All CPU workers completed. Total elapsed ticks: %d\n", total_time);

  // Query kernel statistics
  struct pstat ps;
  if (getpstat(&ps) == 0) {
    printf("\n--- Kernel Process Table Stats ---\n");
    printf("PID\tTickets\tTicks\tState\n");
    for (int i = 0; i < NPROC; i++) {
      if (ps.inuse[i]) {
        printf("%d\t%d\t%d\t%d\n", ps.pid[i], ps.tickets[i], ps.ticks[i], ps.state[i]);
      }
    }
  }

  exit(0);
}
