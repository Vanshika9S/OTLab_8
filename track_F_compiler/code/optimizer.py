"""
optimizer.py
------------
Optimization passes for ToyLang Three-Address Code (TAC):
  1. Constant Folding & Forward Propagation
  2. Strength Reduction & Algebraic Simplification
  3. Common Subexpression Elimination (CSE)
  4. Dead-Code Elimination (DCE) using CFG Fixed-Point Dataflow Liveness Analysis
  5. Loop-Invariant Code Motion (LICM) with Natural Loop Detection
  6. Multi-Pass Fixed-Point Optimization Pipeline
"""

from typing import List, Dict, Set, Tuple, Any, Optional
import copy
from track_F_compiler.code.ir import Instruction


# ==============================================================================
# CFG BASIC BLOCK & LIVENESS ANALYSIS
# ==============================================================================
class BasicBlock:
    def __init__(self, block_id: int):
        self.block_id = block_id
        self.instructions: List[Instruction] = []
        self.predecessors: List["BasicBlock"] = []
        self.successors: List["BasicBlock"] = []
        self.use_set: Set[str] = set()
        self.def_set: Set[str] = set()
        self.live_in: Set[str] = set()
        self.live_out: Set[str] = set()

    def compute_local_defs_and_uses(self):
        self.use_set.clear()
        self.def_set.clear()
        for inst in self.instructions:
            for u in inst.get_uses():
                if u not in self.def_set:
                    self.use_set.add(u)
            for d in inst.get_defs():
                self.def_set.add(d)


class ControlFlowGraph:
    """Constructs CFG from a flat list of TAC instructions."""

    def __init__(self, instructions: List[Instruction]):
        self.instructions = instructions
        self.blocks: List[BasicBlock] = []
        self.label_to_block: Dict[str, BasicBlock] = {}
        self._build_blocks()
        self._connect_edges()
        self.compute_liveness()

    def _build_blocks(self):
        if not self.instructions:
            return

        # Determine leaders
        n = len(self.instructions)
        is_leader = [False] * n
        is_leader[0] = True

        for i, inst in enumerate(self.instructions):
            if inst.op == "LABEL":
                is_leader[i] = True
            elif inst.op in ("JUMP", "JUMP_IF_FALSE"):
                if i + 1 < n:
                    is_leader[i + 1] = True

        # Partition instructions into blocks
        current_block = None
        block_id = 0

        for i, inst in enumerate(self.instructions):
            if is_leader[i]:
                if current_block is not None:
                    self.blocks.append(current_block)
                current_block = BasicBlock(block_id)
                block_id += 1

            current_block.instructions.append(inst)
            if inst.op == "LABEL":
                self.label_to_block[inst.args[0]] = current_block

        if current_block is not None:
            self.blocks.append(current_block)

        for b in self.blocks:
            b.compute_local_defs_and_uses()

    def _connect_edges(self):
        num_blocks = len(self.blocks)
        for i, b in enumerate(self.blocks):
            if not b.instructions:
                continue
            last_inst = b.instructions[-1]
            op = last_inst.op

            if op == "JUMP":
                target = last_inst.args[0]
                if target in self.label_to_block:
                    succ = self.label_to_block[target]
                    b.successors.append(succ)
                    succ.predecessors.append(b)

            elif op == "JUMP_IF_FALSE":
                target = last_inst.args[1]
                if target in self.label_to_block:
                    succ_branch = self.label_to_block[target]
                    b.successors.append(succ_branch)
                    succ_branch.predecessors.append(b)
                # Fall-through successor
                if i + 1 < num_blocks:
                    succ_fall = self.blocks[i + 1]
                    b.successors.append(succ_fall)
                    succ_fall.predecessors.append(b)

            else:
                # Normal fall-through
                if i + 1 < num_blocks:
                    succ_fall = self.blocks[i + 1]
                    b.successors.append(succ_fall)
                    succ_fall.predecessors.append(b)

    def compute_liveness(self):
        """Iterative fixed-point dataflow equations for liveness."""
        changed = True
        while changed:
            changed = False
            for b in reversed(self.blocks):
                # OUT[B] = union_{S in succ(B)} IN[S]
                new_out = set()
                for s in b.successors:
                    new_out.update(s.live_in)

                # IN[B] = USE[B] union (OUT[B] \ DEF[B])
                new_in = b.use_set | (new_out - b.def_set)

                if new_in != b.live_in or new_out != b.live_out:
                    b.live_in = new_in
                    b.live_out = new_out
                    changed = True


