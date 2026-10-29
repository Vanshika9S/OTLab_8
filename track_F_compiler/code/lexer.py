"""
lexer.py
--------
Lexical Analyzer for ToyLang.
Tokenizes source code into a sequence of strongly-typed tokens.
"""

import enum
import re
from typing import List, Optional, Tuple, Any


class TokenType(enum.Enum):
    # Keywords
    LET = "LET"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    PRINT = "PRINT"

    # Identifiers & Literals
    IDENT = "IDENT"
    INT = "INT"

    # Operators
    ASSIGN = "ASSIGN"       # =
    PLUS = "PLUS"           # +
    MINUS = "MINUS"         # -
    STAR = "STAR"           # *
    SLASH = "SLASH"         # /
    PERCENT = "PERCENT"     # %

    # Relational Operators
    EQ = "EQ"               # ==
    NEQ = "NEQ"             # !=
    LT = "LT"               # <
    LTE = "LTE"             # <=
    GT = "GT"               # >
    GTE = "GTE"             # >=

    # Delimiters
    LPAREN = "LPAREN"       # (
    RPAREN = "RPAREN"       # )
    LBRACE = "LBRACE"       # {
    RBRACE = "RBRACE"       # }
    SEMI = "SEMI"           # ;

    EOF = "EOF"


class Token:
    def __init__(self, type_: TokenType, value: Any = None, line: int = 1, col: int = 1):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, line={self.line}, col={self.col})"


KEYWORDS = {
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
}


class Lexer:
    """Tokenizes ToyLang source text into a stream of Token objects."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(source)

    def peek(self) -> Optional[str]:
        if self.pos < self.length:
            return self.source[self.pos]
        return None

    def advance(self) -> Optional[str]:
        if self.pos < self.length:
            ch = self.source[self.pos]
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            return ch
        return None

    def skip_whitespace_and_comments(self):
        while self.pos < self.length:
            ch = self.peek()
            if ch in (" ", "\t", "\r", "\n"):
                self.advance()
            elif ch == "/" and self.pos + 1 < self.length and self.source[self.pos + 1] == "/":
                # Single-line comment: skip until newline
                while self.pos < self.length and self.peek() != "\n":
                    self.advance()
            elif ch == "/" and self.pos + 1 < self.length and self.source[self.pos + 1] == "*":
                # Multi-line comment: skip until */
                self.advance()
                self.advance()
                while self.pos < self.length:
                    if self.peek() == "*" and self.pos + 1 < self.length and self.source[self.pos + 1] == "/":
                        self.advance()
                        self.advance()
                        break
                    self.advance()
            else:
                break

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < self.length:
            self.skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            ch = self.peek()
            col = self.col
            line = self.line

            # Numbers
            if ch.isdigit():
                num_str = ""
                while self.peek() and self.peek().isdigit():
                    num_str += self.advance()
                tokens.append(Token(TokenType.INT, int(num_str), line, col))
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == "_":
                ident_str = ""
                while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
                    ident_str += self.advance()
                ttype = KEYWORDS.get(ident_str, TokenType.IDENT)
                tokens.append(Token(ttype, ident_str, line, col))
                continue

            # Two-character operators
            if ch == "=" and self.pos + 1 < self.length and self.source[self.pos + 1] == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.EQ, "==", line, col))
                continue
            if ch == "!" and self.pos + 1 < self.length and self.source[self.pos + 1] == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.NEQ, "!=", line, col))
                continue
            if ch == "<" and self.pos + 1 < self.length and self.source[self.pos + 1] == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.LTE, "<=", line, col))
                continue
            if ch == ">" and self.pos + 1 < self.length and self.source[self.pos + 1] == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.GTE, ">=", line, col))
                continue

            # Single-character tokens
            single_map = {
                "=": TokenType.ASSIGN,
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "<": TokenType.LT,
                ">": TokenType.GT,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ";": TokenType.SEMI,
            }

            if ch in single_map:
                self.advance()
                tokens.append(Token(single_map[ch], ch, line, col))
                continue

            raise SyntaxError(f"Unexpected character '{ch}' at line {line}, col {col}")

        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens
