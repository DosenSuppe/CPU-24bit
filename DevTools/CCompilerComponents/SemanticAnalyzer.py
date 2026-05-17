"""
Semantic analysis for cc.py.

Walks the AST to:
  - Build global symbol table (functions, globals).
  - Build per-function local symbol table.
  - Assign frame slot indices to params and locals.
  - Compute per-function frame_size.
  - Tag VarDecl / Param nodes with their slot indices.
  - Surface basic errors: redeclared symbols, undefined symbols, void misuse.

Type checking is intentionally minimal in v1; the codegen treats every
scalar as a 24-bit word.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from CCompilerComponents.AST import (
    TranslationUnit, FuncDef, GlobalDecl, Param, VarDecl, Block, If, While,
    ForLoop, Return, Break, Continue, ExprStmt, AsmStmt, CType, BinaryOp,
    UnaryOp, Assign, Call, Index, Ternary, IncDec, IntLit, CharLit, StringLit,
    Ident, Expr, Stmt,
)
from CCompilerComponents.Exceptions import CSemanticError


@dataclass
class GlobalSymbol:
    name: str
    ctype: CType


@dataclass
class FuncSymbol:
    name: str
    ret_type: CType
    params: List[Param]


@dataclass
class LocalSymbol:
    name: str
    ctype: CType
    slot: int          # frame slot index (locals: positive; args: positive separately)
    is_param: bool


class SemanticAnalyzer:

    def __init__(self):
        self.globals: Dict[str, GlobalSymbol] = {}
        self.functions: Dict[str, FuncSymbol] = {}
        # Per-function state (reset for each function):
        self._current_func: Optional[FuncDef] = None
        self._scopes: List[Dict[str, LocalSymbol]] = []
        self._next_local_slot: int = 0   # cumulative slot count (in words)
        self._loop_depth: int = 0        # for break/continue validation

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def Analyze(self, pUnit: TranslationUnit) -> None:
        # Pass 1: gather global declarations and function signatures.
        for item in pUnit.items:
            if isinstance(item, GlobalDecl):
                if item.name in self.globals:
                    raise CSemanticError(f"Redeclared global '{item.name}'", item.line)
                self._ResolveStringInit(item.ctype, item.init, item.name, item.line)
                if item.ctype.is_const and item.init is None and not item.is_extern:
                    raise CSemanticError(
                        f"const global '{item.name}' must be initialized", item.line)
                self.globals[item.name] = GlobalSymbol(item.name, item.ctype)
            elif isinstance(item, FuncDef):
                if item.name in self.functions:
                    raise CSemanticError(f"Redeclared function '{item.name}'", item.line)
                self.functions[item.name] = FuncSymbol(item.name, item.ret_type, item.params)

        # Pass 2: analyze function bodies. Externs have no body to walk.
        for item in pUnit.items:
            if isinstance(item, FuncDef) and not item.is_extern:
                self._AnalyzeFunc(item)

    # ------------------------------------------------------------------
    # Function analysis
    # ------------------------------------------------------------------

    def _AnalyzeFunc(self, pFunc: FuncDef) -> None:
        self._current_func = pFunc
        self._scopes = [{}]
        self._next_local_slot = 0
        pFunc.locals = []
        pFunc.symbols = {}

        # Assign arg slots: 0-based, sized by type (all 1 word here).
        arg_slot = 0
        for p in pFunc.params:
            if p.ctype.kind == "void":
                raise CSemanticError(f"Parameter '{p.name}' cannot be void", pFunc.line)
            p.slot = arg_slot
            arg_slot += p.ctype.WordSize()
            sym = LocalSymbol(p.name, p.ctype, p.slot, is_param=True)
            self._scopes[0][p.name] = sym
            pFunc.symbols[p.name] = sym

        # Walk body
        self._AnalyzeBlock(pFunc.body)

        pFunc.frame_size = self._next_local_slot

    # ------------------------------------------------------------------
    # Statement walk
    # ------------------------------------------------------------------

    def _AnalyzeBlock(self, pBlock: Block) -> None:
        self._scopes.append({})
        for s in pBlock.stmts:
            self._AnalyzeStmt(s)
        self._scopes.pop()

    def _AnalyzeStmt(self, pStmt: Stmt) -> None:
        if isinstance(pStmt, VarDecl):
            self._AnalyzeVarDecl(pStmt)
        elif isinstance(pStmt, ExprStmt):
            self._AnalyzeExpr(pStmt.expr)
        elif isinstance(pStmt, Block):
            self._AnalyzeBlock(pStmt)
        elif isinstance(pStmt, If):
            self._AnalyzeExpr(pStmt.cond)
            self._AnalyzeStmt(pStmt.then_branch)
            if pStmt.else_branch:
                self._AnalyzeStmt(pStmt.else_branch)
        elif isinstance(pStmt, While):
            self._AnalyzeExpr(pStmt.cond)
            self._loop_depth += 1
            try:
                self._AnalyzeStmt(pStmt.body)
            finally:
                self._loop_depth -= 1
        elif isinstance(pStmt, ForLoop):
            if pStmt.init is not None:
                self._AnalyzeStmt(pStmt.init)
            if pStmt.cond is not None:
                self._AnalyzeExpr(pStmt.cond)
            if pStmt.update is not None:
                self._AnalyzeExpr(pStmt.update)
            self._loop_depth += 1
            try:
                self._AnalyzeStmt(pStmt.body)
            finally:
                self._loop_depth -= 1
        elif isinstance(pStmt, Break):
            if self._loop_depth == 0:
                raise CSemanticError("'break' outside of a loop", pStmt.line)
        elif isinstance(pStmt, Continue):
            if self._loop_depth == 0:
                raise CSemanticError("'continue' outside of a loop", pStmt.line)
        elif isinstance(pStmt, Return):
            if pStmt.value is not None:
                self._AnalyzeExpr(pStmt.value)
        elif isinstance(pStmt, AsmStmt):
            pass  # opaque
        else:
            raise CSemanticError(f"Unknown statement type {type(pStmt).__name__}", getattr(pStmt, "line", 0))

    def _AnalyzeVarDecl(self, pDecl: VarDecl) -> None:
        if pDecl.ctype.kind == "void":
            raise CSemanticError(f"Variable '{pDecl.name}' cannot be void", pDecl.line)
        # const requires an initializer (can't be left undefined).
        if pDecl.ctype.is_const and pDecl.init is None:
            raise CSemanticError(
                f"const variable '{pDecl.name}' must be initialized", pDecl.line)
        # String-literal array init: validates / fills in size before slot assignment.
        self._ResolveStringInit(pDecl.ctype, pDecl.init, pDecl.name, pDecl.line)
        # v1 disallows shadowing entirely — one namespace per function.
        if pDecl.name in self._current_func.symbols:
            raise CSemanticError(f"Redeclared local '{pDecl.name}'", pDecl.line)
        size = pDecl.ctype.WordSize()
        pDecl.slot = self._next_local_slot
        self._next_local_slot += size
        sym = LocalSymbol(pDecl.name, pDecl.ctype, pDecl.slot, is_param=False)
        self._scopes[-1][pDecl.name] = sym
        self._current_func.symbols[pDecl.name] = sym
        self._current_func.locals.append(pDecl)
        if pDecl.init is not None:
            if pDecl.ctype.IsArray():
                # Only string-literal initializers are supported; already
                # validated by _ResolveStringInit.
                if not isinstance(pDecl.init, StringLit):
                    raise CSemanticError(
                        "Only string-literal initializers are supported for arrays",
                        pDecl.line)
            else:
                self._AnalyzeExpr(pDecl.init)

    def _ResolveStringInit(self, pCType: CType, pInit: Optional[Expr],
                           pName: str, pLine: int) -> None:
        """If `pInit` is a StringLit and `pCType` is a char array, ensure the
        array has a size: either fill it in (size=None) or check it fits
        (string + NUL terminator)."""
        if not isinstance(pInit, StringLit):
            return
        if not pCType.IsArray() or pCType.inner.kind != "char":
            raise CSemanticError(
                f"String-literal initializer requires a char array, got {pCType}",
                pLine)
        needed = len(pInit.value) + 1  # +1 for NUL terminator
        if pCType.size is None:
            pCType.size = needed
        elif needed > pCType.size:
            raise CSemanticError(
                f"String literal too long for '{pName}' "
                f"(needs {needed} chars including NUL, array has {pCType.size})",
                pLine)

    # ------------------------------------------------------------------
    # Expression walk (very lightweight — just resolves identifiers)
    # ------------------------------------------------------------------

    def _AnalyzeExpr(self, pExpr: Expr) -> None:
        if isinstance(pExpr, (IntLit, CharLit, StringLit)):
            return
        if isinstance(pExpr, Ident):
            if not self._LookupName(pExpr.name):
                raise CSemanticError(f"Undefined identifier '{pExpr.name}'", pExpr.line)
            return
        if isinstance(pExpr, BinaryOp):
            self._AnalyzeExpr(pExpr.left)
            self._AnalyzeExpr(pExpr.right)
            return
        if isinstance(pExpr, UnaryOp):
            self._AnalyzeExpr(pExpr.operand)
            return
        if isinstance(pExpr, Assign):
            self._CheckLvalueWritable(pExpr.target, pExpr.line, "assign to")
            self._AnalyzeExpr(pExpr.target)
            self._AnalyzeExpr(pExpr.value)
            return
        if isinstance(pExpr, Call):
            for a in pExpr.args:
                self._AnalyzeExpr(a)
            if pExpr.name == "syscall":
                if len(pExpr.args) == 0:
                    raise CSemanticError("syscall needs at least the number argument", pExpr.line)
                return
            if pExpr.name not in self.functions:
                raise CSemanticError(f"Call to undefined function '{pExpr.name}'", pExpr.line)
            return
        if isinstance(pExpr, Index):
            self._AnalyzeExpr(pExpr.array)
            self._AnalyzeExpr(pExpr.index)
            return
        if isinstance(pExpr, Ternary):
            self._AnalyzeExpr(pExpr.cond)
            self._AnalyzeExpr(pExpr.then_branch)
            self._AnalyzeExpr(pExpr.else_branch)
            return
        if isinstance(pExpr, IncDec):
            self._CheckLvalueWritable(pExpr.target, pExpr.line,
                                      "increment" if pExpr.op == "++" else "decrement")
            self._AnalyzeExpr(pExpr.target)
            return
        raise CSemanticError(f"Unknown expression type {type(pExpr).__name__}", getattr(pExpr, "line", 0))

    # ------------------------------------------------------------------
    # Const / lvalue helpers
    # ------------------------------------------------------------------

    def _CheckLvalueWritable(self, pTarget: Expr, pLine: int, pVerb: str) -> None:
        """Reject `pVerb` (assignment/increment/decrement) when the target is a
        const variable. Only catches the simple Ident case — complex lvalues
        (`*p`, `a[i]`) aren't const-tracked through pointers in v1."""
        if isinstance(pTarget, Ident):
            ctype = self._GetIdentType(pTarget.name)
            if ctype is not None and ctype.is_const:
                raise CSemanticError(
                    f"Cannot {pVerb}: '{pTarget.name}' is const", pLine)

    def _GetIdentType(self, pName: str) -> Optional[CType]:
        if self._current_func is not None:
            sym = self._current_func.symbols.get(pName)
            if sym is not None:
                return sym.ctype
        g = self.globals.get(pName)
        if g is not None:
            return g.ctype
        return None

    # ------------------------------------------------------------------
    # Symbol lookup helpers
    # ------------------------------------------------------------------

    def _LookupName(self, pName: str) -> bool:
        """True if name resolves to a local/param/global/function."""
        for scope in reversed(self._scopes):
            if pName in scope:
                return True
        if pName in self.globals:
            return True
        if pName in self.functions:
            return True
        return False

    def LookupLocal(self, pName: str) -> Optional[LocalSymbol]:
        for scope in reversed(self._scopes):
            if pName in scope:
                return scope[pName]
        return None
