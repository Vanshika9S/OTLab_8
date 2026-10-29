"""
parser.py
---------
Recursive Descent Parser for ToyLang producing an Abstract Syntax Tree (AST).
"""

from typing import List, Optional, Any
from track_F_compiler.code.lexer import Token, TokenType


# ==============================================================================
# AST Node Definitions
# ==============================================================================
class ASTNode:
    pass


class ProgramNode(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

    def __repr__(self) -> str:
        return f"ProgramNode({self.statements})"


class VarDeclNode(ASTNode):
    def __init__(self, name: str, expr: ASTNode):
        self.name = name
        self.expr = expr

    def __repr__(self) -> str:
        return f"VarDeclNode({self.name} = {self.expr})"


class AssignNode(ASTNode):
    def __init__(self, name: str, expr: ASTNode):
        self.name = name
        self.expr = expr

    def __repr__(self) -> str:
        return f"AssignNode({self.name} = {self.expr})"


class PrintNode(ASTNode):
    def __init__(self, expr: ASTNode):
        self.expr = expr

    def __repr__(self) -> str:
        return f"PrintNode({self.expr})"


class BlockNode(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

    def __repr__(self) -> str:
        return f"BlockNode({self.statements})"


class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, then_branch: BlockNode, else_branch: Optional[BlockNode] = None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __repr__(self) -> str:
        return f"IfNode(cond={self.condition}, then={self.then_branch}, else={self.else_branch})"


class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: BlockNode):
        self.condition = condition
        self.body = body

    def __repr__(self) -> str:
        return f"WhileNode(cond={self.condition}, body={self.body})"


class BinaryOpNode(ASTNode):
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"BinaryOpNode({self.left} {self.op} {self.right})"


class UnaryOpNode(ASTNode):
    def __init__(self, op: str, expr: ASTNode):
        self.op = op
        self.expr = expr

    def __repr__(self) -> str:
        return f"UnaryOpNode({self.op}{self.expr})"


class NumNode(ASTNode):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self) -> str:
        return f"NumNode({self.value})"


class VarNode(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"VarNode({self.name})"


# ==============================================================================
# Recursive Descent Parser
# ==============================================================================
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        return self.tokens[self.pos]

    def peek_next_token(self) -> Token:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.current_token()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def match(self, expected_type: TokenType) -> Token:
        curr = self.current_token()
        if curr.type == expected_type:
            return self.advance()
        raise SyntaxError(
            f"Parser error at line {curr.line}, col {curr.col}: expected {expected_type.name}, got {curr.type.name} ({curr.value})"
        )

    def parse(self) -> ProgramNode:
        statements = []
        while self.current_token().type != TokenType.EOF:
            statements.append(self.statement())
        return ProgramNode(statements)

    def statement(self) -> ASTNode:
        curr = self.current_token()
        if curr.type == TokenType.LET:
            return self.var_decl()
        elif curr.type == TokenType.IDENT:
            return self.assignment()
        elif curr.type == TokenType.PRINT:
            return self.print_stmt()
        elif curr.type == TokenType.IF:
            return self.if_stmt()
        elif curr.type == TokenType.WHILE:
            return self.while_stmt()
        elif curr.type == TokenType.LBRACE:
            return self.block()
        raise SyntaxError(f"Unexpected token in statement: {curr}")

    def var_decl(self) -> VarDeclNode:
        self.match(TokenType.LET)
        name_tok = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        expr = self.expression()
        self.match(TokenType.SEMI)
        return VarDeclNode(name_tok.value, expr)

    def assignment(self) -> AssignNode:
        name_tok = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        expr = self.expression()
        self.match(TokenType.SEMI)
        return AssignNode(name_tok.value, expr)

    def print_stmt(self) -> PrintNode:
        self.match(TokenType.PRINT)
        self.match(TokenType.LPAREN)
        expr = self.expression()
        self.match(TokenType.RPAREN)
        self.match(TokenType.SEMI)
        return PrintNode(expr)

    def block(self) -> BlockNode:
        self.match(TokenType.LBRACE)
        stmts = []
        while self.current_token().type not in (TokenType.RBRACE, TokenType.EOF):
            stmts.append(self.statement())
        self.match(TokenType.RBRACE)
        return BlockNode(stmts)

    def if_stmt(self) -> IfNode:
        self.match(TokenType.IF)
        self.match(TokenType.LPAREN)
        cond = self.condition()
        self.match(TokenType.RPAREN)
        then_b = self.block()
        else_b = None
        if self.current_token().type == TokenType.ELSE:
            self.match(TokenType.ELSE)
            else_b = self.block()
        return IfNode(cond, then_b, else_b)

    def while_stmt(self) -> WhileNode:
        self.match(TokenType.WHILE)
        self.match(TokenType.LPAREN)
        cond = self.condition()
        self.match(TokenType.RPAREN)
        body = self.block()
        return WhileNode(cond, body)

    def condition(self) -> ASTNode:
        left = self.expression()
        curr = self.current_token()
        rel_ops = {
            TokenType.EQ: "==",
            TokenType.NEQ: "!=",
            TokenType.LT: "<",
            TokenType.LTE: "<=",
            TokenType.GT: ">",
            TokenType.GTE: ">=",
        }
        if curr.type in rel_ops:
            op_str = rel_ops[curr.type]
            self.advance()
            right = self.expression()
            return BinaryOpNode(op_str, left, right)
        return left

    def expression(self) -> ASTNode:
        node = self.term()
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self.advance()
            right = self.term()
            node = BinaryOpNode(op_tok.value, node, right)
        return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current_token().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self.advance()
            right = self.factor()
            node = BinaryOpNode(op_tok.value, node, right)
        return node

    def factor(self) -> ASTNode:
        curr = self.current_token()
        if curr.type == TokenType.INT:
            self.advance()
            return NumNode(curr.value)
        elif curr.type == TokenType.IDENT:
            self.advance()
            return VarNode(curr.value)
        elif curr.type == TokenType.LPAREN:
            self.advance()
            node = self.expression()
            self.match(TokenType.RPAREN)
            return node
        elif curr.type == TokenType.MINUS:
            self.advance()
            return UnaryOpNode("-", self.factor())
        raise SyntaxError(f"Unexpected token in factor: {curr}")
