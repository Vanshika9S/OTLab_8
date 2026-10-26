# Track G: xv6 Environment Setup and Verification Guide

> **OS Target**: Windows (via WSL2 / Ubuntu) or native Linux  
> **Rule Requirement**: Do NOT record or report benchmark numbers until actually executed and confirmed on hardware under QEMU.

---

## 1. Which xv6 Version?
Please confirm whether your course uses:
- **Option A (Standard Modern)**: MIT `xv6-riscv` (6.S081 / 6.1810 teaching OS).
- **Option B (Legacy)**: MIT `xv6-public` (32-bit x86 architecture).

Unless specified otherwise by your instructor, modern OS optimization courses use `xv6-riscv`.

---

## 2. Exact Setup Steps for Windows (WSL2)

### Step 2.1: Open WSL2 Terminal (Ubuntu)
In Windows PowerShell, ensure WSL is active:
```powershell
wsl -d Ubuntu
```

### Step 2.2: Install RISC-V Cross-Compiler and QEMU
Inside your WSL terminal:
```bash
sudo apt-get update
sudo apt-get install -y git build-essential gdb-multiarch qemu-system-misc \
                        gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu
```

Verify installations:
```bash
riscv64-linux-gnu-gcc --version
qemu-system-riscv64 --version
```

### Step 2.3: Clone Unmodified MIT xv6-riscv
```bash
cd /mnt/c/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/
git clone https://github.com/mit-pdos/xv6-riscv.git
cd xv6-riscv
```

### Step 2.4: Build and Boot xv6 in QEMU
```bash
make qemu
```
*(To exit QEMU at any time, press `Ctrl-A` then `X`).*

---

## 3. Mandatory Baseline Verification: usertests

Before making any kernel modifications (scheduler, buffer cache, COW fork), the unmodified kernel must pass all official stress tests:

Inside the xv6 shell:
```bash
$ usertests
```

### Output Confirmation Form
Paste the final output lines confirming the clean pass into your reply:
```text
ALL TESTS PASSED
```
*Note: We will not record or fabricate baseline turnaround times or usertests status until you paste the confirmed log from your actual run.*
