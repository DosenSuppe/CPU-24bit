"""
AST node definitions for the C-to-DASM compiler.

All nodes are simple dataclasses. Line numbers are tracked on every node for
error reporting.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


# -------------------------- Types --------------------------------------------

@dataclass
class CType:
    """
    Represents a C type. `kind` is one of:
        'int'   - 24-bit word
        'char'  - 24-bit word (same as int in this dialect, kept distinct for diagnostics)
        'void'  - return-only type
        'ptr'   - pointer to `inner`
        'array' - fixed-size array of `inner`, length `size`

    `is_const` only tracks variable-level constness ("you may not assign to
    this name"). It does NOT propagate through pointers — `const int *p` and
    `int *const p` are not distinguished. See SemanticAnalyzer for what's
    enforced.
    """
    kind: str
    inner: Optional["CType"] = None
    size: Optional[int] = None  # for arrays
    is_const: bool = False

    def IsScalar(self) -> bool:
        return self.kind in ("int", "char", "ptr")

    def IsPointer(self) -> bool:
        return self.kind == "ptr"

    def IsArray(self) -> bool:
        return self.kind == "array"

    def WordSize(self) -> int:
        """Storage size in 24-bit words."""
        if self.kind in ("int", "char", "ptr"):
            return 1
        if self.kind == "array":
            return self.size * self.inner.WordSize()
        if self.kind == "void":
            return 0
        raise ValueError(f"Unknown type kind: {self.kind}")

    def __str__(self) -> str:
        prefix = "const " if self.is_const else ""
        if self.kind == "ptr":
            return f"{prefix}{self.inner}*"
        if self.kind == "array":
            return f"{prefix}{self.inner}[{self.size}]"
        return f"{prefix}{self.kind}"


# -------------------------- Expressions --------------------------------------

@dataclass
class Expr:
    line: int = field(default=0, repr=False)
    col: int = field(default=0, repr=False)


@dataclass
class IntLit(Expr):
    value: int = 0


@dataclass
class CharLit(Expr):
    value: int = 0  # already converted to integer code point


@dataclass
class StringLit(Expr):
    value: str = ""


@dataclass
class Ident(Expr):
    name: str = ""


@dataclass
class BinaryOp(Expr):
    op: str = ""        # '+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>',
                        # '==', '!=', '<', '>', '<=', '>=', '&&', '||'
    left: Expr = None
    right: Expr = None


@dataclass
class UnaryOp(Expr):
    op: str = ""        # '-', '!', '~', '*', '&'
    operand: Expr = None


@dataclass
class Assign(Expr):
    op: str = "="       # '=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='
    target: Expr = None  # must be lvalue
    value: Expr = None


@dataclass
class Call(Expr):
    name: str = ""
    args: List[Expr] = field(default_factory=list)


@dataclass
class Index(Expr):
    array: Expr = None   # the array/pointer being indexed
    index: Expr = None   # the index expression


@dataclass
class Ternary(Expr):
    cond: Expr = None
    then_branch: Expr = None
    else_branch: Expr = None


@dataclass
class IncDec(Expr):
    op: str = "++"          # '++' or '--'
    is_post: bool = False    # False = prefix (++x), True = postfix (x++)
    target: Expr = None      # must be lvalue


# -------------------------- Statements ---------------------------------------

@dataclass
class Stmt:
    line: int = field(default=0, repr=False)
    col: int = field(default=0, repr=False)


@dataclass
class VarDecl(Stmt):
    ctype: CType = None
    name: str = ""
    init: Optional[Expr] = None  # initializer expression, or None
    slot: int = -1               # filled by SemanticAnalyzer (local frame slot)


@dataclass
class ExprStmt(Stmt):
    expr: Expr = None


@dataclass
class Block(Stmt):
    stmts: List[Stmt] = field(default_factory=list)


@dataclass
class If(Stmt):
    cond: Expr = None
    then_branch: Stmt = None
    else_branch: Optional[Stmt] = None


@dataclass
class While(Stmt):
    cond: Expr = None
    body: Stmt = None

@dataclass
class ForLoop(Stmt):
    init: Optional[Stmt] = None      # VarDecl, ExprStmt, or None
    cond: Optional[Expr] = None      # None means "always true"
    update: Optional[Expr] = None    # None means no-op
    body: Stmt = None

@dataclass
class Return(Stmt):
    value: Optional[Expr] = None


@dataclass
class Break(Stmt):
    pass


@dataclass
class Continue(Stmt):
    pass


@dataclass
class AsmStmt(Stmt):
    text: str = ""  # unescaped DASM string


# -------------------------- Top-level ----------------------------------------

@dataclass
class Param:
    ctype: CType = None
    name: str = ""
    slot: int = -1  # filled by SemanticAnalyzer (arg slot index, 0-based)


@dataclass
class FuncDef:
    ret_type: CType = None
    name: str = ""
    params: List[Param] = field(default_factory=list)
    body: Optional[Block] = None    # None for extern declarations
    line: int = 0
    is_extern: bool = False          # True = declared elsewhere, do not emit
    # Filled by SemanticAnalyzer:
    locals: List[VarDecl] = field(default_factory=list)  # all locals in declaration order
    frame_size: int = 0      # number of local slots (sum of WordSize for each local)
    callee_saves_used: List[str] = field(default_factory=list)  # registers actually touched
    # Flat name -> LocalSymbol map (set after semantic analysis).
    symbols: dict = field(default_factory=dict)


@dataclass
class GlobalDecl:
    ctype: CType = None
    name: str = ""
    init: Optional[Expr] = None  # IntLit/CharLit constant, or None (zero-init)
    line: int = 0
    is_extern: bool = False


@dataclass
class TranslationUnit:
    items: List[Union[FuncDef, GlobalDecl]] = field(default_factory=list)
