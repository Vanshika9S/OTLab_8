"""
benchmarks.py
-------------
Benchmark Suite and Tricky Correctness Verification for Track F Compiler Optimizations.

Measures:
  1. Static Code Size (IR instruction count before and after)
  2. Dynamic Execution Cycles (VM steps before and after)
  3. Wall-Clock Execution Time (before and after)
  4. Compile & Optimization Pass Time
  5. Correctness Verification (Output equivalence and edge-case behavior)
"""

import sys
import os
import time
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_F_compiler.code.lexer import Lexer
from track_F_compiler.code.parser import Parser
from track_F_compiler.code.ir import IRCodeGenerator, VirtualMachine
from track_F_compiler.code.optimizer import OptimizerPipeline
from track_F_compiler.code.register_allocator import (
    LivenessAnalyzer, ILPRegisterAllocator, GreedyChaitinBriggsAllocator, NaiveRegisterAllocator
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ==============================================================================
# BENCHMARK SUITE PROGRAMS
# ==============================================================================
BENCHMARKS = {
    "Prog1_ConstFold_DCE": """
    let a = 10 + 20 * 2;
    let b = a * 2;
    let dead_var = b + 500;
    let c = 5;
    if (c > 10) {
        let unreachable = 999;
        print(unreachable);
    } else {
        print(b);
    }
    """,

    "Prog2_CSE_StrengthRed": """
    let x = 7;
    let y = 14;
    let t1 = (x * y) + 3;
    let t2 = (x * y) + 10;
    let z = x * 8;
    let res = t1 + t2 + z;
    print(res);
    """,

    "Prog3_LICM_Loop": """
    let n = 25;
    let base_offset = 15 * 4;
    let factor = 3;
    let acc = 0;
    let i = 0;

    while (i < n) {
        let invariant = base_offset * factor;
        acc = acc + invariant + i;
        i = i + 1;
    }
    print(acc);
    """,

    "Prog4_Fibonacci_Sequence": """
    let n = 15;
    let a = 0;
    let b = 1;
    let i = 0;

    while (i < n) {
        let next_val = a + b;
        a = b;
        b = next_val;
        i = i + 1;
    }
    print(a);
    """,

    "Prog5_Nested_Conditionals": """
    let sum = 0;
    let i = 0;
    let limit = 20;

    while (i < limit) {
        let mult = i * 2;
        if (mult > 10) {
            sum = sum + mult;
        } else {
            sum = sum + 1;
        }
        i = i + 1;
    }
    print(sum);
    """
}


# ==============================================================================
# TRICKY EDGE CASES (CORRECTNESS TEST SUITE)
# ==============================================================================
TRICKY_EDGE_CASES = {
    "EdgeCase_SideEffectsPreserved": """
    // DCE must NEVER remove print even if its argument looks like dead arithmetic
    let x = 50 * 2;
    let dead = x + 100;
    print(x);
    """,

    "EdgeCase_LoopVariableMutation": """
    // Variables mutated inside loops must NOT be propagated as constant initial values
    let i = 0;
    let acc = 0;
    while (i < 5) {
        acc = acc + i;
        i = i + 1;
    }
    print(acc);
    """,

    "EdgeCase_VariableReassignment": """
    // Sequential reassignment of the same variable name must preserve intermediate states
    let x = 10;
    x = x + 5;
    x = x * 2;
    print(x);
    """,

    "EdgeCase_UnreachableBranchPruning": """
    // Constant condition ensures else branch is taken; dead then branch must not crash
    let flag = 0;
    if (flag == 1) {
        let dead = 999;
        print(dead);
    } else {
        let live = 42;
        print(live);
    }
    """,

    "EdgeCase_ZeroIdentities": """
    // Multiplication by zero, addition of zero, subtraction of zero
    let a = 123;
    let b = a * 0;
    let c = a + 0;
    let d = a - 0;
    let res = b + c + d;
    print(res);
    """
}


def run_compiler_benchmarks() -> Tuple[pd.DataFrame, pd.DataFrame]:
    print("\n--- Running Track F Compiler Optimization Benchmarks ---")
    pipeline = OptimizerPipeline()
    records = []

    for name, source in BENCHMARKS.items():
        # 1. Front-end compilation
        t_compile_0 = time.perf_counter()
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        ir_unopt = IRCodeGenerator().generate(ast)
        t_compile = (time.perf_counter() - t_compile_0) * 1000.0

        # 2. Optimization pass pipeline
        t_opt_0 = time.perf_counter()
        ir_opt, passes_run = pipeline.optimize(ir_unopt)
        t_opt = (time.perf_counter() - t_opt_0) * 1000.0

        # 3. Virtual Machine execution: Unoptimized
        t_run_unopt_0 = time.perf_counter()
        vm_unopt = VirtualMachine(ir_unopt)
        out_unopt, cycles_unopt = vm_unopt.run()
        t_run_unopt = (time.perf_counter() - t_run_unopt_0) * 1000.0

        # 4. Virtual Machine execution: Optimized
        t_run_opt_0 = time.perf_counter()
        vm_opt = VirtualMachine(ir_opt)
        out_opt, cycles_opt = vm_opt.run()
        t_run_opt = (time.perf_counter() - t_run_opt_0) * 1000.0

        # Correctness check: Output equivalence
        is_identical = bool(out_unopt == out_opt)
        assert is_identical, f"Correctness violation in {name}! Unopt: {out_unopt} vs Opt: {out_opt}"

        code_size_reduction = (len(ir_unopt) - len(ir_opt)) / len(ir_unopt) * 100.0
        cycle_speedup = cycles_unopt / max(cycles_opt, 1)

        records.append({
            "Program": name,
            "Output": str(out_opt),
            "Output_Identical": is_identical,
            "Unopt_IR_Size": len(ir_unopt),
            "Opt_IR_Size": len(ir_opt),
            "Size_Reduction_Percent": round(code_size_reduction, 2),
            "Unopt_Cycles": cycles_unopt,
            "Opt_Cycles": cycles_opt,
            "Cycle_Speedup_Factor": round(cycle_speedup, 2),
            "Unopt_Runtime_ms": round(t_run_unopt, 3),
            "Opt_Runtime_ms": round(t_run_opt, 3),
            "Compile_Time_ms": round(t_compile, 3),
            "Optimization_Time_ms": round(t_opt, 3)
        })
        print(f"{name:25s} | Out: {str(out_opt):10s} | Size: {len(ir_unopt):2d}->{len(ir_opt):2d} (-{code_size_reduction:4.1f}%) | Cycles: {cycles_unopt:3d}->{cycles_opt:3d} ({cycle_speedup:4.1f}x)")

    df_bench = pd.DataFrame(records)
    csv_file = os.path.join(RESULTS_DIR, "compiler_benchmarks_summary.csv")
    df_bench.to_csv(csv_file, index=False)

    # Plot Code Size and Dynamic Cycle Reductions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    x = np.arange(len(df_bench))
    width = 0.35

    ax1.bar(x - width/2, df_bench["Unopt_IR_Size"], width, label="Unoptimized TAC Size", color="#d62728", alpha=0.85)
    ax1.bar(x + width/2, df_bench["Opt_IR_Size"], width, label="Optimized TAC Size", color="#1f77b4", alpha=0.85)
    ax1.set_xlabel("Benchmark Program", fontsize=11)
    ax1.set_ylabel("IR Instruction Count (Static Size)", fontsize=11)
    ax1.set_title("Static Code Size Reduction", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels([p.replace("Prog", "P") for p in df_bench["Program"]], rotation=15)
    ax1.grid(True, axis="y", linestyle="--", alpha=0.6)
    ax1.legend()

    ax2.bar(x - width/2, df_bench["Unopt_Cycles"], width, label="Unoptimized Cycles", color="#d62728", alpha=0.85)
    ax2.bar(x + width/2, df_bench["Opt_Cycles"], width, label="Optimized Cycles", color="#2ca02c", alpha=0.85)
    ax2.set_xlabel("Benchmark Program", fontsize=11)
    ax2.set_ylabel("Dynamic VM Execution Cycles", fontsize=11)
    ax2.set_title("Dynamic Instruction Cycle Reduction", fontsize=12, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels([p.replace("Prog", "P") for p in df_bench["Program"]], rotation=15)
    ax2.grid(True, axis="y", linestyle="--", alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    plot_file = os.path.join(RESULTS_DIR, "compiler_optimization_speedup.png")
    plt.savefig(plot_file, dpi=300)
    plt.close()

    # ==========================================================================
    # REGISTER ALLOCATION OPTIMIZATION BENCHMARK
    # ==========================================================================
    print("\n--- Register Allocation Optimization Benchmarks ---")
    reg_records = []

    for name in ["Prog3_LICM_Loop", "Prog4_Fibonacci_Sequence", "Prog5_Nested_Conditionals"]:
        source = BENCHMARKS[name]
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        ir = IRCodeGenerator().generate(ast)

        variables, edges, spill_costs = LivenessAnalyzer.build_interference_graph(ir)

        for K in [2, 3, 4]:
            res_ilp = ILPRegisterAllocator.allocate(variables, edges, spill_costs, K_registers=K)
            res_gr = GreedyChaitinBriggsAllocator.allocate(variables, edges, spill_costs, K_registers=K)
            res_nv = NaiveRegisterAllocator.allocate(variables, spill_costs)

            reg_records.append({
                "Program": name,
                "Registers_K": K,
                "Variables": len(variables),
                "Interference_Edges": len(edges),
                "ILP_Spilled": len(res_ilp["spilled"]),
                "ILP_Spill_Cost": res_ilp["total_spill_cost"],
                "ILP_Time_ms": round(res_ilp["runtime_ms"], 2),
                "Greedy_Spilled": len(res_gr["spilled"]),
                "Greedy_Spill_Cost": res_gr["total_spill_cost"],
                "Greedy_Time_ms": round(res_gr["runtime_ms"], 2),
                "Naive_Spill_Cost": res_nv["total_spill_cost"]
            })
            print(f"{name:20s} | K={K} | ILP Cost: {res_ilp['total_spill_cost']:2d} ({res_ilp['runtime_ms']:4.1f}ms) vs Greedy Cost: {res_gr['total_spill_cost']:2d} ({res_gr['runtime_ms']:4.2f}ms) vs Naive: {res_nv['total_spill_cost']:2d}")

    df_reg = pd.DataFrame(reg_records)
    reg_csv = os.path.join(RESULTS_DIR, "register_allocation_comparison.csv")
    df_reg.to_csv(reg_csv, index=False)

    return df_bench, df_reg


def verify_tricky_edge_cases() -> pd.DataFrame:
    print("\n--- Verifying Tricky Correctness Edge Cases ---")
    pipeline = OptimizerPipeline()
    records = []

    for name, source in TRICKY_EDGE_CASES.items():
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        ir_unopt = IRCodeGenerator().generate(ast)
        ir_opt, _ = pipeline.optimize(ir_unopt)

        vm_unopt = VirtualMachine(ir_unopt)
        out_unopt, _ = vm_unopt.run()

        vm_opt = VirtualMachine(ir_opt)
        out_opt, _ = vm_opt.run()

        is_identical = bool(out_unopt == out_opt)
        records.append({
            "Edge_Case": name,
            "Expected_Output": str(out_unopt),
            "Optimized_Output": str(out_opt),
            "Output_Identical": is_identical,
            "Status": "PASSED" if is_identical else "FAILED"
        })
        print(f"{name:35s} | Expected: {str(out_unopt):8s} | Optimized: {str(out_opt):8s} | Status: PASSED")
        assert is_identical, f"Edge case failed: {name}"

    df_edge = pd.DataFrame(records)
    edge_csv = os.path.join(RESULTS_DIR, "compiler_edge_cases_verification.csv")
    df_edge.to_csv(edge_csv, index=False)
    return df_edge


def main():
    print("=" * 80)
    print("DAY 8: TRACK F COMPILER OPTIMIZATION BENCHMARK SUITE")
    print("=" * 80)

    run_compiler_benchmarks()
    verify_tricky_edge_cases()

    print("\n[SUCCESS] Track F compiler benchmark suite completed successfully!")


if __name__ == "__main__":
    main()
