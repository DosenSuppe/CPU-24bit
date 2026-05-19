"""
Code generator: walks the AST and emits DASM into an AsmEmitter.

Strategy: pure accumulator-based. Every expression result ends in REA.
Binary ops evaluate RHS first (PUSH), then LHS (REA), then POP REB,
then `OP REA, REB` so that REA = LHS op RHS even for non-commutative ops.

Locals/params live on the stack. Reads/writes go through REY (effective
address) using REZ as the offset constant. The frame pointer is REX.
"""

from typing import List, Optional

from CCompilerComponents import CallingConvention as CC
from CCompilerComponents.AST import (
    TranslationUnit, FuncDef, GlobalDecl, StructDecl, Block, VarDecl, If, While,
    ForLoop, Return, Break, Continue, ExprStmt, AsmStmt, Expr, Stmt, IntLit,
    CharLit, StringLit, Ident, BinaryOp, UnaryOp, Assign, Call, Index,
    MemberAccess, Ternary, IncDec, Cast, SizeOf, CType,
)
from CCompilerComponents.AsmEmitter import AsmEmitter
from CCompilerComponents.LabelGenerator import LabelGenerator
from CCompilerComponents.SemanticAnalyzer import SemanticAnalyzer
from CCompilerComponents.Exceptions import CCodeGenError
from CCompilerComponents import Builtins


# Binary ops that map directly to a 2-operand ALU instruction.
DIRECT_OPS = {
    "+":  "ADD",
    "-":  "SUB",
    "*":  "MUL",
    "/":  "DIV",
    "&":  "AND",
    "|":  "OR",
    "^":  "XOR",
    "<<": "SHL",
    ">>": "SHR",
}

# Compound assignment shorthand -> underlying binary op
COMPOUND_OPS = {
    "+=":  "+",
    "-=":  "-",
    "*=":  "*",
    "/=":  "/",
    "%=":  "%",
    "&=":  "&",
    "|=":  "|",
    "^=":  "^",
    "<<=": "<<",
    ">>=": ">>",
}


