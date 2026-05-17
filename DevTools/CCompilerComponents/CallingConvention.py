"""
Calling convention and ABI knobs for the C-to-DASM compiler.

All ABI decisions are centralized here so that a single edit re-targets the
calling convention. The first emulator run may require flipping
STACK_GROWS_DOWN if the hardware stack actually grows up.
"""


WORD_SIZE = 1  # everything (int, char, pointer) is one 24-bit word
WORD_MASK = 0xFFFFFF  # mask for emitting 24-bit immediates (handles negatives)

# Stack grows toward LOWER addresses, post-decrement (the emulator's CPU.Core/Cpu.cs:
# PUSH writes at SP then SP--; POP does SP++ then reads). CALL behaves the same as
# PUSH on the return address.
#
# After the prologue
#   PUSH REX        ; save old FP at mem[SP], then SP--
#   GET_SP REX      ; FP = current SP (one below the saved-FP slot)
# the frame looks like:
#   mem[FP + 3 + N] = arg N        (caller pushed args right-to-left; arg0 closest to ret_addr)
#   mem[FP + 2]     = return address
#   mem[FP + 1]     = saved old FP
#   mem[FP + 0]     = local slot 0 (next PUSH writes here)
#   mem[FP - 1]     = local slot 1
#   mem[FP - N]     = local slot N
#
# Arrays of size K declared at slot S occupy slots S..S+K-1, which sit at memory
# addresses FP - S, FP - S - 1, ..., FP - (S + K - 1). For C semantics
# (a[0] at the LOWEST address, a + i reaching a[i]), &a = FP - (S + K - 1).
STACK_GROWS_DOWN = True
ARG_BASE_OFFSET = 3      # arg N is at FP + (ARG_BASE_OFFSET + N)

# Frame pointer register (reserved across all C functions)
FP_REG = "REX"

# Scratch registers used by codegen for address arithmetic (never preserved)
ADDR_REG_A = "REY"
ADDR_REG_B = "REZ"

# Accumulator / return value
ACC_REG = "REA"

# Secondary scratch for binary ops, also used to discard popped values
SCRATCH_B = "REB"
SCRATCH_C = "REC"

# Caller-saved registers (callee may freely clobber)
CALLER_SAVED = ["REA", "REB", "REC"]

# Callee-saved registers (callee must PUSH/POP if it uses them)
CALLEE_SAVED = ["REN", "REO", "REP", "REQ", "RER", "RES", "RET", "REU", "REV", "REW"]

# Syscall argument registers, indexed by position.
# Position 0 = syscall number (placed in REA), then args 1..N follow.
SYSCALL_REGS = ["REA", "REB", "REC", "REN", "REO", "REP", "REQ", "RER", "RES"]


def LocalOffsetSign() -> int:
    """+1 if locals are below FP (stack grows down), -1 otherwise."""
    return 1 if STACK_GROWS_DOWN else -1


def ArgOffsetSign() -> int:
    """+1 if args are above FP (stack grows down), -1 otherwise."""
    return 1 if STACK_GROWS_DOWN else -1
