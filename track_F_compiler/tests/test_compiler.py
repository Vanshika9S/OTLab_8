"""
test_compiler.py
----------------
Automated unit test suite for Track F Compiler Optimizations:
  1. Lexer and Parser token/AST correctness
  2. Constant Folding and Forward Propagation
  3. Strength Reduction and Algebraic Simplification
  4. Common Subexpression Elimination (CSE)
  5. Dead-Code Elimination (DCE) using CFG Liveness Analysis
  6. Loop-Invariant Code Motion (LICM)
  7. Exact ILP vs Greedy Register Allocation
  8. Tricky edge cases and output equivalence verification
"""

import os
import sys
import pytest

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_F_compiler.code.lexer import Lexer, TokenType
from track_F_compiler.code.parser import Parser
from track_F_compiler.code.ir import IRCodeGenerator, VirtualMachine, Instruction
from track_F_compiler.code.optimizer import (
    ConstantFolderAndPropagator, StrengthReducer, CommonSubexpressionEliminator,
    DeadCodeEliminator, LoopInvariantCodeMotion, OptimizerPipeline
)
from track_F_compiler.code.register_allocator import (
    LivenessAnalyzer, ILPRegisterAllocator, GreedyChaitinBriggsAllocator, NaiveRegisterAllocator
)


def test_lexer_tokens():
    """Verifies that the lexer properly tokenizes keywords, identifiers, numbers, operators, and comments."""
    src = "let x = 10 + 20 * 2; // test comment\nprint(x);"
    tokens = Lexer(src).tokenize()
    types = [t.type for t in tokens]
    assert types == [
        TokenType.LET, TokenType.IDENT, TokenType.ASSIGN, TokenType.INT,
        TokenType.PLUS, TokenType.INT, TokenType.STAR, TokenType.INT,
        TokenType.SEMI, TokenType.PRINT, TokenType.LPAREN, TokenType.IDENT,
        TokenType.RPAREN, TokenType.SEMI, TokenType.EOF
    ]
    assert tokens[1].value == "x"
    assert tokens[3].value == 10


def test_parser_ast_structure():
    """Verifies that the parser creates valid AST representation for nested expressions."""
    src = "let a = (5 + 3) * 2; if (a > 10) { print(a); }"
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    assert len(ast.statements) == 2


def test_constant_folding_and_propagation():
    """Verifies that arithmetic operations on constants are folded compile-time."""
    src = "let a = 10 + 20 * 2; let b = a * 2; print(b);"
    ast = Parser(Lexer(src).tokenize()).parse()
    ir = IRCodeGenerator().generate(ast)
    opt_ir = ConstantFolderAndPropagator.run(ir)
    opt_ir = DeadCodeEliminator.run(opt_ir)

    # In optimized IR, b should be folded to 100
    vm = VirtualMachine(opt_ir)
    out, _ = vm.run()
    assert out == [100]


def test_strength_reduction():
    """Verifies that multiplication by powers of 2 is reduced to left-shifts and identities simplified."""
    insts = [
        Instruction("BINOP", "t0", ["*", "x", 8]),
        Instruction("BINOP", "t1", ["*", "y", 1]),
        Instruction("BINOP", "t2", ["*", "z", 0]),
        Instruction("BINOP", "t3", ["+", "a", 0]),
    ]
    opt = StrengthReducer.run(insts)
    assert opt[0].op == "BINOP" and opt[0].args[0] == "<<" and opt[0].args[2] == 3
    assert opt[1].op == "COPY" and opt[1].args[0] == "y"
    assert opt[2].op == "CONST" and opt[2].args[0] == 0
    assert opt[3].op == "COPY" and opt[3].args[0] == "a"


def test_common_subexpression_elimination():
    """Verifies that redundant calculations of (x * y) are eliminated and reused."""
    insts = [
        Instruction("BINOP", "t0", ["*", "x", "y"]),
        Instruction("COPY", "a", ["t0"]),
        Instruction("BINOP", "t1", ["*", "x", "y"]),  # Redundant!
        Instruction("COPY", "b", ["t1"]),
    ]
    opt = CommonSubexpressionEliminator.run(insts)
    # The second BINOP should be replaced with a COPY of t0
    assert opt[2].op == "COPY" and opt[2].args[0] == "t0"


