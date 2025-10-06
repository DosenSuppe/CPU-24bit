# The 24-Bit CPU

This Repo includes my concept of a 24-Bit CPU.

## What does this CPU offer?
- 16 MB RAM
- ALU that can perform:
  - addition, subtraction, multiplication, division
  - logical AND, OR and XOR operations
  - bit-shifting
  - comparision  ('>', '<', '=')
- 16 expansion ports
- 11 general purpose registers
- up to 256 unique instructions
- clock speed of up to 3.8Khz (messured on [my hardware](/docs/MyHardware.md))

## What is Planned?
- comprehensive [instruction set](/docs/InstructionSet.md)
- adding I/O devices such as:
  - 256x256 display (including a [display-adapter](/docs/DisplayAdapter.md))
  - output terminal
  - a clock displaying UTC time (more [here](/docs/Clock.md))
  - keyboard
- [assembly compiler](docs/AssemblyCompiler.md)
- a port of a limited C compiler

## More Technical Information
- [instruction layout](/docs/InstructionSet.md#Layout)
- [addressing registers](/docs/Registers.md)

## Requirements
- Visual Studio Code
- [Logisim Evolution](https://github.com/logisim-evolution/logisim-evolution) ([latest binaries](https://github.com/logisim-evolution/logisim-evolution/releases))

#
**This Repo is actively maintained.** <br>
**10/07/2025**