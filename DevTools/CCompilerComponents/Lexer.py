"""
C lexer for the cc.py compiler.

Tokenizes the supported C subset. Tracks line/column for error reporting.
"""

from dataclasses import dataclass
from typing import List

from CCompilerComponents.Exceptions import CLexError


# Token kinds
TK_INT_LIT     = "INT_LIT"
TK_CHAR_LIT    = "CHAR_LIT"
TK_STRING_LIT  = "STRING_LIT"
TK_IDENT       = "IDENT"
TK_KEYWORD     = "KEYWORD"
TK_PUNCT       = "PUNCT"
TK_EOF         = "EOF"


KEYWORDS = {
    "int", "char", "void",
    "if", "else", "while", "for", "return",
    "break", "continue", "const",
    "struct",
    "sizeof",
    "asm", "syscall", "extern",
}


# Multi-character punctuators, sorted longest-first.
# Note: "++"/"--"/"->" must precede their single-char prefixes so greedy match picks them.
MULTI_PUNCT = [
    "<<=", ">>=",
    "==", "!=", "<=", ">=", "<<", ">>",
    "&&", "||",
    "++", "--", "->",
    "+=", "-=", "*=", "/=", "%=",
    "&=", "|=", "^=",
]

SINGLE_PUNCT = set("+-*/%&|^~!=<>(){}[],;?:.")


@dataclass
class Token:
    kind: str
    value: object
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, L{self.line}:{self.col})"


class Lexer:

    def __init__(self, pSource: str):
        self.src = pSource
        self.pos = 0
        self.line = 1
        self.col = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def Tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            self._SkipWhitespaceAndComments()
            if self.pos >= len(self.src):
                tokens.append(Token(TK_EOF, None, self.line, self.col))
                return tokens

            startLine = self.line
            startCol = self.col
            c = self.src[self.pos]

            if c.isdigit():
                tokens.append(self._LexNumber(startLine, startCol))
            elif c.isalpha() or c == "_":
                tokens.append(self._LexIdentOrKeyword(startLine, startCol))
            elif c == "'":
                tokens.append(self._LexCharLit(startLine, startCol))
            elif c == '"':
                tokens.append(self._LexStringLit(startLine, startCol))
            else:
                tokens.append(self._LexPunct(startLine, startCol))

    # ------------------------------------------------------------------
    # Source helpers
    # ------------------------------------------------------------------

    def _Peek(self, pOffset: int = 0) -> str:
        idx = self.pos + pOffset
        return self.src[idx] if idx < len(self.src) else ""

    def _Advance(self) -> str:
        c = self.src[self.pos]
        self.pos += 1
        if c == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def _SkipWhitespaceAndComments(self) -> None:
        while self.pos < len(self.src):
            c = self.src[self.pos]
            if c.isspace():
                self._Advance()
                continue
            if c == "/" and self._Peek(1) == "/":
                # Line comment
                while self.pos < len(self.src) and self.src[self.pos] != "\n":
                    self._Advance()
                continue
            if c == "/" and self._Peek(1) == "*":
                # Block comment
                self._Advance(); self._Advance()
                while self.pos < len(self.src):
                    if self.src[self.pos] == "*" and self._Peek(1) == "/":
                        self._Advance(); self._Advance()
                        break
                    self._Advance()
                else:
                    raise CLexError("Unterminated block comment", self.line, self.col)
                continue
            break

    # ------------------------------------------------------------------
    # Lexers per token kind
    # ------------------------------------------------------------------

    def _LexNumber(self, pLine: int, pCol: int) -> Token:
        start = self.pos
        # 0x / 0X hex literal
        if self.src[self.pos] == "0" and self._Peek(1) in ("x", "X"):
            self._Advance(); self._Advance()
            digits_start = self.pos
            while self.pos < len(self.src) and self._IsHexDigit(self.src[self.pos]):
                self._Advance()
            if self.pos == digits_start:
                raise CLexError("Hex literal needs digits", pLine, pCol)
            value = int(self.src[start:self.pos], 16)
        else:
            while self.pos < len(self.src) and self.src[self.pos].isdigit():
                self._Advance()
            value = int(self.src[start:self.pos], 10)
        return Token(TK_INT_LIT, value & 0xFFFFFF, pLine, pCol)

    @staticmethod
    def _IsHexDigit(c: str) -> bool:
        return c.isdigit() or c.lower() in ("a", "b", "c", "d", "e", "f")

    def _LexIdentOrKeyword(self, pLine: int, pCol: int) -> Token:
        start = self.pos
        while self.pos < len(self.src) and (self.src[self.pos].isalnum() or self.src[self.pos] == "_"):
            self._Advance()
        text = self.src[start:self.pos]
        if text in KEYWORDS:
            return Token(TK_KEYWORD, text, pLine, pCol)
        return Token(TK_IDENT, text, pLine, pCol)

    def _LexCharLit(self, pLine: int, pCol: int) -> Token:
        self._Advance()  # opening quote
        if self.pos >= len(self.src):
            raise CLexError("Unterminated character literal", pLine, pCol)
        c = self.src[self.pos]
        if c == "\\":
            self._Advance()
            esc = self._Advance()
            value = self._UnescapeChar(esc, pLine, pCol)
        else:
            value = ord(c)
            self._Advance()
        if self.pos >= len(self.src) or self.src[self.pos] != "'":
            raise CLexError("Unterminated character literal", pLine, pCol)
        self._Advance()  # closing quote
        return Token(TK_CHAR_LIT, value & 0xFFFFFF, pLine, pCol)

    def _LexStringLit(self, pLine: int, pCol: int) -> Token:
        self._Advance()  # opening quote
        chars = []
        while self.pos < len(self.src) and self.src[self.pos] != '"':
            c = self.src[self.pos]
            if c == "\\":
                self._Advance()
                if self.pos >= len(self.src):
                    raise CLexError("Unterminated string escape", pLine, pCol)
                esc = self._Advance()
                chars.append(chr(self._UnescapeChar(esc, pLine, pCol)))
            elif c == "\n":
                raise CLexError("Newline in string literal", self.line, self.col)
            else:
                chars.append(c)
                self._Advance()
        if self.pos >= len(self.src):
            raise CLexError("Unterminated string literal", pLine, pCol)
        self._Advance()  # closing quote
        return Token(TK_STRING_LIT, "".join(chars), pLine, pCol)

    @staticmethod
    def _UnescapeChar(pEsc: str, pLine: int, pCol: int) -> int:
        table = {
            "n": 0x0A, "t": 0x09, "r": 0x0D, "0": 0x00,
            "\\": ord("\\"), "'": ord("'"), '"': ord('"'),
            "b": 0x08, "f": 0x0C, "v": 0x0B, "a": 0x07,
        }
        if pEsc in table:
            return table[pEsc]
        raise CLexError(f"Unknown escape \\{pEsc}", pLine, pCol)

    def _LexPunct(self, pLine: int, pCol: int) -> Token:
        # Try multi-character punctuators first
        for op in MULTI_PUNCT:
            if self.src.startswith(op, self.pos):
                for _ in op:
                    self._Advance()
                return Token(TK_PUNCT, op, pLine, pCol)
        c = self.src[self.pos]
        if c in SINGLE_PUNCT:
            self._Advance()
            return Token(TK_PUNCT, c, pLine, pCol)
        raise CLexError(f"Unexpected character {c!r}", pLine, pCol)
