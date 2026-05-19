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
    TranslationUnit, FuncDef, GlobalDecl, StructDecl, StructDef, StructField,
    Param, VarDecl, Block, If, While, ForLoop, Return, Break, Continue,
    ExprStmt, AsmStmt, CType, BinaryOp, UnaryOp, Assign, Call, Index,
    MemberAccess, Ternary, IncDec, Cast, SizeOf, IntLit, CharLit, StringLit,
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
        # struct name -> StructDef. Forward declarations live here as
        # entries with is_complete=False.
        self.structs: Dict[str, StructDef] = {}
        # Per-function state (reset for each function):
        self._current_func: Optional[FuncDef] = None
        self._scopes: List[Dict[str, LocalSymbol]] = []
        self._next_local_slot: int = 0   # cumulative slot count (in words)
        self._loop_depth: int = 0        # for break/continue validation

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def Analyze(self, pUnit: TranslationUnit) -> None:
        # Pass 0: register and (eagerly) populate struct definitions in source
        # order. Forward declarations register an incomplete entry that a later
        # full definition can upgrade. Self-referential structs work because we
        # reserve the name BEFORE walking the fields.
        for item in pUnit.items:
            if isinstance(item, StructDecl):
                self._RegisterStruct(item)

        # Pass 1: gather global declarations and function signatures.
        # Every CType encountered here is resolved (struct_def attached) so
        # WordSize() works downstream without further bookkeeping.
        for item in pUnit.items:
            if isinstance(item, GlobalDecl):
                self._ResolveCType(item.ctype, item.line)
                if item.ctype.IsStruct() and not item.ctype.struct_def.is_complete:
                    raise CSemanticError(
                        f"Global '{item.name}' has incomplete struct type "
                        f"'{item.ctype}'", item.line)
                if item.name in self.globals:
                    raise CSemanticError(f"Redeclared global '{item.name}'", item.line)
                self._ResolveStringInit(item.ctype, item.init, item.name, item.line)
                if item.ctype.is_const and item.init is None and not item.is_extern:
                    raise CSemanticError(
                        f"const global '{item.name}' must be initialized", item.line)
                self.globals[item.name] = GlobalSymbol(item.name, item.ctype)
            elif isinstance(item, FuncDef):
                self._ResolveCType(item.ret_type, item.line)
                if item.ret_type.IsStruct():
                    raise CSemanticError(
                        f"Function '{item.name}' returns struct by value, which "
                        f"is not supported in v1 (return 'struct {item.ret_type.struct_name} *' instead)",
                        item.line)
                for p in item.params:
                    self._ResolveCType(p.ctype, item.line)
                    if p.ctype.IsStruct():
                        raise CSemanticError(
                            f"Param '{p.name}' of '{item.name}': struct-by-value "
                            f"is not supported in v1 (use 'struct {p.ctype.struct_name} *')",
                            item.line)
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
        # Resolve any struct references in the type so WordSize() works.
        self._ResolveCType(pDecl.ctype, pDecl.line)
        if pDecl.ctype.kind == "void":
            raise CSemanticError(f"Variable '{pDecl.name}' cannot be void", pDecl.line)
        # Incomplete struct can't be declared by value (size unknown).
        if pDecl.ctype.IsStruct() and not pDecl.ctype.struct_def.is_complete:
            raise CSemanticError(
                f"Local '{pDecl.name}' has incomplete struct type "
                f"'{pDecl.ctype}' (only pointers to incomplete structs are allowed)",
                pDecl.line)
        if pDecl.ctype.IsArray() and pDecl.ctype.inner.IsStruct():
            # Array of struct — make sure the element type is fully resolved
            # and complete; WordSize() will multiply through.
            self._ResolveCType(pDecl.ctype.inner, pDecl.line)
            if not pDecl.ctype.inner.struct_def.is_complete:
                raise CSemanticError(
                    f"Local '{pDecl.name}': array of incomplete struct '{pDecl.ctype.inner}'",
                    pDecl.line)
        if pDecl.ctype.IsStruct() and pDecl.init is not None:
            raise CSemanticError(
                "Struct initializers are not supported in v1; "
                "assign fields individually after declaration", pDecl.line)
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
            # Reject whole-struct assignment in v1 — would require a multi-word
            # memcpy-style codegen path. Field-by-field assignment works fine.
            target_t = self._TypeOfExpr(pExpr.target)
            if target_t is not None and target_t.IsStruct():
                raise CSemanticError(
                    "Struct-to-struct assignment is not supported in v1 "
                    "(copy field-by-field, or use pointers)", pExpr.line)
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
        if isinstance(pExpr, Cast):
            self._ResolveCType(pExpr.target_type, pExpr.line)
            if pExpr.target_type.kind == "void":
                raise CSemanticError("Cannot cast to void", pExpr.line)
            if pExpr.target_type.IsStruct():
                raise CSemanticError(
                    f"Cannot cast to struct type '{pExpr.target_type}' "
                    f"(use pointer-to-struct instead)", pExpr.line)
            self._AnalyzeExpr(pExpr.operand)
            return
        if isinstance(pExpr, SizeOf):
            if pExpr.target_type is not None:
                self._ResolveCType(pExpr.target_type, pExpr.line)
                if pExpr.target_type.kind == "void":
                    raise CSemanticError("sizeof(void) is not allowed", pExpr.line)
                if pExpr.target_type.IsStruct() and not pExpr.target_type.struct_def.is_complete:
                    raise CSemanticError(
                        f"sizeof on incomplete '{pExpr.target_type}'", pExpr.line)
            else:
                # sizeof expr — walk for diagnostics (operand is unevaluated
                # in C, but we still verify it's well-formed).
                self._AnalyzeExpr(pExpr.target)
            return
        if isinstance(pExpr, MemberAccess):
            self._AnalyzeExpr(pExpr.target)
            target_t = self._TypeOfExpr(pExpr.target)
            if target_t is None:
                raise CSemanticError(
                    f"Cannot determine type of target for '{'->' if pExpr.via_ptr else '.'}{pExpr.field}'",
                    pExpr.line)
            if pExpr.via_ptr:
                if not target_t.IsPointer() or not target_t.inner.IsStruct():
                    raise CSemanticError(
                        f"Operator '->' requires pointer-to-struct, got '{target_t}'",
                        pExpr.line)
                struct_t = target_t.inner
            else:
                if not target_t.IsStruct():
                    raise CSemanticError(
                        f"Operator '.' requires struct, got '{target_t}'",
                        pExpr.line)
                struct_t = target_t
            # struct_t should already be resolved (it came from a resolved
            # variable declaration), but defend against it.
            self._ResolveCType(struct_t, pExpr.line)
            sd = struct_t.struct_def
            if sd is None or not sd.is_complete:
                raise CSemanticError(
                    f"Member access on incomplete '{struct_t}'", pExpr.line)
            field = sd.FindField(pExpr.field)
            if field is None:
                raise CSemanticError(
                    f"'struct {sd.name}' has no field '{pExpr.field}'",
                    pExpr.line)
            return
        raise CSemanticError(f"Unknown expression type {type(pExpr).__name__}", getattr(pExpr, "line", 0))

    # ------------------------------------------------------------------
    # Const / lvalue helpers
    # ------------------------------------------------------------------

    def _CheckLvalueWritable(self, pTarget: Expr, pLine: int, pVerb: str) -> None:
        """Reject `pVerb` (assignment/increment/decrement) when the target is a
        const variable. Catches the simple Ident case and `.field` access on a
        const struct. Const-pointed-to (`const T *p` → `*p`) is not tracked in v1."""
        if isinstance(pTarget, Ident):
            ctype = self._GetIdentType(pTarget.name)
            if ctype is not None and ctype.is_const:
                raise CSemanticError(
                    f"Cannot {pVerb}: '{pTarget.name}' is const", pLine)
        elif isinstance(pTarget, MemberAccess) and not pTarget.via_ptr:
            # `.field` on a const struct: blocked. `->field` on a pointer
            # to a const struct isn't tracked through the pointer.
            base_t = self._TypeOfExpr(pTarget.target)
            if base_t is not None and base_t.is_const:
                raise CSemanticError(
                    f"Cannot {pVerb}: containing struct is const", pLine)

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

    # ------------------------------------------------------------------
    # Struct registration & CType resolution
    # ------------------------------------------------------------------

    def _RegisterStruct(self, pDecl: StructDecl) -> None:
        """Add or upgrade a struct entry in `self.structs`.

        Repeat forward declarations are idempotent. A full body upgrades any
        existing forward declaration of the same name in place — by mutating
        the existing StructDef, so CTypes that already reference it (via
        `struct_def`) see the upgrade for free.
        """
        existing = self.structs.get(pDecl.name)

        if pDecl.is_forward:
            if existing is None:
                self.structs[pDecl.name] = StructDef(
                    name=pDecl.name, fields=[], word_size=0,
                    is_complete=False, line=pDecl.line)
            return  # forward redeclarations are fine

        # Full definition. Reject redefinition of an already-complete struct.
        if existing is not None and existing.is_complete:
            raise CSemanticError(
                f"Redeclared 'struct {pDecl.name}'", pDecl.line)

        # Reserve the name as incomplete BEFORE walking fields, so that fields
        # can self-reference via pointer (`struct Node { struct Node *next; }`).
        if existing is None:
            existing = StructDef(name=pDecl.name, fields=[], word_size=0,
                                 is_complete=False, line=pDecl.line)
            self.structs[pDecl.name] = existing

        # Resolve each field type, compute offsets, and accumulate size.
        offset = 0
        resolved: List[StructField] = []
        for f in pDecl.fields:
            self._ResolveCType(f.ctype, f.line)
            if f.ctype.kind == "void":
                raise CSemanticError(
                    f"Field '{f.name}' cannot be void", f.line)
            # By-value struct field must be complete. Self-reference would
            # mean infinite recursion, so it MUST go through a pointer.
            if f.ctype.IsStruct() and not f.ctype.struct_def.is_complete:
                raise CSemanticError(
                    f"Field '{f.name}' has incomplete struct type "
                    f"'{f.ctype}' (use a pointer instead)", f.line)
            if any(rf.name == f.name for rf in resolved):
                raise CSemanticError(
                    f"Duplicate field '{f.name}' in struct {pDecl.name}",
                    f.line)
            f.offset = offset
            offset += f.ctype.WordSize()
            resolved.append(f)

        # Upgrade the existing entry IN PLACE so any CType that has already
        # captured `struct_def` sees the new fields/size automatically.
        existing.fields = resolved
        existing.word_size = offset
        existing.is_complete = True

    def _ResolveCType(self, pType: CType, pLine: int) -> None:
        """Recursively walk a CType, attaching StructDef references to any
        struct CTypes encountered. Idempotent — safe to call multiple times.
        Raises CSemanticError on unknown struct names."""
        if pType is None:
            return
        if pType.kind == "struct":
            if pType.struct_def is None:
                sd = self.structs.get(pType.struct_name)
                if sd is None:
                    raise CSemanticError(
                        f"Unknown 'struct {pType.struct_name}'", pLine)
                pType.struct_def = sd
            return
        # Pointer and array carry an inner type that also needs resolving.
        if pType.inner is not None:
            self._ResolveCType(pType.inner, pLine)

    # ------------------------------------------------------------------
    # Expression type inference (used by MemberAccess and friends)
    # ------------------------------------------------------------------

    def _TypeOfExpr(self, pExpr: Expr) -> Optional[CType]:
        """Best-effort static type of an expression. Returns None when the
        type can't be determined (e.g. malformed AST mid-analysis). Designed
        to be extensible — new expression kinds just add a branch.

        Currently used for: member-access target validation, const checking
        on `.field`, struct-assignment rejection.
        """
        if isinstance(pExpr, IntLit):
            return CType(kind="int")
        if isinstance(pExpr, CharLit):
            return CType(kind="char")
        if isinstance(pExpr, StringLit):
            return CType(kind="ptr", inner=CType(kind="char"))
        if isinstance(pExpr, Ident):
            return self._GetIdentType(pExpr.name)
        if isinstance(pExpr, UnaryOp):
            if pExpr.op == "*":
                inner = self._TypeOfExpr(pExpr.operand)
                if inner is not None and inner.IsPointer():
                    return inner.inner
                return None
            if pExpr.op == "&":
                inner = self._TypeOfExpr(pExpr.operand)
                if inner is None:
                    return None
                return CType(kind="ptr", inner=inner)
            return CType(kind="int")
        if isinstance(pExpr, BinaryOp):
            # Approximation: pointer arithmetic preserves the pointer type;
            # everything else collapses to int. Good enough for v1.
            lt = self._TypeOfExpr(pExpr.left)
            rt = self._TypeOfExpr(pExpr.right)
            if lt is not None and lt.IsPointer():
                return lt
            if rt is not None and rt.IsPointer():
                return rt
            return CType(kind="int")
        if isinstance(pExpr, Index):
            base = self._TypeOfExpr(pExpr.array)
            if base is None:
                return None
            if base.IsArray() or base.IsPointer():
                return base.inner
            return None
        if isinstance(pExpr, MemberAccess):
            target_t = self._TypeOfExpr(pExpr.target)
            if target_t is None:
                return None
            if pExpr.via_ptr:
                if not target_t.IsPointer() or not target_t.inner.IsStruct():
                    return None
                sd = target_t.inner.struct_def
            else:
                if not target_t.IsStruct():
                    return None
                sd = target_t.struct_def
            if sd is None:
                return None
            f = sd.FindField(pExpr.field)
            return f.ctype if f is not None else None
        if isinstance(pExpr, Call):
            if pExpr.name == "syscall":
                return CType(kind="int")
            f = self.functions.get(pExpr.name)
            return f.ret_type if f else None
        if isinstance(pExpr, Assign):
            return self._TypeOfExpr(pExpr.target)
        if isinstance(pExpr, Ternary):
            # Assume both branches have the same type; pick whichever resolves.
            t = self._TypeOfExpr(pExpr.then_branch)
            return t if t is not None else self._TypeOfExpr(pExpr.else_branch)
        if isinstance(pExpr, IncDec):
            return self._TypeOfExpr(pExpr.target)
        if isinstance(pExpr, Cast):
            return pExpr.target_type
        if isinstance(pExpr, SizeOf):
            return CType(kind="int")
        return None