def test_dead_code_elimination_preserves_side_effects():
    """Verifies that DCE eliminates unused assignments but never removes print statements."""
    src = "let dead1 = 100 * 2; let dead2 = dead1 + 50; let live = 42; print(live);"
    ast = Parser(Lexer(src).tokenize()).parse()
    ir = IRCodeGenerator().generate(ast)
    opt_ir = DeadCodeEliminator.run(ir)

    vm = VirtualMachine(opt_ir)
    out, _ = vm.run()
    assert out == [42]
    # Verify dead variables were removed
    dest_names = [inst.dest for inst in opt_ir if inst.dest]
    assert "dead1" not in dest_names
    assert "dead2" not in dest_names


def test_loop_invariant_code_motion():
    """Verifies that loop-invariant calculations are hoisted outside loop headers."""
    src = """
    let n = 10; let b = 50; let f = 2; let acc = 0; let i = 0;
    while (i < n) {
        let inv = b * f;
        acc = acc + inv + i;
        i = i + 1;
    }
    print(acc);
    """
    ast = Parser(Lexer(src).tokenize()).parse()
    ir = IRCodeGenerator().generate(ast)
    opt_ir, _ = OptimizerPipeline().optimize(ir)

    vm_unopt = VirtualMachine(ir)
    vm_opt = VirtualMachine(opt_ir)
    out_unopt, _ = vm_unopt.run()
    out_opt, _ = vm_opt.run()

    assert out_unopt == out_opt
    assert len(opt_ir) < len(ir)


def test_register_allocation_ilp_vs_greedy():
    """Verifies that ILP and Greedy register allocators find valid non-interfering allocations."""
    src = """
    let a = 1; let b = 2; let c = 3;
    let d = a + b;
    let e = c + d;
    print(e);
    """
    ast = Parser(Lexer(src).tokenize()).parse()
    ir = IRCodeGenerator().generate(ast)
    variables, edges, spill_costs = LivenessAnalyzer.build_interference_graph(ir)

    res_ilp = ILPRegisterAllocator.allocate(variables, edges, spill_costs, K_registers=3)
    res_greedy = GreedyChaitinBriggsAllocator.allocate(variables, edges, spill_costs, K_registers=3)
    res_naive = NaiveRegisterAllocator.allocate(variables, spill_costs)

    assert res_ilp["success"]
    assert res_greedy["success"]
    assert res_ilp["total_spill_cost"] <= res_naive["total_spill_cost"]
    assert res_greedy["total_spill_cost"] <= res_naive["total_spill_cost"]

    # Verify no interfering variables share the same register in ILP
    alloc_ilp = res_ilp["allocation"]
    for u, v in edges:
        if u in alloc_ilp and v in alloc_ilp:
            assert alloc_ilp[u] != alloc_ilp[v], f"Interfering variables {u} and {v} assigned same register {alloc_ilp[u]}"


def test_tricky_edge_cases_output_equivalence():
    """Verifies that tricky edge cases (loops, variable reassignment, dead branches) preserve output."""
    cases = [
        ("let i = 0; let s = 0; while (i < 6) { s = s + i; i = i + 1; } print(s);", [15]),
        ("let x = 10; x = x + 5; x = x * 2; print(x);", [30]),
        ("let flag = 0; if (flag == 1) { print(999); } else { print(77); }", [77]),
        ("let a = 10; let b = a * 0; let c = a + 0; print(b + c);", [10]),
    ]
    pipeline = OptimizerPipeline()

    for src, expected in cases:
        ast = Parser(Lexer(src).tokenize()).parse()
        ir = IRCodeGenerator().generate(ast)
        opt_ir, _ = pipeline.optimize(ir)

        vm_unopt = VirtualMachine(ir)
        vm_opt = VirtualMachine(opt_ir)
        out_unopt, _ = vm_unopt.run()
        out_opt, _ = vm_opt.run()

        assert out_unopt == expected
        assert out_opt == expected
