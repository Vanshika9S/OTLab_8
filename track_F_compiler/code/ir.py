"""
ir.py
-----
Three-Address Code (TAC) Intermediate Representation and Stack/Register VM Interpreter for ToyLang.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from track_F_compiler.code.parser import (
    ASTNode, ProgramNode, VarDeclNode, AssignNode, PrintNode,
    BlockNode, IfNode, WhileNode, BinaryOpNode, UnaryOpNode, NumNode, VarNode
)


class Instruction:
    """Three-Address Code (TAC) instruction."""
    def __init__(self, op: str, dest: Optional[str] = None, args: Optional[List[Any]] = None):
        self.op = op          # e.g., 'CONST', 'COPY', 'BINOP', 'PRINT', 'LABEL', 'JUMP', 'JUMP_IF_FALSE'
        self.dest = dest      # Destination register/variable name
        self.args = args or []  # Operands / literals / label names

    def __repr__(self) -> str:
        if self.op == "LABEL":
            return f"{self.args[0]}:"
        elif self.op == "CONST":
            return f"  {self.dest} = {self.args[0]}"
        elif self.op == "COPY":
            return f"  {self.dest} = {self.args[0]}"
        elif self.op == "BINOP":
            return f"  {self.dest} = {self.args[1]} {self.args[0]} {self.args[2]}"
        elif self.op == "UNARYOP":
            return f"  {self.dest} = {self.args[0]} {self.args[1]}"
        elif self.op == "PRINT":
            return f"  print {self.args[0]}"
        elif self.op == "JUMP":
            return f"  jump {self.args[0]}"
        elif self.op == "JUMP_IF_FALSE":
            return f"  jump_if_false {self.args[0]}, {self.args[1]}"
        return f"  {self.op} {self.dest} {self.args}"

    def get_defs(self) -> Set[str]:
        """Variables/registers written to by this instruction."""
        if self.dest is not None and self.op not in ("LABEL", "PRINT", "JUMP", "JUMP_IF_FALSE"):
            return {self.dest}
        return set()

    def get_uses(self) -> Set[str]:
        """Variables/registers read by this instruction."""
        uses = set()
        if self.op == "COPY":
            if isinstance(self.args[0], str) and not self.args[0].isdigit():
                uses.add(self.args[0])
        elif self.op == "BINOP":
            for operand in (self.args[1], self.args[2]):
                if isinstance(operand, str) and not operand.isdigit() and not (operand.startswith("-") and operand[1:].isdigit()):
                    uses.add(operand)
        elif self.op == "UNARYOP":
            operand = self.args[1]
            if isinstance(operand, str) and not operand.isdigit():
                uses.add(operand)
        elif self.op in ("PRINT", "JUMP_IF_FALSE"):
            operand = self.args[0]
            if isinstance(operand, str) and not operand.isdigit():
                uses.add(operand)
        return uses


class IRCodeGenerator:
    """Compiles an AST into linear Three-Address Code (TAC)."""

    def __init__(self):
        self.instructions: List[Instruction] = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self) -> str:
        name = f"$t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self) -> str:
        name = f"$L{self.label_count}"
        self.label_count += 1
        return name

    def emit(self, instruction: Instruction):
        self.instructions.append(instruction)

    def generate(self, node: ASTNode) -> List[Instruction]:
        self.visit(node)
        return self.instructions

    def visit(self, node: ASTNode) -> Optional[str]:
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise NotImplementedError(f"No IR generator method visit_{type(node).__name__}")

    def visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_BlockNode(self, node: BlockNode):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDeclNode(self, node: VarDeclNode):
        res = self.visit(node.expr)
        self.emit(Instruction("COPY", node.name, [res]))

    def visit_AssignNode(self, node: AssignNode):
        res = self.visit(node.expr)
        self.emit(Instruction("COPY", node.name, [res]))

    def visit_PrintNode(self, node: PrintNode):
        res = self.visit(node.expr)
        self.emit(Instruction("PRINT", None, [res]))

    def visit_NumNode(self, node: NumNode) -> str:
        t = self.new_temp()
        self.emit(Instruction("CONST", t, [node.value]))
        return t

    def visit_VarNode(self, node: VarNode) -> str:
        return node.name

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        expr_t = self.visit(node.expr)
        dest_t = self.new_temp()
        self.emit(Instruction("UNARYOP", dest_t, [node.op, expr_t]))
        return dest_t

    def visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        left_t = self.visit(node.left)
        right_t = self.visit(node.right)
        dest_t = self.new_temp()
        self.emit(Instruction("BINOP", dest_t, [node.op, left_t, right_t]))
        return dest_t

    def visit_IfNode(self, node: IfNode):
        cond_t = self.visit(node.condition)
        else_label = self.new_label()
        end_label = self.new_label()

        # Branch to else if condition is 0 / False
        target_else = else_label if node.else_branch else end_label
        self.emit(Instruction("JUMP_IF_FALSE", None, [cond_t, target_else]))

        # Then branch
        self.visit(node.then_branch)

        if node.else_branch:
            self.emit(Instruction("JUMP", None, [end_label]))
            self.emit(Instruction("LABEL", None, [else_label]))
            self.visit(node.else_branch)

        self.emit(Instruction("LABEL", None, [end_label]))

    def visit_WhileNode(self, node: WhileNode):
        start_label = self.new_label()
        end_label = self.new_label()

        self.emit(Instruction("LABEL", None, [start_label]))
        cond_t = self.visit(node.condition)
        self.emit(Instruction("JUMP_IF_FALSE", None, [cond_t, end_label]))

        self.visit(node.body)
        self.emit(Instruction("JUMP", None, [start_label]))
        self.emit(Instruction("LABEL", None, [end_label]))


# ==============================================================================
# IR Virtual Machine Interpreter
# ==============================================================================
class VirtualMachine:
    """Executes Three-Address Code (TAC) and tracks instruction cycles and output."""

    def __init__(self, instructions: List[Instruction], max_cycles: int = 500000):
        self.instructions = instructions
        self.max_cycles = max_cycles
        self.env: Dict[str, int] = {}
        self.output: List[int] = []
        self.cycles = 0
        self.label_map: Dict[str, int] = {}

        # Precompute label addresses for O(1) jump lookups
        for idx, inst in enumerate(instructions):
            if inst.op == "LABEL":
                self.label_map[inst.args[0]] = idx

    def resolve(self, operand: Any) -> int:
        if isinstance(operand, int):
            return operand
        if isinstance(operand, str):
            # Check if integer literal stored as string
            if operand.isdigit() or (operand.startswith("-") and operand[1:].isdigit()):
                return int(operand)
            if operand in self.env:
                return self.env[operand]
            raise NameError(f"Undefined variable or temporary '{operand}'")
        raise ValueError(f"Cannot resolve operand: {operand}")

    def run(self) -> Tuple[List[int], int]:
        pc = 0
        n = len(self.instructions)

        while pc < n:
            self.cycles += 1
            if self.cycles > self.max_cycles:
                raise TimeoutError(f"Execution exceeded maximum instruction cycle limit ({self.max_cycles})")

            inst = self.instructions[pc]
            op = inst.op

            if op == "LABEL":
                pc += 1

            elif op == "CONST":
                self.env[inst.dest] = int(inst.args[0])
                pc += 1

            elif op == "COPY":
                self.env[inst.dest] = self.resolve(inst.args[0])
                pc += 1

            elif op == "BINOP":
                bop = inst.args[0]
                v1 = self.resolve(inst.args[1])
                v2 = self.resolve(inst.args[2])

                if bop == "+":
                    res = v1 + v2
                elif bop == "-":
                    res = v1 - v2
                elif bop == "*":
                    res = v1 * v2
                elif bop == "/":
                    if v2 == 0:
                        raise ZeroDivisionError("Division by zero in runtime VM")
                    res = v1 // v2
                elif bop == "%":
                    if v2 == 0:
                        raise ZeroDivisionError("Modulo by zero in runtime VM")
                    res = v1 % v2
                elif bop == "==":
                    res = 1 if v1 == v2 else 0
                elif bop == "!=":
                    res = 1 if v1 != v2 else 0
                elif bop == "<":
                    res = 1 if v1 < v2 else 0
                elif bop == "<=":
                    res = 1 if v1 <= v2 else 0
                elif bop == ">":
                    res = 1 if v1 > v2 else 0
                elif bop == ">=":
                    res = 1 if v1 >= v2 else 0
                elif bop == "<<":
                    res = v1 << v2
                else:
                    raise ValueError(f"Unknown binary operator '{bop}'")

                self.env[inst.dest] = res
                pc += 1

            elif op == "UNARYOP":
                uop = inst.args[0]
                val = self.resolve(inst.args[1])
                if uop == "-":
                    res = -val
                else:
                    raise ValueError(f"Unknown unary operator '{uop}'")
                self.env[inst.dest] = res
                pc += 1

            elif op == "PRINT":
                val = self.resolve(inst.args[0])
                self.output.append(val)
                pc += 1

            elif op == "JUMP":
                target_label = inst.args[0]
                pc = self.label_map[target_label] + 1

            elif op == "JUMP_IF_FALSE":
                cond_val = self.resolve(inst.args[0])
                target_label = inst.args[1]
                if cond_val == 0:
                    pc = self.label_map[target_label] + 1
                else:
                    pc += 1

            else:
                raise ValueError(f"Unknown VM instruction: {inst}")

        return self.output, self.cycles