# ==============================================================================
# PASS 1: CONSTANT FOLDING & CONSTANT PROPAGATION
# ==============================================================================
class ConstantFolderAndPropagator:
    @staticmethod
    def run(instructions: List[Instruction]) -> List[Instruction]:
        constants: Dict[str, int] = {}
        optimized: List[Instruction] = []

        for inst in instructions:
            op = inst.op

            # Invalidate constants across labels to prevent illegal loop assumptions
            if op == "LABEL":
                constants.clear()
                optimized.append(inst)
                continue

            if op == "CONST":
                val = int(inst.args[0])
                constants[inst.dest] = val
                optimized.append(inst)

            elif op == "COPY":
                src = inst.args[0]
                if isinstance(src, str) and src in constants:
                    val = constants[src]
                    constants[inst.dest] = val
                    optimized.append(Instruction("CONST", inst.dest, [val]))
                else:
                    if inst.dest in constants:
                        del constants[inst.dest]
                    optimized.append(inst)

            elif op == "BINOP":
                bop = inst.args[0]
                s1 = inst.args[1]
                s2 = inst.args[2]

                v1 = constants.get(s1) if isinstance(s1, str) else s1
                v2 = constants.get(s2) if isinstance(s2, str) else s2

                if v1 is not None and v2 is not None:
                    folded = ConstantFolderAndPropagator._eval_binop(bop, v1, v2)
                    if folded is not None:
                        constants[inst.dest] = folded
                        optimized.append(Instruction("CONST", inst.dest, [folded]))
                        continue

                new_s1 = v1 if v1 is not None else s1
                new_s2 = v2 if v2 is not None else s2
                if inst.dest in constants:
                    del constants[inst.dest]
                optimized.append(Instruction("BINOP", inst.dest, [bop, new_s1, new_s2]))

            elif op == "UNARYOP":
                uop = inst.args[0]
                s = inst.args[1]
                v = constants.get(s) if isinstance(s, str) else s
                if v is not None and uop == "-":
                    folded = -v
                    constants[inst.dest] = folded
                    optimized.append(Instruction("CONST", inst.dest, [folded]))
                else:
                    if inst.dest in constants:
                        del constants[inst.dest]
                    optimized.append(inst)

            elif op == "PRINT":
                s = inst.args[0]
                new_s = constants.get(s, s)
                optimized.append(Instruction("PRINT", None, [new_s]))

            elif op == "JUMP_IF_FALSE":
                cond = inst.args[0]
                target = inst.args[1]
                val = constants.get(cond) if isinstance(cond, str) else cond

                if val is not None:
                    if val == 0:
                        optimized.append(Instruction("JUMP", None, [target]))
                    else:
                        # Jump is never taken -> drop!
                        pass
                else:
                    optimized.append(inst)

            else:
                optimized.append(inst)

        return optimized

    @staticmethod
    def _eval_binop(op: str, v1: int, v2: int) -> Optional[int]:
        try:
            if op == "+": return v1 + v2
            if op == "-": return v1 - v2
            if op == "*": return v1 * v2
            if op == "/": return v1 // v2 if v2 != 0 else None
            if op == "%": return v1 % v2 if v2 != 0 else None
            if op == "==": return 1 if v1 == v2 else 0
            if op == "!=": return 1 if v1 != v2 else 0
            if op == "<": return 1 if v1 < v2 else 0
            if op == "<=": return 1 if v1 <= v2 else 0
            if op == ">": return 1 if v1 > v2 else 0
            if op == ">=": return 1 if v1 >= v2 else 0
        except ZeroDivisionError:
            return None
        return None


