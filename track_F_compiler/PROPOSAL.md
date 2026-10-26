# Track F: Mini-Compiler Optimization — Language & Grammar Proposal

> **Status**: Architecture Proposal (Design Phase — No optimization code written yet per Day 3 instructions)  
> **Course**: Optimization Techniques (Assignment 8, Track F)

---

## 1. Formal Grammar Specification (EBNF)

We specify **ToyLang**, a structured, statically-scoped imperative toy language designed specifically to expose compiler optimization opportunities (constant folding, dead-code elimination, common subexpression elimination, loop unrolling, and register allocation).

```ebnf
Program        ::= Statement*

Statement      ::= VarDecl
                 | Assignment
                 | IfStmt
                 | WhileStmt
                 | PrintStmt
                 | Block

Block          ::= "{" Statement* "}"

VarDecl        ::= "let" Identifier "=" Expression ";"
Assignment     ::= Identifier "=" Expression ";"
PrintStmt      ::= "print" "(" Expression ")" ";"

IfStmt         ::= "if" "(" Condition ")" Block ("else" Block)?
WhileStmt      ::= "while" "(" Condition ")" Block

Condition      ::= Expression RelOp Expression
RelOp          ::= "==" | "!=" | "<" | "<=" | ">" | ">="

Expression     ::= Term (( "+" | "-" ) Term)*
Term           ::= Factor (( "*" | "/" | "%" ) Factor)*
Factor         ::= Integer
                 | Identifier
                 | "(" Expression ")"
                 | "-" Factor

Identifier     ::= [a-zA-Z_][a-zA-Z0-9_]*
Integer        ::= [0-9]+
```

---

## 2. Three Example Benchmark Programs

### Program 1: Arithmetic, Constant Folding & Dead-Code Elimination
*Target Optimizations: Constant Folding, Constant Propagation, Dead-Code Elimination (DCE).*

```c
// Example 1: Constant folding and dead code
let a = 10 + 20 * 2;       // Fold to: a = 50
let b = a * 2;              // Propagate: b = 100
let dead_var = b + 500;     // Unused in subsequent code -> DCE candidate
let c = 5;
if (c > 10) {               // Known constant branch (5 > 10 is False) -> Dead branch DCE
    let unreachable = 999;
    print(unreachable);
} else {
    print(b);               // Outputs 100
}
```

### Program 2: Common Subexpression Elimination & Strength Reduction
*Target Optimizations: Available Expressions / CSE, Strength Reduction.*

```c
// Example 2: Common Subexpression Elimination (CSE) & Strength Reduction
let x = 7;
let y = 14;
let t1 = (x * y) + 3;       // Computes (x * y)
let t2 = (x * y) + 10;      // (x * y) is redundant subexpression -> reuse t1's multiplication
let z = x * 8;              // Multiplication by 2^3 -> Strength reduction to (x << 3)
let res = t1 + t2 + z;
print(res);
```

### Program 3: Loop Invariant Code Motion & Loop Unrolling
*Target Optimizations: Loop-Invariant Code Motion (LICM), Loop Unrolling, Register Allocation via Graph Coloring.*

```c
// Example 3: Loop Optimization & Register Allocation
let n = 10;
let base_offset = 15 * 4;   // Invariant: constant expression
let factor = 3;
let acc = 0;
let i = 0;

while (i < n) {
    let invariant = base_offset * factor; // Loop-invariant computation -> hoist before loop
    acc = acc + invariant + i;
    i = i + 1;                            // Loop unrolling candidate (e.g. unroll factor 2 or 4)
}

print(acc);
```

---

## 3. Chapter 6 Optimization Decision Formulation
Per Section 6 of `ASSIGNMENT_SPEC.md`, at least one compiler decision must be formulated as a mathematical optimization problem:
- **Register Allocation via Graph Coloring**:
  - Interference graph $G = (V, E)$ where variables $u, v$ have overlapping live ranges.
  - Formulated as an exact **Integer Linear Programming (ILP)** or **Chaitin-Briggs Greedy Kempe-heuristic**:
    $$\min K \quad \text{s.t.} \quad c_u \neq c_v \; \forall (u, v) \in E, \; c_u \in \{1, \dots, K\}$$
    Minimizes register spill memory operations.
