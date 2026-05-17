"""
Recursive-descent C parser for cc.py.

Produces an AST from a list of tokens. Uses Pratt-style precedence climbing
for expressions.
"""

from typing import List, Optional

from CCompilerComponents.AST import (
    CType, IntLit, CharLit, StringLit, Ident, BinaryOp, UnaryOp, Assign,
    Call, Index, Ternary, IncDec, VarDecl, ExprStmt, Block, If, While,
    ForLoop, Return, Break, Continue, AsmStmt, Param, FuncDef, GlobalDecl,
    TranslationUnit, Expr, Stmt,
)
from CCompilerComponents.Exceptions import CParseError
from CCompilerComponents.Lexer import (
    Token, TK_INT_LIT, TK_CHAR_LIT, TK_STRING_LIT, TK_IDENT, TK_KEYWORD,
    TK_PUNCT, TK_EOF,
)


# C operator precedence levels (higher = binds tighter).
# Index lookup: PRECEDENCE[op] -> (binding_power, is_right_assoc)
PRECEDENCE = {
    "||": (1, False),
    "&&": (2, False),
    "|":  (3, False),
    "^":  (4, False),
    "&":  (5, False),
    "==": (6, False), "!=": (6, False),
    "<":  (7, False), ">":  (7, False), "<=": (7, False), ">=": (7, False),
    "<<": (8, False), ">>": (8, False),
    "+":  (9, False), "-":  (9, False),
    "*":  (10, False), "/":  (10, False), "%":  (10, False),
}

ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}