# ==============================================================================
# PASS 2: STRENGTH REDUCTION & ALGEBRAIC IDENTITIES
# ==============================================================================
class StrengthReducer:
    @staticmethod
    def run(instructions: List[Instruction]) -> List[Instruction]:
        optimized: List[Instruction] = []

        for inst in instructions:
            if inst.op != "BINOP":
                optimized.append(inst)
                continue

            op = inst.args[0]
            s1 = inst.args[1]
            s2 = inst.args[2]

            if op == "*":
                if s2 == 0 or s1 == 0:
                    optimized.append(Instruction("CONST", inst.dest, [0]))
                    continue
                if s2 == 1:
                    optimized.append(Instruction("COPY", inst.dest, [s1]))
                    continue
                if s1 == 1:
                    optimized.append(Instruction("COPY", inst.dest, [s2]))
                    continue
                # x * 2^k -> x << k
                if isinstance(s2, int) and s2 > 0 and (s2 & (s2 - 1)) == 0:
                    shift = s2.bit_length() - 1
                    optimized.append(Instruction("BINOP", inst.dest, ["<<", s1, shift]))
                    continue
                if isinstance(s1, int) and s1 > 0 and (s1 & (s1 - 1)) == 0:
                    shift = s1.bit_length() - 1
                    optimized.append(Instruction("BINOP", inst.dest, ["<<", s2, shift]))
                    continue

            elif op == "+":
                if s2 == 0:
                    optimized.append(Instruction("COPY", inst.dest, [s1]))
                    continue
                if s1 == 0:
                    optimized.append(Instruction("COPY", inst.dest, [s2]))
                    continue

            elif op == "-":
                if s2 == 0:
                    optimized.append(Instruction("COPY", inst.dest, [s1]))
                    continue

            elif op == "/":
                if s2 == 1:
                    optimized.append(Instruction("COPY", inst.dest, [s1]))
                    continue

            optimized.append(inst)

        return optimized


# ==============================================================================
# PASS 3: COMMON SUBEXPRESSION ELIMINATION (CSE)
# ==============================================================================
class CommonSubexpressionEliminator:
    @staticmethod
    def run(instructions: List[Instruction]) -> List[Instruction]:
        optimized: List[Instruction] = []
        expr_table: Dict[Tuple[str, Any, Any], str] = {}

        for inst in instructions:
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_FALSE"):
                expr_table.clear()
                optimized.append(inst)
                continue

            if inst.op == "BINOP":
                key = (inst.args[0], inst.args[1], inst.args[2])
                comm_key = (inst.args[0], inst.args[2], inst.args[1]) if inst.args[0] in ("+", "*", "==", "!=") else None

                match_dest = expr_table.get(key)
                if match_dest is None and comm_key:
                    match_dest = expr_table.get(comm_key)

                if match_dest is not None:
                    optimized.append(Instruction("COPY", inst.dest, [match_dest]))
                else:
                    expr_table[key] = inst.dest
                    optimized.append(inst)

            elif inst.op in ("CONST", "COPY"):
                dest = inst.dest
                keys_to_remove = [k for k in expr_table if k[1] == dest or k[2] == dest]
                for k in keys_to_remove:
                    del expr_table[k]
                optimized.append(inst)

            else:
                optimized.append(inst)

        return optimized


