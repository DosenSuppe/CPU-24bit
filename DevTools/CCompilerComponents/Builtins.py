"""
Builtin lowerings: `syscall(...)` and `asm("...")`.

These are not regular functions — they emit specific DASM sequences. The
CodeGen module delegates to functions here when it encounters them.
"""

from CCompilerComponents import CallingConvention as CC


def IsBuiltinCall(pName: str) -> bool:
    return pName == "syscall"


def LowerSyscall(pEmitter, pArgExprs, pEvalExprFn) -> None:
    """
    Lower a `syscall(num, arg1, arg2, ...)` call.

    Strategy: evaluate each arg left-to-right into REA, push it. After all
    args are on the stack, pop them back in reverse into the syscall-arg
    registers per the convention. Then emit INT.

    Args:
        pEmitter:     AsmEmitter to write into.
        pArgExprs:    list of AST expressions (first is the syscall number).
        pEvalExprFn:  callable(expr) that evaluates `expr` into REA.

    On return, the syscall's result is in REA.
    """
    n = len(pArgExprs)
    if n == 0:
        raise ValueError("syscall needs at least the number argument")
    if n > len(CC.SYSCALL_REGS):
        raise ValueError(f"syscall supports at most {len(CC.SYSCALL_REGS)} arguments (got {n})")

    # 1) Evaluate each arg in source order, pushing the result.
    for i, arg in enumerate(pArgExprs):
        pEvalExprFn(arg)
        pEmitter.Instr("PUSH", CC.ACC_REG, pComment=f"syscall arg {i}")

    # 2) Pop in reverse into target registers.
    #    pArgExprs[0] -> SYSCALL_REGS[0] (REA: syscall number)
    #    pArgExprs[1] -> SYSCALL_REGS[1] (REB)
    #    ...
    for i in reversed(range(n)):
        pEmitter.Instr("POP", CC.SYSCALL_REGS[i], pComment=f"-> {CC.SYSCALL_REGS[i]}")

    # 3) Fire the software interrupt. Handler reads REA for dispatch.
    pEmitter.Instr("INT", pComment="syscall trap")
    # Return value is whatever the handler left in REA.


def LowerAsm(pEmitter, pText: str) -> None:
    """Emit an inline-asm string verbatim, one DASM line per logical newline."""
    pEmitter.Comment("inline asm")
    pEmitter.Raw(pText)
