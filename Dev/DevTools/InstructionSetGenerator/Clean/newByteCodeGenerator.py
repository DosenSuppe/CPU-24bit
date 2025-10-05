from MicroInstructions import *
from Flags import Flags

from Instruction import Instruction

FetchSequence = [0x7C0004, 0xB]
EndSequence = [0x800]

Instructions = [
    Instruction("NOP", 0x0).AddPossibleFlags([flag.value for flag in Flags])
    .AddFetch(FetchSequence).AddMain([]).AddEnd(EndSequence),

    Instruction("HALT", 0x1).AddPossibleFlags([flag.value for flag in Flags])
    .AddFetch(FetchSequence).AddMain([]).AddEnd(EndSequence),

    Instruction("MOV", 0x2).AddPossibleFlags([flag.value for flag in Flags])
    .AddFetch(FetchSequence).AddMain([]).AddEnd(EndSequence),

    Instruction("CALL"),

    Instruction("LOAD"),
    Instruction("STORE"),

    # ALU Instructions
    Instruction("ADD"),
    Instruction("SUB"),
    Instruction("MUL"),
    Instruction("DIV"),
    Instruction("B_AND"),
    Instruction("B_OR"),
    Instruction("B_XOR"),
    Instruction("CMP"),
]



