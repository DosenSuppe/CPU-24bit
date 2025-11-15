# The 24-Bit CPU

This repository contains my implementation of a 24-bit CPU, building upon the 16-bit CPU I created in 2023 as part of a school project.

At the time, my understanding of CPU architecture was limited, and the 16-bit design relied on several improvised solutions. While it met the requirements of the project, I have since revisited the topic and invested significant time in researching proper CPU design principles and instruction handling.

This project represents a cleaner, more robust, and more thoughtfully designed successor to that earlier work. It incorporates the lessons I’ve learned and reflects a deeper understanding of computer architecture.

I recognize that there is still much more to explore in this field, and I welcome feedback, suggestions, and contributions to help improve this project further.

## Current State
- Implements a RISC-style instruction set architecture (ISA) on a von Neumann bus architecture.
- Supports 16 MB of memory, with 14 MB available as addressable RAM and 2 MB reserved for memory-mapped I/O (MMIO) and storage.
- Provides 16 general-purpose registers (GPRs).
- Includes interrupt handling support.
- Features a 24-bit Arithmetic Logic Unit (ALU).

## Plans
This project was created primarily for educational purposes, but my goal is to evolve it into a fully functional 24-bit CPU with features that make software development on it practical and enjoyable.

Planned improvements include:

- Refining the instruction set to address current limitations with immediate constants and memory access.
- For example, instructions such as LDI REA, [#0xF00000] or ADD REA, #1, REC are currently unsupported and require workarounds.
- Expanding instruction support to make operations more intuitive and efficient.
- Enhancing overall CPU functionality with features commonly found in modern educational CPU designs.
- Improving documentation and tooling to make the CPU easier to understand, use, and extend.

## Docs
- [How to use the compiler](/docs/DevelopmentSoftware/Compiler.md)
- [How to use the linker](/docs/DevelopmentSoftware/Linker.md)
- [How to install the syntax highlighter](/docs/DevelopmentSoftware/DasmCodeHighlighter.md)
- [How to use the assembly language](/docs/Dasm/index.md)
- [CPU components explained](/docs/CpuParts/index.md)


## Requirements
- Visual Studio Code
- Python 3.10
- [Logisim Evolution](https://github.com/logisim-evolution/logisim-evolution) ([latest binaries](https://github.com/logisim-evolution/logisim-evolution/releases))

#
**This Repo is actively maintained.** <br>