class CodeGen:

    def __init__(self, pAnalyzer: SemanticAnalyzer, pSourceName: str):
        self.analyzer = pAnalyzer
        self.source_name = pSourceName
        self.emitter = AsmEmitter()
        self.labels = LabelGenerator()
        # Per-function state (set in _GenFunc):
        self._current_func: FuncDef = None
        self._func_label_prefix: str = ""
        # Pending string literals to emit in .CData
        self._string_literals: List[tuple] = []  # (label, text)
        # Stack of (break_label, continue_label) for the nearest enclosing
        # loops. break/continue inside a nested if/block walk up the stack.
        self._loop_stack: List[tuple] = []
        # When True, skip the .Kernel boot stub (library mode).
        self.no_entry: bool = False
        # Object-file dependencies to declare via !IMPORT at the top of the
        # emitted .asm. Lets the linker pull in sibling objects (like the
        # heap library) without command-line plumbing.
        self.imports: List[str] = []

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def Generate(self, pUnit: TranslationUnit) -> str:
        self._EmitHeader()
        self._EmitKernel(pUnit)
        self._EmitCCode(pUnit)
        self._EmitCData(pUnit)
        return self.emitter.Result()

    # ------------------------------------------------------------------
    # File sections
    # ------------------------------------------------------------------

    def _EmitHeader(self) -> None:
        e = self.emitter
        e.Comment("=" * 60)
        e.Comment(f"cc.py output for {self.source_name}")
        e.Comment("Auto-generated. Do not edit by hand.")
        e.Comment("=" * 60)
        # Linker dependencies from `--import` flags. Emit before any segment.
        for imp in self.imports:
            e.Raw(f'!IMPORT "{imp}"')

    def _EmitKernel(self, pUnit: TranslationUnit) -> None:
        # Library mode: caller suppresses the boot stub entirely.
        if self.no_entry:
            return
        # Only emit a boot stub when this source actually DEFINES `main`.
        # An extern declaration of main doesn't trigger the stub.
        has_main = any(isinstance(item, FuncDef) and item.name == "main"
                       and not item.is_extern
                       for item in pUnit.items)
        if not has_main:
            return
        e = self.emitter
        e.Segment("Kernel")
        e.Comment("Boot stub: set up stack, call main, halt with return value in REA.")
        e.Instr("SET_SP", "$Stack.Start")
        e.Instr("SET_IVR", "$InterruptVector.Start")
        e.Instr("CALL", "main")
        e.Instr("HALT")

    def _EmitCCode(self, pUnit: TranslationUnit) -> None:
        e = self.emitter
        # Only emit a .CCode segment if there are actual function bodies.
        # Externs contribute nothing; pure-extern files emit no code segment.
        funcs = [it for it in pUnit.items
                 if isinstance(it, FuncDef) and not it.is_extern]
        if not funcs:
            return
        e.Segment("CCode")
        # Emit main first if present so it sits at the top of .CCode for readability.
        funcs.sort(key=lambda f: (0 if f.name == "main" else 1))
        for f in funcs:
            self._GenFunc(f)

    def _EmitCData(self, pUnit: TranslationUnit) -> None:
        e = self.emitter
        # Extern globals carry no storage in this file; skip them.
        globals_list = [it for it in pUnit.items
                        if isinstance(it, GlobalDecl) and not it.is_extern]
        if not globals_list and not self._string_literals:
            return
        e.Segment("CData")
        for g in globals_list:
            self._GenGlobal(g)
        for label, text in self._string_literals:
            self._GenStringLit(label, text)

    # ------------------------------------------------------------------
    # Globals / string literals
    # ------------------------------------------------------------------

    def _GenGlobal(self, pGlobal: GlobalDecl) -> None:
        e = self.emitter
        e.Label(pGlobal.name)
        if pGlobal.ctype.IsArray():
            if isinstance(pGlobal.init, StringLit):
                # String literal: emit chars then NUL; pad the rest with zeros.
                # Char arrays only — analyzer guarantees inner.kind == 'char'.
                n = pGlobal.ctype.size  # element count (1 word each for char)
                chars = [self._Imm(ord(c)) for c in pGlobal.init.value] + ["#0"]
                pad = ["#0"] * (n - len(chars))
                e.DataWord(*(chars + pad),
                           pComment=f'{pGlobal.ctype} = "{pGlobal.init.value}"')
            else:
                # Zero-init. Use WordSize() so arrays of multi-word elements
                # (e.g. struct elements) get the right total.
                words = ["#0"] * pGlobal.ctype.WordSize()
                e.DataWord(*words, pComment=f"{pGlobal.ctype}")
        elif pGlobal.ctype.IsStruct():
            # Struct globals: zero-init (initializer lists not supported).
            words = ["#0"] * pGlobal.ctype.WordSize()
            e.DataWord(*words, pComment=f"{pGlobal.ctype}")
        else:
            init_val = "#0"
            if pGlobal.init is not None:
                if isinstance(pGlobal.init, IntLit):
                    init_val = self._Imm(pGlobal.init.value)
                elif isinstance(pGlobal.init, CharLit):
                    init_val = self._Imm(pGlobal.init.value)
                else:
                    raise CCodeGenError(
                        f"Global '{pGlobal.name}' must be initialized with a literal constant"
                    )
            e.DataWord(init_val, pComment=str(pGlobal.ctype))

    def _GenStringLit(self, pLabel: str, pText: str) -> None:
        e = self.emitter
        e.Label(pLabel)
        words = [self._Imm(ord(c)) for c in pText] + ["#0"]
        e.DataWord(*words, pComment=f'"{pText}" + NUL')

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------

    def _GenFunc(self, pFunc: FuncDef) -> None:
        e = self.emitter
        self._current_func = pFunc
        self._func_label_prefix = pFunc.name
        # Keep the analyzer's per-function state aligned so its helpers
        # (notably _TypeOfExpr -> _GetIdentType) resolve identifiers against
        # the function currently being emitted, not the last one analyzed.
        self.analyzer._current_func = pFunc

        param_list = ", ".join(f"{p.ctype} {p.name}" for p in pFunc.params)
        e.Blank()
        e.Header(f"function {pFunc.name}({param_list})")
        e.Comment(f"frame: {pFunc.frame_size} local word(s)")
        e.Label(pFunc.name)

        # Prologue
        e.Instr("PUSH", CC.FP_REG, pComment="save old FP")
        e.Instr("GET_SP", CC.FP_REG, pComment="FP = SP")

        # Reserve local slots. Each PUSH #0 reserves 1 word. Slot reservation
        # happens once up front (we need the full frame size known here so the
        # epilogue can SET_SP_R back), but the *initializer expressions* must
        # run at their source-order position — not hoisted to function entry —
        # otherwise an init like `int x = some_func(y)` runs before `y` has
        # been computed by earlier statements.
        for _ in range(pFunc.frame_size):
            e.Instr("PUSH", "#0", pComment="reserve local")

        # Body: copy each param's value into its local "home" if needed.
        # In our model params are already addressable on the stack (caller pushed them).
        # No copy needed — _LoadIdent computes their FP-relative address directly.

        # Emit each statement. VarDecls run their initializer here (in source
        # order); the slot itself was reserved above. Nested-block VarDecls
        # are handled the same way by the Block handler in _GenStmt.
        last_real_stmt = None
        for s in pFunc.body.stmts:
            if isinstance(s, VarDecl):
                self._GenLocalInit(s)
                continue
            self._GenStmt(s)
            last_real_stmt = s

        # Fallthrough epilogue, but only if control could actually reach the
        # end of the function. If the last top-level statement was a Return,
        # the trailing epilogue would be dead code.
        if not isinstance(last_real_stmt, Return):
            self._EmitEpilogue()

    def _EmitEpilogue(self) -> None:
        e = self.emitter
        # Deallocate the entire local frame in one instruction by snapping
        # SP back to FP. This works because the prologue did `GET_SP FP`
        # AFTER `PUSH REX`, so FP points at the saved-FP slot's neighbor —
        # exactly where SP was sitting before any PUSH #0 reservations ran.
        if self._current_func.frame_size > 0:
            e.Instr("SET_SP_R", CC.FP_REG,
                    pComment=f"SP = FP (release {self._current_func.frame_size} local word(s))")
        # Restore old FP
        e.Instr("POP", CC.FP_REG, pComment="restore FP")
        e.Instr("RTS")

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _GenStmt(self, pStmt: Stmt) -> None:
        if isinstance(pStmt, Block):
            for s in pStmt.stmts:
                if isinstance(s, VarDecl):
                    # Slot was reserved up front in _GenFunc; the initializer
                    # runs here, in source order.
                    self._GenLocalInit(s)
                    continue
                self._GenStmt(s)
            return

        if isinstance(pStmt, ExprStmt):
            self._GenExpr(pStmt.expr)
            return

        if isinstance(pStmt, Return):
            if pStmt.value is not None:
                self._GenExpr(pStmt.value)
            self._EmitEpilogue()
            return

        if isinstance(pStmt, If):
            self._GenIf(pStmt)
            return

        if isinstance(pStmt, While):
            self._GenWhile(pStmt)
            return

        if isinstance(pStmt, ForLoop):
            self._GenForLoop(pStmt)
            return

        if isinstance(pStmt, Break):
            if not self._loop_stack:
                raise CCodeGenError("'break' outside loop reached codegen")
            break_label, _ = self._loop_stack[-1]
            self.emitter.Instr("JP", break_label, pComment="break")
            return

        if isinstance(pStmt, Continue):
            if not self._loop_stack:
                raise CCodeGenError("'continue' outside loop reached codegen")
            _, cont_label = self._loop_stack[-1]
            self.emitter.Instr("JP", cont_label, pComment="continue")
            return

        if isinstance(pStmt, AsmStmt):
            Builtins.LowerAsm(self.emitter, pStmt.text)
            return

        if isinstance(pStmt, VarDecl):
            # Handled by _GenFunc hoisting; reached only if directly under a nested Block.
            self._GenLocalInit(pStmt)
            return

        raise CCodeGenError(f"Unhandled statement {type(pStmt).__name__}")

    def _GenIf(self, pStmt: If) -> None:
        e = self.emitter
        else_label = self.labels.NewLabel(self._func_label_prefix, "else")
        end_label  = self.labels.NewLabel(self._func_label_prefix, "endif")

        self._GenExpr(pStmt.cond)
        # If REA == 0, jump to else (or end if no else).
        e.Instr("LDI", CC.SCRATCH_B, "#0")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        if pStmt.else_branch is not None:
            e.Instr("JP_EQ", else_label)
            self._GenStmt(pStmt.then_branch)
            e.Instr("JP", end_label)
            e.Label(else_label)
            self._GenStmt(pStmt.else_branch)
            e.Label(end_label)
        else:
            e.Instr("JP_EQ", end_label)
            self._GenStmt(pStmt.then_branch)
            e.Label(end_label)
            
    def _GenForLoop(self, pStmt: ForLoop) -> None:
        # for (init; cond; update) body
        #
        #     init
        # top:
        #     if (!cond) goto end     ; omitted if cond is empty (infinite loop)
        #     body
        # cont:                       ; `continue` jumps here, NOT to top —
        #     update                  ;  C semantics require the update to run.
        #     goto top
        # end:
        e = self.emitter
        top_label  = self.labels.NewLabel(self._func_label_prefix, "for")
        cont_label = self.labels.NewLabel(self._func_label_prefix, "forcont")
        end_label  = self.labels.NewLabel(self._func_label_prefix, "endfor")

        if pStmt.init is not None:
            self._GenStmt(pStmt.init)

        e.Label(top_label)
        if pStmt.cond is not None:
            self._GenExpr(pStmt.cond)
            e.Instr("LDI", CC.SCRATCH_B, "#0")
            e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
            e.Instr("JP_EQ", end_label)

        self._loop_stack.append((end_label, cont_label))
        try:
            self._GenStmt(pStmt.body)
        finally:
            self._loop_stack.pop()

        e.Label(cont_label)
        if pStmt.update is not None:
            self._GenExpr(pStmt.update)

        e.Instr("JP", top_label)
        e.Label(end_label)

    def _GenWhile(self, pStmt: While) -> None:
        e = self.emitter
        top_label = self.labels.NewLabel(self._func_label_prefix, "loop")
        end_label = self.labels.NewLabel(self._func_label_prefix, "endloop")

        e.Label(top_label)
        self._GenExpr(pStmt.cond)
        e.Instr("LDI", CC.SCRATCH_B, "#0")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        e.Instr("JP_EQ", end_label)
        # `continue` in a while loop re-tests the condition, so it targets the top.
        self._loop_stack.append((end_label, top_label))
        try:
            self._GenStmt(pStmt.body)
        finally:
            self._loop_stack.pop()
        e.Instr("JP", top_label)
        e.Label(end_label)

    # ------------------------------------------------------------------
    # Expression codegen — every expr leaves its result in REA
    # ------------------------------------------------------------------

    def _GenExpr(self, pExpr: Expr) -> None:
        if isinstance(pExpr, IntLit):
            self.emitter.Instr("LDI", CC.ACC_REG, self._Imm(pExpr.value))
            return

        if isinstance(pExpr, CharLit):
            self.emitter.Instr("LDI", CC.ACC_REG, self._Imm(pExpr.value))
            return

        if isinstance(pExpr, StringLit):
            label = self.labels.NewStringLabel()
            self._string_literals.append((label, pExpr.value))
            # Address-of label
            self.emitter.Instr("LDI", CC.ACC_REG, label, pComment=f'"{pExpr.value[:20]}"')
            return

        if isinstance(pExpr, Ident):
            self._LoadIdent(pExpr.name)
            return

        if isinstance(pExpr, BinaryOp):
            self._GenBinary(pExpr)
            return

        if isinstance(pExpr, UnaryOp):
            self._GenUnary(pExpr)
            return

        if isinstance(pExpr, Assign):
            self._GenAssign(pExpr)
            return

        if isinstance(pExpr, Call):
            self._GenCall(pExpr)
            return

        if isinstance(pExpr, Index):
            # Compute address into REA, copy to REY, then dereference (scalar
            # elements only). For struct elements, "loading" by value isn't
            # representable in a 1-word register — the caller almost certainly
            # wants a sub-field via `.` or the address via `&`.
            self._AddressOfIndex(pExpr)
            arr_t = self.analyzer._TypeOfExpr(pExpr.array)
            elem_t = (arr_t.inner if arr_t is not None
                      and (arr_t.IsArray() or arr_t.IsPointer()) else None)
            if elem_t is not None and elem_t.IsStruct():
                raise CCodeGenError(
                    "Cannot use a struct array element by value here "
                    "(use `.field` or `&` to take its address)")
            if elem_t is not None and elem_t.IsArray():
                # Multi-dimensional: element decays to its address.
                return
            self.emitter.Instr("MOV", CC.ADDR_REG_A, CC.ACC_REG)
            self.emitter.Instr("LDI", CC.ACC_REG, f"[{CC.ADDR_REG_A}]", pComment="deref a[i]")
            return

        if isinstance(pExpr, Ternary):
            self._GenTernary(pExpr)
            return

        if isinstance(pExpr, IncDec):
            self._GenIncDec(pExpr)
            return

        if isinstance(pExpr, MemberAccess):
            self._GenMemberLoad(pExpr)
            return

        if isinstance(pExpr, Cast):
            # Casts are runtime no-ops in this v1 dialect — every scalar /
            # pointer is one 24-bit word, so reinterpreting the bits is free.
            # Just emit the operand's value.
            self._GenExpr(pExpr.operand)
            return

        if isinstance(pExpr, SizeOf):
            # Fold to a compile-time integer. The operand of sizeof is
            # unevaluated; we never generate code for it.
            if pExpr.target_type is not None:
                size = pExpr.target_type.WordSize()
            else:
                t = self.analyzer._TypeOfExpr(pExpr.target)
                if t is None:
                    raise CCodeGenError(
                        "sizeof: cannot determine operand type")
                size = t.WordSize()
            self.emitter.Instr("LDI", CC.ACC_REG, self._Imm(size),
                               pComment=f"sizeof = {size}")
            return

        raise CCodeGenError(f"Unhandled expression {type(pExpr).__name__}")

    # ------------------------------------------------------------------
    # Ternary
    # ------------------------------------------------------------------

    def _GenTernary(self, pExpr: Ternary) -> None:
        e = self.emitter
        else_label = self.labels.NewLabel(self._func_label_prefix, "telse")
        end_label  = self.labels.NewLabel(self._func_label_prefix, "tend")
        self._GenExpr(pExpr.cond)
        e.Instr("LDI", CC.SCRATCH_B, "#0")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        e.Instr("JP_EQ", else_label)
        self._GenExpr(pExpr.then_branch)
        e.Instr("JP", end_label)
        e.Label(else_label)
        self._GenExpr(pExpr.else_branch)
        e.Label(end_label)

    # ------------------------------------------------------------------
    # ++ / --  (prefix and postfix)
    # ------------------------------------------------------------------

    def _GenIncDec(self, pExpr: IncDec) -> None:
        # Plan: compute &target into ADDR_REG_A, load *target into REA,
        # then either (postfix) stash old / mutate / restore old, or
        # (prefix) mutate / leave new in REA.
        e = self.emitter
        self._AddressOfLValue(pExpr.target)            # REA = &target
        e.Instr("MOV", CC.ADDR_REG_A, CC.ACC_REG, pComment="addr of target")
        e.Instr("LDI", CC.ACC_REG, f"[{CC.ADDR_REG_A}]", pComment="load target")

        op_instr = "ADD" if pExpr.op == "++" else "SUB"
        if pExpr.is_post:
            # Result is the OLD value; mutate memory but restore REA.
            e.Instr("PUSH", CC.ACC_REG, pComment="save old (postfix result)")
            e.Instr("LDI",  CC.SCRATCH_B, "#1")
            e.Instr(op_instr, CC.ACC_REG, CC.SCRATCH_B)
            e.Instr("STR", CC.ADDR_REG_A, CC.ACC_REG, pComment="commit new value")
            e.Instr("POP", CC.ACC_REG, pComment="REA = old value")
        else:
            # Prefix: result is the NEW value.
            e.Instr("LDI",  CC.SCRATCH_B, "#1")
            e.Instr(op_instr, CC.ACC_REG, CC.SCRATCH_B)
            e.Instr("STR", CC.ADDR_REG_A, CC.ACC_REG, pComment="commit new value")

    # ------------------------------------------------------------------
    # Binary operations
    # ------------------------------------------------------------------

    def _GenBinary(self, pExpr: BinaryOp) -> None:
        op = pExpr.op
        e = self.emitter

        # Short-circuit boolean ops
        if op == "&&":
            self._GenShortCircuitAnd(pExpr)
            return
        if op == "||":
            self._GenShortCircuitOr(pExpr)
            return

        # Standard: eval RHS, push, eval LHS, pop into REB, op
        self._GenExpr(pExpr.right)
        e.Instr("PUSH", CC.ACC_REG, pComment=f"save RHS of {op}")
        self._GenExpr(pExpr.left)
        e.Instr("POP", CC.SCRATCH_B, pComment="REB = RHS")

        if op in DIRECT_OPS:
            e.Instr(DIRECT_OPS[op], CC.ACC_REG, CC.SCRATCH_B)
            return

        if op == "%":
            # remainder: r = a - (a / b) * b ; REA = a, REB = b on entry.
            e.Instr("PUSH", CC.ACC_REG,  pComment="save a")
            e.Instr("PUSH", CC.SCRATCH_B, pComment="save b")
            e.Instr("DIV",  CC.ACC_REG, CC.SCRATCH_B, pComment="REA = a / b")
            e.Instr("POP",  CC.SCRATCH_B, pComment="REB = b")
            e.Instr("MUL",  CC.ACC_REG, CC.SCRATCH_B, pComment="REA = (a/b) * b")
            e.Instr("POP",  CC.SCRATCH_B, pComment="REB = a")
            e.Instr("SUB",  CC.SCRATCH_B, CC.ACC_REG, CC.ACC_REG,
                    pComment="REA = a - (a/b)*b")
            return

        if op in ("==", "!=", "<", ">", "<=", ">="):
            self._GenComparison(op)
            return

        raise CCodeGenError(f"Unknown binary op '{op}'")

    def _GenComparison(self, pOp: str) -> None:
        """REA = LHS, REB = RHS. Emit CMP and produce 0/1 in REA."""
        e = self.emitter
        end_label = self.labels.NewLabel(self._func_label_prefix, "cmp")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        # Pre-set REA = 0 (false). Then conditionally overwrite with 1.
        # We use JP_<negation> end to skip the "set 1" if condition is false.
        e.Instr("LDI", CC.ACC_REG, "#0", pComment="default false")
        if pOp == "==":
            e.Instr("JP_NEQ", end_label)
        elif pOp == "!=":
            e.Instr("JP_EQ", end_label)
        elif pOp == "<":
            # less-than: skip if LHS >= RHS, i.e. JP_GT or JP_EQ
            skip = self.labels.NewLabel(self._func_label_prefix, "ge")
            e.Instr("JP_GT", end_label)
            e.Instr("JP_EQ", end_label)
        elif pOp == ">":
            e.Instr("JP_LT", end_label)
            e.Instr("JP_EQ", end_label)
        elif pOp == "<=":
            # ≤ true unless LHS > RHS
            e.Instr("JP_GT", end_label)
        elif pOp == ">=":
            e.Instr("JP_LT", end_label)
        else:
            raise CCodeGenError(f"Unhandled comparison {pOp}")
        e.Instr("LDI", CC.ACC_REG, "#1", pComment="true")
        e.Label(end_label)

    def _GenShortCircuitAnd(self, pExpr: BinaryOp) -> None:
        """a && b — if a is 0, result is 0 (skip b). Otherwise eval b, result is (b != 0)."""
        e = self.emitter
        end_label = self.labels.NewLabel(self._func_label_prefix, "and_end")
        self._GenExpr(pExpr.left)
        e.Instr("LDI", CC.SCRATCH_B, "#0")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        e.Instr("JP_EQ", end_label)  # REA already 0
        # eval RHS
        self._GenExpr(pExpr.right)
        # Normalize to 0/1
        self._NormalizeToBool()
        e.Label(end_label)

    def _GenShortCircuitOr(self, pExpr: BinaryOp) -> None:
        """a || b — if a is nonzero, result is 1 (skip b). Otherwise eval b, result is (b != 0)."""
        e = self.emitter
        set_one  = self.labels.NewLabel(self._func_label_prefix, "or_one")
        end_label = self.labels.NewLabel(self._func_label_prefix, "or_end")
        self._GenExpr(pExpr.left)
        e.Instr("LDI", CC.SCRATCH_B, "#0")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        e.Instr("JP_NEQ", set_one)
        # left was 0; evaluate right and normalize
        self._GenExpr(pExpr.right)
        self._NormalizeToBool()
        e.Instr("JP", end_label)
        e.Label(set_one)
        e.Instr("LDI", CC.ACC_REG, "#1")
        e.Label(end_label)

    def _NormalizeToBool(self) -> None:
        """REA = (REA != 0) ? 1 : 0"""
        e = self.emitter
        end_label = self.labels.NewLabel(self._func_label_prefix, "norm")
        e.Instr("LDI", CC.SCRATCH_B, "#0")
        e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
        e.Instr("LDI", CC.ACC_REG, "#0")
        e.Instr("JP_EQ", end_label)
        e.Instr("LDI", CC.ACC_REG, "#1")
        e.Label(end_label)

    # ------------------------------------------------------------------
    # Unary
    # ------------------------------------------------------------------

    def _GenUnary(self, pExpr: UnaryOp) -> None:
        e = self.emitter
        op = pExpr.op
        if op == "&":
            self._AddressOfLValue(pExpr.operand)
            return
        if op == "*":
            self._GenExpr(pExpr.operand)
            e.Instr("MOV", CC.ADDR_REG_A, CC.ACC_REG)
            e.Instr("LDI", CC.ACC_REG, f"[{CC.ADDR_REG_A}]", pComment="*p")
            return
        if op == "-":
            self._GenExpr(pExpr.operand)
            e.Instr("LDI", CC.SCRATCH_B, "#0")
            e.Instr("SUB", CC.SCRATCH_B, CC.ACC_REG, CC.ACC_REG, pComment="REA = 0 - REA")
            return
        if op == "~":
            self._GenExpr(pExpr.operand)
            e.Instr("NOT", CC.ACC_REG)
            return
        if op == "!":
            self._GenExpr(pExpr.operand)
            end_label = self.labels.NewLabel(self._func_label_prefix, "not")
            e.Instr("LDI", CC.SCRATCH_B, "#0")
            e.Instr("CMP", CC.ACC_REG, CC.SCRATCH_B)
            e.Instr("LDI", CC.ACC_REG, "#0")
            e.Instr("JP_NEQ", end_label)
            e.Instr("LDI", CC.ACC_REG, "#1")
            e.Label(end_label)
            return
        raise CCodeGenError(f"Unknown unary op '{op}'")

    # ------------------------------------------------------------------
    # Assignment
    # ------------------------------------------------------------------

    def _GenAssign(self, pExpr: Assign) -> None:
        e = self.emitter
        op = pExpr.op

        # Compute the value to store into REA.
        if op == "=":
            self._GenExpr(pExpr.value)
        else:
            # x op= y  becomes  x = x op y
            base_op = COMPOUND_OPS[op]
            # Eval RHS, push, eval LHS, pop RHS into REB.
            self._GenExpr(pExpr.value)
            e.Instr("PUSH", CC.ACC_REG, pComment=f"RHS of {op}")
            self._GenExpr(pExpr.target)
            e.Instr("POP", CC.SCRATCH_B)
            if base_op in DIRECT_OPS:
                e.Instr(DIRECT_OPS[base_op], CC.ACC_REG, CC.SCRATCH_B)
            elif base_op == "%":
                # Same modulo trick as _GenBinary
                e.Instr("PUSH", CC.ACC_REG,  pComment="save a")
                e.Instr("PUSH", CC.SCRATCH_B, pComment="save b")
                e.Instr("DIV",  CC.ACC_REG, CC.SCRATCH_B)
                e.Instr("POP",  CC.SCRATCH_B)
                e.Instr("MUL",  CC.ACC_REG, CC.SCRATCH_B)
                e.Instr("POP",  CC.SCRATCH_B)
                e.Instr("SUB",  CC.SCRATCH_B, CC.ACC_REG, CC.ACC_REG)
            else:
                raise CCodeGenError(f"Compound op '{op}' not supported")

        # Commit the value (currently in REA) to the target. For scalar
        # locals and params, STR_LOC / STR_ARG do it in a single instruction.
        # For globals and complex lvalues, fall back to "compute address into
        # REY, then STR".
        target = pExpr.target
        if isinstance(target, Ident):
            local = self._current_func.symbols.get(target.name)
            if local is not None and not local.ctype.IsArray():
                if local.is_param:
                    offset = CC.ARG_BASE_OFFSET + local.slot
                    e.Instr("STR_ARG", CC.ACC_REG, self._Imm(offset),
                            pComment=f"{target.name} = value")
                else:
                    e.Instr("STR_LOC", CC.ACC_REG, self._Imm(local.slot),
                            pComment=f"{target.name} = value")
                return
            # Global, or local array — keep the general address-compute path.
            self._AddressOfIdentInto(CC.ADDR_REG_A, target.name)
            e.Instr("STR", CC.ADDR_REG_A, CC.ACC_REG, pComment="*target = value")
            return

        # Member-access fast path: when the field is a scalar of a LOCAL
        # struct (the common case `s.x = ...`), STR_LOC handles it in one
        # instruction — same trick used for plain locals.
        if isinstance(target, MemberAccess) and self._TryFastMemberStore(target):
            return

        # Complex lvalue path
        e.Instr("PUSH", CC.ACC_REG, pComment="save value")
        if isinstance(target, Index):
            self._AddressOfIndex(target)
        elif isinstance(target, UnaryOp) and target.op == "*":
            self._GenExpr(target.operand)
        elif isinstance(target, MemberAccess):
            self._AddressOfMember(target)
        else:
            raise CCodeGenError(f"Cannot assign to {type(target).__name__}")
        e.Instr("MOV", CC.ADDR_REG_A, CC.ACC_REG, pComment="REY = &target")
        e.Instr("POP", CC.ACC_REG, pComment="restore value")
        e.Instr("STR", CC.ADDR_REG_A, CC.ACC_REG, pComment="*target = value")

    # ------------------------------------------------------------------
    # Struct member access
    # ------------------------------------------------------------------

    def _GenMemberLoad(self, pExpr: MemberAccess) -> None:
        """Load the value of `target.field` or `target->field` into REA.

        Fast path: scalar field of a LOCAL struct (`.field`, not `->field`)
        becomes a single `LDR_LOC` because the slot offset is known at
        compile time.

        General path: compute address into REA, MOV to ADDR_REG_A, deref.
        """
        e = self.emitter

        # Fast path: `local_struct.scalar_field`.
        if (not pExpr.via_ptr and isinstance(pExpr.target, Ident)):
            sym = self._current_func.symbols.get(pExpr.target.name)
            if (sym is not None and not sym.is_param
                    and sym.ctype.IsStruct()):
                field = sym.ctype.struct_def.FindField(pExpr.field)
                if field.ctype.IsScalar():
                    slot_offset = (sym.slot + sym.ctype.WordSize()
                                   - 1 - field.offset)
                    e.Instr("LDR_LOC", CC.ACC_REG, self._Imm(slot_offset),
                            pComment=f"{pExpr.target.name}.{pExpr.field}")
                    return

        # General path: compute &field, then deref (scalar fields only).
        self._AddressOfMember(pExpr)
        field_t = self._FieldTypeOf(pExpr)
        if field_t is not None and field_t.IsStruct():
            # A struct-typed field can't be loaded by value. The user wants
            # a sub-field of it (`.x.y`) or its address (`&x.y`); both routes
            # call _AddressOfMember directly without going through here.
            raise CCodeGenError(
                f"Cannot use struct field '.{pExpr.field}' by value here "
                f"(access a sub-field or take its address)")
        if field_t is not None and field_t.IsArray():
            # Array field decays to its address.
            return
        e.Instr("MOV", CC.ADDR_REG_A, CC.ACC_REG)
        e.Instr("LDI", CC.ACC_REG, f"[{CC.ADDR_REG_A}]",
                pComment=f".{pExpr.field}")

    def _TryFastMemberStore(self, pTarget: MemberAccess) -> bool:
        """If `pTarget` is a scalar field of a local struct accessed with `.`,
        emit a single STR_LOC and return True. Otherwise return False so the
        caller can use the general address-compute path. Assumes REA holds
        the value to store."""
        if pTarget.via_ptr or not isinstance(pTarget.target, Ident):
            return False
        sym = self._current_func.symbols.get(pTarget.target.name)
        if sym is None or sym.is_param or not sym.ctype.IsStruct():
            return False
        field = sym.ctype.struct_def.FindField(pTarget.field)
        if not field.ctype.IsScalar():
            return False
        slot_offset = sym.slot + sym.ctype.WordSize() - 1 - field.offset
        self.emitter.Instr(
            "STR_LOC", CC.ACC_REG, self._Imm(slot_offset),
            pComment=f"{pTarget.target.name}.{pTarget.field} = value")
        return True

    def _AddressOfMember(self, pExpr: MemberAccess) -> None:
        """Compute `&(target.field)` or `&(target->field)` into REA."""
        e = self.emitter
        struct_t = self._StructTypeOfTarget(pExpr.target, pExpr.via_ptr)
        field = struct_t.struct_def.FindField(pExpr.field)

        if pExpr.via_ptr:
            # target is a pointer expression; its value IS the struct's address.
            self._GenExpr(pExpr.target)
        else:
            # target is itself a struct lvalue; take its address.
            self._AddressOfLValue(pExpr.target)

        if field.offset != 0:
            e.Instr("LDI", CC.SCRATCH_B, self._Imm(field.offset))
            e.Instr("ADD", CC.ACC_REG, CC.SCRATCH_B,
                    pComment=f"&.{pExpr.field} (+{field.offset})")

    def _StructTypeOfTarget(self, pTargetExpr: Expr, pViaPtr: bool) -> CType:
        """Return the CType (kind='struct') for the struct being accessed.
        For `.`, that's the target's type. For `->`, it's the target's
        pointer-inner type."""
        t = self.analyzer._TypeOfExpr(pTargetExpr)
        if t is None:
            raise CCodeGenError(
                "Cannot determine struct type for member access (analyzer bug?)")
        return t.inner if pViaPtr else t

    def _FieldTypeOf(self, pExpr: MemberAccess) -> Optional[CType]:
        """The CType of the accessed field, or None if it can't be determined."""
        struct_t = self._StructTypeOfTarget(pExpr.target, pExpr.via_ptr)
        f = struct_t.struct_def.FindField(pExpr.field)
        return f.ctype if f is not None else None

    def _AddressOfLValue(self, pExpr: Expr) -> None:
        """Compute the address of an lvalue, leave in REA (for &x as rvalue)."""
        e = self.emitter
        if isinstance(pExpr, Ident):
            self._AddressOfIdentInto(CC.ACC_REG, pExpr.name)
            return
        if isinstance(pExpr, Index):
            self._AddressOfIndex(pExpr)
            return
        if isinstance(pExpr, MemberAccess):
            self._AddressOfMember(pExpr)
            return
        if isinstance(pExpr, UnaryOp) and pExpr.op == "*":
            # &*p  ==  p
            self._GenExpr(pExpr.operand)
            return
        raise CCodeGenError(f"Cannot take address of {type(pExpr).__name__}")

    def _AddressOfIdent(self, pName: str) -> None:
        """Convenience: write address of identifier into REA."""
        self._AddressOfIdentInto(CC.ACC_REG, pName)

    def _AddressOfIdentInto(self, pReg: str, pName: str) -> None:
        """Write address of identifier directly into pReg (uses REZ as temp).

        Frame layout (grow-down stack, post-decrement PUSH):
            arg N             at  FP + (ARG_BASE_OFFSET + N)        (use ADD)
            scalar local at slot S    at  FP - S                     (use SUB)
            array of size K at slot S: &a = FP - (S + K - 1)         (use SUB)
        """
        e = self.emitter
        local = self._current_func.symbols.get(pName)
        if local is not None:
            if local.is_param:
                offset = CC.ARG_BASE_OFFSET + local.slot
                e.Instr("MOV", pReg, CC.FP_REG)
                e.Instr("LDI", CC.ADDR_REG_B, self._Imm(offset))
                e.Instr("ADD", pReg, CC.ADDR_REG_B, pComment=f"&{pName} (arg)")
                return
            size = local.ctype.WordSize()
            offset = local.slot + size - 1
            e.Instr("MOV", pReg, CC.FP_REG)
            if offset == 0:
                e.Instr("LDI", CC.ADDR_REG_B, "#0")
                e.Instr("SUB", pReg, CC.ADDR_REG_B, pComment=f"&{pName} (local)")
            else:
                e.Instr("LDI", CC.ADDR_REG_B, self._Imm(offset))
                e.Instr("SUB", pReg, CC.ADDR_REG_B, pComment=f"&{pName} (local)")
            return
        # Global
        if pName in self.analyzer.globals:
            e.Instr("LDI", pReg, pName, pComment=f"&{pName} (global)")
            return
        # Function names — addressable for function-pointer use; not supported in v1.
        raise CCodeGenError(f"Cannot take address of unknown symbol '{pName}'")

    def _AddressOfIndex(self, pExpr: Index) -> None:
        """Compute &(array[index]). All elements are 1 word."""
        e = self.emitter
        # Determine element word-size for stride. For scalar elements (the
        # historical case) this is 1 and we emit no multiply; for arrays of
        # struct (multi-word elements) we scale the index before adding.
        elem_size = self._IndexElementSize(pExpr.array)

        # Evaluate index, scale by element size if needed, save it.
        self._GenExpr(pExpr.index)
        if elem_size > 1:
            e.Instr("LDI", CC.SCRATCH_B, self._Imm(elem_size),
                    pComment=f"sizeof(element) = {elem_size}")
            e.Instr("MUL", CC.ACC_REG, CC.SCRATCH_B, pComment="index *= sizeof")
        e.Instr("PUSH", CC.ACC_REG, pComment="save scaled index")
        # Compute base address into REA.
        if isinstance(pExpr.array, Ident):
            # Could be an array or a pointer; both reduce to "address of element 0".
            local = self._current_func.symbols.get(pExpr.array.name)
            if local is not None and local.ctype.IsArray():
                # &array (local array)
                self._AddressOfIdent(pExpr.array.name)
            elif local is not None and local.is_param and local.ctype.IsPointer():
                # param is pointer: load its value as base
                self._LoadIdent(pExpr.array.name)
            elif local is not None:
                # local pointer variable: load its value
                self._LoadIdent(pExpr.array.name)
            elif pExpr.array.name in self.analyzer.globals:
                gtype = self.analyzer.globals[pExpr.array.name].ctype
                if gtype.IsArray():
                    self._AddressOfIdent(pExpr.array.name)
                else:
                    self._LoadIdent(pExpr.array.name)
            else:
                raise CCodeGenError(f"Indexing unknown symbol '{pExpr.array.name}'")
        else:
            # General lvalue/expression that yields a pointer value
            self._GenExpr(pExpr.array)
        # REA = base; pop index into REB and add.
        e.Instr("POP", CC.SCRATCH_B, pComment="REB = scaled index")
        e.Instr("ADD", CC.ACC_REG, CC.SCRATCH_B, pComment="&base[index]")

    def _IndexElementSize(self, pArrayExpr: Expr) -> int:
        """Word-size of one element when indexing `pArrayExpr`. Returns 1 for
        scalar/pointer/char arrays and pointers (the historical default);
        returns N>1 for arrays of struct or pointers-to-struct (where the
        struct itself has WordSize N).
        """
        arr_t = self.analyzer._TypeOfExpr(pArrayExpr)
        if arr_t is None:
            return 1
        if arr_t.IsArray() or arr_t.IsPointer():
            return arr_t.inner.WordSize() if arr_t.inner is not None else 1
        return 1

    # ------------------------------------------------------------------
    # Calls
    # ------------------------------------------------------------------

    def _GenCall(self, pExpr: Call) -> None:
        e = self.emitter
        if Builtins.IsBuiltinCall(pExpr.name):
            Builtins.LowerSyscall(self.emitter, pExpr.args, self._GenExpr)
            return

        # Push args right-to-left
        for i in range(len(pExpr.args) - 1, -1, -1):
            self._GenExpr(pExpr.args[i])
            e.Instr("PUSH", CC.ACC_REG, pComment=f"arg {i}")

        e.Instr("CALL", pExpr.name)

        # Caller cleans up pushed args
        for i in range(len(pExpr.args)):
            e.Instr("POP", CC.SCRATCH_C, pComment="discard arg")

    # ------------------------------------------------------------------
    # Identifier load/store helpers
    # ------------------------------------------------------------------

    def _LoadIdent(self, pName: str) -> None:
        """Load the value of identifier `pName` into REA."""
        e = self.emitter
        local = self._current_func.symbols.get(pName)
        if local is not None:
            if local.ctype.IsStruct():
                # Bare struct value isn't loadable (multi-word). Should be
                # caught by the analyzer in most contexts; defense in depth.
                raise CCodeGenError(
                    f"Cannot use struct '{pName}' as a value here "
                    f"(use a field or &{pName})")
            if local.ctype.IsArray():
                # Array name decays to pointer to element 0
                self._AddressOfIdentInto(CC.ACC_REG, pName)
                return
            # Scalar local or param: single-instruction FP-relative load.
            if local.is_param:
                offset = CC.ARG_BASE_OFFSET + local.slot
                e.Instr("LDR_ARG", CC.ACC_REG, self._Imm(offset), pComment=pName)
            else:
                e.Instr("LDR_LOC", CC.ACC_REG, self._Imm(local.slot), pComment=pName)
            return
        if pName in self.analyzer.globals:
            g = self.analyzer.globals[pName]
            if g.ctype.IsArray():
                e.Instr("LDI", CC.ACC_REG, pName, pComment=f"&{pName}")
                return
            e.Instr("LDI", CC.ADDR_REG_A, pName, pComment=f"&{pName}")
            e.Instr("LDI", CC.ACC_REG, f"[{CC.ADDR_REG_A}]", pComment=pName)
            return
        raise CCodeGenError(f"Cannot load unknown identifier '{pName}'")

    def _GenLocalInit(self, pDecl: VarDecl) -> None:
        """Emit code to run a VarDecl's initializer. Handles scalar inits and
        string-literal-into-char-array inits. No-op if `pDecl.init is None`."""
        if pDecl.init is None:
            return
        if pDecl.ctype.IsArray():
            if not isinstance(pDecl.init, StringLit):
                # Analyzer should have rejected anything else.
                raise CCodeGenError(
                    f"Unsupported array initializer for '{pDecl.name}'")
            self._StoreStringIntoLocalArray(pDecl)
            return
        self._GenExpr(pDecl.init)
        self._StoreLocal(pDecl.slot, pDecl.ctype.WordSize())

    def _StoreStringIntoLocalArray(self, pDecl: VarDecl) -> None:
        """Write each char of pDecl.init.value (plus NUL) into the local array.
        Slots beyond the string length stay at the zero initialized by the
        prologue's PUSH #0."""
        e = self.emitter
        text: str = pDecl.init.value
        chars = [ord(c) for c in text] + [0]
        # Array address: &arr[0] = FP - (slot + size - 1); &arr[i] = &arr[0] + i.
        base_offset = pDecl.slot + pDecl.ctype.size - 1
        for i, ch in enumerate(chars):
            offset = base_offset - i
            e.Instr("MOV", CC.ADDR_REG_A, CC.FP_REG)
            e.Instr("LDI", CC.ADDR_REG_B,
                    self._Imm(offset) if offset != 0 else "#0")
            e.Instr("SUB", CC.ADDR_REG_A, CC.ADDR_REG_B,
                    pComment=f"&{pDecl.name}[{i}]")
            e.Instr("LDI", CC.ACC_REG, self._Imm(ch))
            e.Instr("STR", CC.ADDR_REG_A, CC.ACC_REG)

    def _StoreLocal(self, pSlot: int, pSize: int) -> None:
        """Store REA into a scalar local at frame slot `pSlot`.

        Grow-down post-decrement stack: scalar at slot S sits at FP - S.
        Single-instruction emission via STR_LOC.
        """
        if pSize != 1:
            raise CCodeGenError(f"Multi-word local stores not supported (size={pSize})")
        self.emitter.Instr("STR_LOC", CC.ACC_REG, self._Imm(pSlot),
                           pComment="*local = REA")

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    @staticmethod
    def _Imm(pValue: int) -> str:
        """Format a 24-bit integer immediate, masking negatives."""
        v = pValue & CC.WORD_MASK
        return f"#0x{v:X}"