class Parser:

    def __init__(self, pTokens: List[Token]):
        self.toks = pTokens
        self.pos = 0

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def _Peek(self, pOffset: int = 0) -> Token:
        idx = self.pos + pOffset
        if idx >= len(self.toks):
            return self.toks[-1]
        return self.toks[idx]

    def _Advance(self) -> Token:
        tok = self.toks[self.pos]
        self.pos += 1
        return tok

    def _Match(self, pKind: str, pValue=None) -> bool:
        tok = self._Peek()
        if tok.kind != pKind:
            return False
        if pValue is not None and tok.value != pValue:
            return False
        return True

    def _Accept(self, pKind: str, pValue=None) -> Optional[Token]:
        if self._Match(pKind, pValue):
            return self._Advance()
        return None

    def _Expect(self, pKind: str, pValue=None) -> Token:
        tok = self._Peek()
        if not self._Match(pKind, pValue):
            wanted = pValue if pValue is not None else pKind
            raise CParseError(f"Expected {wanted!r}, got {tok.value!r} ({tok.kind})",
                              tok.line, tok.col)
        return self._Advance()

    # ------------------------------------------------------------------
    # Top-level: TranslationUnit
    # ------------------------------------------------------------------

    def Parse(self) -> TranslationUnit:
        items = []
        while not self._Match(TK_EOF):
            items.append(self._ParseTopLevel())
        return TranslationUnit(items=items)

    def _ParseTopLevel(self):
        # All top-level forms start with a type keyword (optionally preceded
        # by `extern`). `extern` is accepted on both functions and globals
        # and marks them as declared-here, defined-elsewhere.
        start_tok = self._Peek()
        is_extern = bool(self._Accept(TK_KEYWORD, "extern"))
        ctype = self._ParseType()
        name_tok = self._Expect(TK_IDENT)
        name = name_tok.value

        # Function: `Type name (`
        if self._Match(TK_PUNCT, "("):
            return self._ParseFuncDef(ctype, name, start_tok.line, is_extern)

        # Global variable: optional array size, optional init, semicolon.
        # `[]` (empty brackets) is allowed when a string-literal init will
        # size the array; the analyzer fills `size` in that case.
        if self._Accept(TK_PUNCT, "["):
            size: Optional[int] = None
            if not self._Match(TK_PUNCT, "]"):
                size_tok = self._Expect(TK_INT_LIT)
                size = size_tok.value
            self._Expect(TK_PUNCT, "]")
            ctype = CType(kind="array", inner=ctype, size=size,
                          is_const=ctype.is_const)
        init = None
        if self._Accept(TK_PUNCT, "="):
            init = self._ParseExpression()
        self._Expect(TK_PUNCT, ";")
        return GlobalDecl(ctype=ctype, name=name, init=init, line=start_tok.line,
                          is_extern=is_extern)

    # ------------------------------------------------------------------
    # Type parsing
    # ------------------------------------------------------------------

    def _ParseType(self) -> CType:
        # Optional leading `const`. We only support variable-level constness
        # (see CType doc), so const before any base type just stamps the
        # outermost CType.
        is_const = bool(self._Accept(TK_KEYWORD, "const"))
        tok = self._Peek()
        if tok.kind != TK_KEYWORD or tok.value not in ("int", "char", "void"):
            raise CParseError(f"Expected type, got {tok.value!r}", tok.line, tok.col)
        self._Advance()
        ctype = CType(kind=tok.value)
        # Pointer stars. is_const stays on the *outermost* type, which after
        # any '*' is the pointer itself — matches our variable-level semantics.
        while self._Accept(TK_PUNCT, "*"):
            ctype = CType(kind="ptr", inner=ctype)
        ctype.is_const = is_const
        return ctype

    # ------------------------------------------------------------------
    # Function definition
    # ------------------------------------------------------------------

    def _ParseFuncDef(self, pRetType: CType, pName: str, pLine: int,
                      pIsExtern: bool = False) -> FuncDef:
        self._Expect(TK_PUNCT, "(")
        params: List[Param] = []
        # `void` alone in param list = no params
        if self._Match(TK_KEYWORD, "void") and self._Peek(1).value == ")":
            self._Advance()
        elif not self._Match(TK_PUNCT, ")"):
            while True:
                p_type = self._ParseType()
                # Param names are optional in declarations (extern). For
                # definitions a name is still required; we enforce that below
                # when there's a body.
                if self._Match(TK_IDENT):
                    p_name = self._Advance().value
                else:
                    p_name = ""
                params.append(Param(ctype=p_type, name=p_name))
                if not self._Accept(TK_PUNCT, ","):
                    break
        self._Expect(TK_PUNCT, ")")
        # Declaration (no body): `Type name(params);`
        if self._Accept(TK_PUNCT, ";"):
            return FuncDef(ret_type=pRetType, name=pName, params=params,
                           body=None, line=pLine, is_extern=True)
        body = self._ParseBlock()
        # Definitions require named params
        for p in params:
            if not p.name:
                raise CParseError(
                    f"Parameter in definition of '{pName}' must have a name",
                    pLine, 0)
        return FuncDef(ret_type=pRetType, name=pName, params=params, body=body,
                       line=pLine, is_extern=pIsExtern)

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _ParseBlock(self) -> Block:
        tok = self._Expect(TK_PUNCT, "{")
        stmts: List[Stmt] = []
        while not self._Match(TK_PUNCT, "}"):
            if self._Match(TK_EOF):
                raise CParseError("Unterminated block", tok.line, tok.col)
            stmts.append(self._ParseStatement())
        self._Expect(TK_PUNCT, "}")
        return Block(stmts=stmts, line=tok.line, col=tok.col)

    def _ParseStatement(self) -> Stmt:
        tok = self._Peek()

        # Block
        if tok.kind == TK_PUNCT and tok.value == "{":
            return self._ParseBlock()

        # Keyword-led statements
        if tok.kind == TK_KEYWORD:
            kw = tok.value
            if kw == "if":       return self._ParseIf()
            if kw == "while":    return self._ParseWhile()
            if kw == "for":      return self._ParseFor()
            if kw == "return":   return self._ParseReturn()
            if kw == "break":    return self._ParseBreak()
            if kw == "continue": return self._ParseContinue()
            if kw == "asm":      return self._ParseAsm()
            if kw in ("int", "char", "const"):  # Local declaration
                return self._ParseLocalDecl()
            if kw == "void":
                raise CParseError("'void' is only valid as a function return type",
                                  tok.line, tok.col)
            # Fallthrough for syscall (treated as expression)

        # Expression statement
        expr = self._ParseExpression()
        self._Expect(TK_PUNCT, ";")
        return ExprStmt(expr=expr, line=tok.line, col=tok.col)

    def _ParseIf(self) -> If:
        tok = self._Expect(TK_KEYWORD, "if")
        self._Expect(TK_PUNCT, "(")
        cond = self._ParseExpression()
        self._Expect(TK_PUNCT, ")")
        then_branch = self._ParseStatement()
        else_branch = None
        if self._Accept(TK_KEYWORD, "else"):
            else_branch = self._ParseStatement()
        return If(cond=cond, then_branch=then_branch, else_branch=else_branch,
                  line=tok.line, col=tok.col)

    def _ParseWhile(self) -> While:
        tok = self._Expect(TK_KEYWORD, "while")
        self._Expect(TK_PUNCT, "(")
        cond = self._ParseExpression()
        self._Expect(TK_PUNCT, ")")
        body = self._ParseStatement()
        return While(cond=cond, body=body, line=tok.line, col=tok.col)

    def _ParseFor(self) -> ForLoop:
        # for (init? ; cond? ; update?) body
        # init may be an empty statement, an expression, or a declaration.
        tok = self._Expect(TK_KEYWORD, "for")
        self._Expect(TK_PUNCT, "(")

        init: Optional[Stmt] = None
        if self._Accept(TK_PUNCT, ";"):
            pass  # empty init
        elif (self._Match(TK_KEYWORD, "int")
              or self._Match(TK_KEYWORD, "char")
              or self._Match(TK_KEYWORD, "const")):
            # Declaration form — _ParseLocalDecl consumes the trailing ';'.
            init = self._ParseLocalDecl()
        else:
            expr_tok = self._Peek()
            expr = self._ParseExpression()
            self._Expect(TK_PUNCT, ";")
            init = ExprStmt(expr=expr, line=expr_tok.line, col=expr_tok.col)

        cond: Optional[Expr] = None
        if not self._Match(TK_PUNCT, ";"):
            cond = self._ParseExpression()
        self._Expect(TK_PUNCT, ";")

        update: Optional[Expr] = None
        if not self._Match(TK_PUNCT, ")"):
            update = self._ParseExpression()
        self._Expect(TK_PUNCT, ")")

        body = self._ParseStatement()
        return ForLoop(init=init, cond=cond, update=update, body=body,
                       line=tok.line, col=tok.col)

    def _ParseReturn(self) -> Return:
        tok = self._Expect(TK_KEYWORD, "return")
        value = None
        if not self._Match(TK_PUNCT, ";"):
            value = self._ParseExpression()
        self._Expect(TK_PUNCT, ";")
        return Return(value=value, line=tok.line, col=tok.col)

    def _ParseAsm(self) -> AsmStmt:
        tok = self._Expect(TK_KEYWORD, "asm")
        self._Expect(TK_PUNCT, "(")
        text_tok = self._Expect(TK_STRING_LIT)
        self._Expect(TK_PUNCT, ")")
        self._Expect(TK_PUNCT, ";")
        return AsmStmt(text=text_tok.value, line=tok.line, col=tok.col)

    def _ParseBreak(self) -> Break:
        tok = self._Expect(TK_KEYWORD, "break")
        self._Expect(TK_PUNCT, ";")
        return Break(line=tok.line, col=tok.col)

    def _ParseContinue(self) -> Continue:
        tok = self._Expect(TK_KEYWORD, "continue")
        self._Expect(TK_PUNCT, ";")
        return Continue(line=tok.line, col=tok.col)

    def _ParseLocalDecl(self) -> VarDecl:
        start = self._Peek()
        ctype = self._ParseType()
        name = self._Expect(TK_IDENT).value
        if self._Accept(TK_PUNCT, "["):
            # Allow `[]` (size omitted) — SemanticAnalyzer will size it from
            # the string-literal initializer.
            size: Optional[int] = None
            if not self._Match(TK_PUNCT, "]"):
                size_tok = self._Expect(TK_INT_LIT)
                size = size_tok.value
            self._Expect(TK_PUNCT, "]")
            ctype = CType(kind="array", inner=ctype, size=size,
                          is_const=ctype.is_const)
        init = None
        if self._Accept(TK_PUNCT, "="):
            init = self._ParseExpression()
        self._Expect(TK_PUNCT, ";")
        return VarDecl(ctype=ctype, name=name, init=init, line=start.line, col=start.col)

    # ------------------------------------------------------------------
    # Expressions (Pratt-style precedence climbing)
    # ------------------------------------------------------------------

    def _ParseExpression(self) -> Expr:
        return self._ParseAssignment()

    def _ParseAssignment(self) -> Expr:
        left = self._ParseTernary()
        if self._Peek().kind == TK_PUNCT and self._Peek().value in ASSIGN_OPS:
            op_tok = self._Advance()
            right = self._ParseAssignment()
            return Assign(op=op_tok.value, target=left, value=right,
                          line=op_tok.line, col=op_tok.col)
        return left

    def _ParseTernary(self) -> Expr:
        # cond '?' expression ':' conditional
        # Right-associative on the else side (matches C grammar: the else
        # branch is `conditional`, so `a ? b : c ? d : e` parses as
        # `a ? b : (c ? d : e)`).
        cond = self._ParseBinary(0)
        if self._Accept(TK_PUNCT, "?"):
            then_branch = self._ParseExpression()
            self._Expect(TK_PUNCT, ":")
            else_branch = self._ParseTernary()
            return Ternary(cond=cond, then_branch=then_branch,
                           else_branch=else_branch,
                           line=cond.line, col=cond.col)
        return cond

    def _ParseBinary(self, pMinPrec: int) -> Expr:
        left = self._ParseUnary()
        while True:
            tok = self._Peek()
            if tok.kind != TK_PUNCT or tok.value not in PRECEDENCE:
                break
            prec, right_assoc = PRECEDENCE[tok.value]
            if prec < pMinPrec:
                break
            self._Advance()
            next_prec = prec if right_assoc else prec + 1
            right = self._ParseBinary(next_prec)
            left = BinaryOp(op=tok.value, left=left, right=right,
                            line=tok.line, col=tok.col)
        return left

    def _ParseUnary(self) -> Expr:
        tok = self._Peek()
        # Prefix ++ / --: parsed as IncDec, target must be lvalue (checked later).
        if tok.kind == TK_PUNCT and tok.value in ("++", "--"):
            self._Advance()
            operand = self._ParseUnary()
            return IncDec(op=tok.value, is_post=False, target=operand,
                          line=tok.line, col=tok.col)
        if tok.kind == TK_PUNCT and tok.value in ("-", "!", "~", "*", "&", "+"):
            self._Advance()
            if tok.value == "+":
                # unary plus is a no-op
                return self._ParseUnary()
            operand = self._ParseUnary()
            return UnaryOp(op=tok.value, operand=operand,
                           line=tok.line, col=tok.col)
        return self._ParsePostfix()

    def _ParsePostfix(self) -> Expr:
        expr = self._ParsePrimary()
        while True:
            if self._Accept(TK_PUNCT, "["):
                idx = self._ParseExpression()
                self._Expect(TK_PUNCT, "]")
                expr = Index(array=expr, index=idx, line=expr.line, col=expr.col)
            elif self._Match(TK_PUNCT, "++") or self._Match(TK_PUNCT, "--"):
                op_tok = self._Advance()
                expr = IncDec(op=op_tok.value, is_post=True, target=expr,
                              line=op_tok.line, col=op_tok.col)
            else:
                break
        return expr

    def _ParsePrimary(self) -> Expr:
        tok = self._Peek()

        if tok.kind == TK_INT_LIT:
            self._Advance()
            return IntLit(value=tok.value, line=tok.line, col=tok.col)

        if tok.kind == TK_CHAR_LIT:
            self._Advance()
            return CharLit(value=tok.value, line=tok.line, col=tok.col)

        if tok.kind == TK_STRING_LIT:
            self._Advance()
            return StringLit(value=tok.value, line=tok.line, col=tok.col)

        if tok.kind == TK_PUNCT and tok.value == "(":
            self._Advance()
            inner = self._ParseExpression()
            self._Expect(TK_PUNCT, ")")
            return inner

        # `syscall(...)` builtin — looks just like a call site
        if tok.kind == TK_KEYWORD and tok.value == "syscall":
            self._Advance()
            args = self._ParseCallArgs()
            return Call(name="syscall", args=args, line=tok.line, col=tok.col)

        if tok.kind == TK_IDENT:
            self._Advance()
            if self._Match(TK_PUNCT, "("):
                args = self._ParseCallArgs()
                return Call(name=tok.value, args=args, line=tok.line, col=tok.col)
            return Ident(name=tok.value, line=tok.line, col=tok.col)

        raise CParseError(f"Unexpected token {tok.value!r}", tok.line, tok.col)

    def _ParseCallArgs(self) -> List[Expr]:
        self._Expect(TK_PUNCT, "(")
        args: List[Expr] = []
        if not self._Match(TK_PUNCT, ")"):
            while True:
                args.append(self._ParseExpression())
                if not self._Accept(TK_PUNCT, ","):
                    break
        self._Expect(TK_PUNCT, ")")
        return args
