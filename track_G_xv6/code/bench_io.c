#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "user/user.h"
#include "kernel/pstat.h"

// Workload 2: I/O-Bound Interactive Benchmark
// Objective: Response time and starvation resistance under frequent blocking I/O.
// Expected Behavior:
//   - An I/O-bound process yields CPU frequently via sleep/disk I/O.
//   - When waking up, the scheduler should promptly dispatch it without latency penalties.

int main(int argc, char *argv[]) {
  printf("[bench_io] Starting I/O-bound responsiveness benchmark...\n");

  int pid = fork();
  if (pid < 0) {
    printf("[bench_io] Fork failed\n");
    exit(1);
  }

  if (pid == 0) {
    // Child: interactive I/O worker
    settickets(20);
    int total_latency = 0;
    int rounds = 20;

    for (int r = 0; r < rounds; r++) {
      int t0 = uptime();
      // Sleep for 1 timer tick (yielding voluntarily)
      sleep(1);
      int t1 = uptime();
      total_latency += (t1 - t0);

      // Perform a small file write and read
      int fd = open("iotest.tmp", O_CREATE | O_WRONLY);
      if (fd >= 0) {
        write(fd, "xv6_io_benchmark_block", 22);
        close(fd);
      }
      unlink("iotest.tmp");
    }

    printf("[bench_io] Completed %d I/O iterations. Average latency per cycle: %d ticks\n",
           rounds, total_latency / rounds);
    exit(0);
  }

  // Parent: concurrent background worker competing for CPU
  settickets(10);
  volatile double sum = 0;
  for (int i = 0; i < 20000000; i++) {
    sum += 1.0;
  }

  wait(0);
  printf("[bench_io] I/O benchmark finished successfully.\n");
  exit(0);
}
