#ifndef _PSTAT_H_
#define _PSTAT_H_

#include "param.h"

// Process statistics structure for Track G scheduler evaluation
struct pstat {
  int inuse[NPROC];     // 1 if this process table slot is currently active; 0 otherwise
  int pid[NPROC];       // Process ID
  int tickets[NPROC];   // Number of lottery/stride tickets assigned
  int ticks[NPROC];     // Total CPU timer ticks accumulated by this process
  int state[NPROC];     // Current process state (e.g., RUNNABLE, RUNNING, SLEEPING)
};

#endif // _PSTAT_H_