# ==============================================================================
# PASS 4: DEAD-CODE ELIMINATION VIA CFG LIVENESS ANALYSIS
# ==============================================================================
class DeadCodeEliminator:
    @staticmethod
    def run(instructions: List[Instruction]) -> List[Instruction]:
        cfg = ControlFlowGraph(instructions)
        clean_instructions: List[Instruction] = []

        for b in cfg.blocks:
            # Backward pass within basic block from live_out
            live = set(b.live_out)
            block_filtered = []

            for inst in reversed(b.instructions):
                op = inst.op

                # Essential instructions with side effects
                if op in ("PRINT", "LABEL", "JUMP", "JUMP_IF_FALSE"):
                    block_filtered.append(inst)
                    live.update(inst.get_uses())
                    continue

                dest = inst.dest
                if dest in live:
                    block_filtered.append(inst)
                    live.discard(dest)
                    live.update(inst.get_uses())
                else:
                    # Dead code: value never subsequently used -> ELIMINATE!
                    pass

            block_filtered.reverse()
            clean_instructions.extend(block_filtered)

        # Remove unreferenced labels
        referenced = set()
        for inst in clean_instructions:
            if inst.op in ("JUMP", "JUMP_IF_FALSE"):
                referenced.add(inst.args[-1])

        final_instructions = []
        for inst in clean_instructions:
            if inst.op == "LABEL" and inst.args[0] not in referenced:
                continue
            final_instructions.append(inst)

        return final_instructions


# ==============================================================================
# PASS 5: LOOP-INVARIANT CODE MOTION (LICM)
# ==============================================================================
class LoopInvariantCodeMotion:
    @staticmethod
    def run(instructions: List[Instruction]) -> List[Instruction]:
        # Identify single natural loops: LABEL start ... JUMP start, LABEL end
        loop_start_idx = None
        loop_end_idx = None
        target_label = None

        for idx, inst in enumerate(instructions):
            if inst.op == "LABEL" and loop_start_idx is None:
                lbl = inst.args[0]
                for j in range(idx + 1, len(instructions)):
                    if instructions[j].op == "JUMP" and instructions[j].args[0] == lbl:
                        loop_start_idx = idx
                        loop_end_idx = j
                        target_label = lbl
                        break
            if loop_start_idx is not None:
                break

        if loop_start_idx is None or loop_end_idx is None:
            return instructions

        # Body between header label and jump
        loop_body = instructions[loop_start_idx:loop_end_idx + 1]

        # Find variables mutated inside the loop
        loop_mutated: Set[str] = set()
        for inst in loop_body:
            loop_mutated.update(inst.get_defs())

        invariants = []
        kept_body = []

        for inst in loop_body:
            # Cannot hoist branches, labels, prints, or loop counters
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT"):
                kept_body.append(inst)
                continue

            uses = inst.get_uses()
            # Invariant condition: uses non-empty, none in loop_mutated, dest not in uses
            if uses and not (uses & loop_mutated) and inst.dest not in uses:
                invariants.append(inst)
            else:
                kept_body.append(inst)

        # Assemble: pre-loop + hoisted invariants + loop body + post-loop
        optimized = (
            instructions[:loop_start_idx]
            + invariants
            + kept_body
            + instructions[loop_end_idx + 1:]
        )
        return optimized


# ==============================================================================
# PASS PIPELINE
# ==============================================================================
class OptimizerPipeline:
    def __init__(self, passes: Optional[List[str]] = None):
        self.passes = passes or ["const_fold", "strength_red", "cse", "dce", "licm"]

    def optimize(self, instructions: List[Instruction], max_iter: int = 10) -> Tuple[List[Instruction], int]:
        current = copy.deepcopy(instructions)

        for iteration in range(max_iter):
            prev_str = str(current)

            if "const_fold" in self.passes:
                current = ConstantFolderAndPropagator.run(current)
            if "strength_red" in self.passes:
                current = StrengthReducer.run(current)
            if "cse" in self.passes:
                current = CommonSubexpressionEliminator.run(current)
            if "dce" in self.passes:
                current = DeadCodeEliminator.run(current)
            if "licm" in self.passes:
                current = LoopInvariantCodeMotion.run(current)

            if str(current) == prev_str:
                return current, iteration + 1

        return current, max_iter
