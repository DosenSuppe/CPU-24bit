# Registers
The address on a register is stored in as 5 bit value.
The leading bit (5th bit) indicates whether it's an expansion port or not. <br>
0 0000 -> register range <br>
1 0000 -> expansion port range <br>

This CPU offers:
- 11 general purpose registers
- 3 ALU registers
- 1 stack pointer 
- 1 program counter
- 16 expansion ports

| Register | Value | Type |
|:--------:|:-----:|------|
| REA | 0x00 | ALU register |
| REB | 0x01 | ALU register |
| ACC | 0x02 | ALU register |
| REP - REZ | 0x03 - 0x0D | general purpose register |
| SP | 0x0E | stack pointer |
| PC | 0x0F | program counter |
| EP0 - EPF | 0x10 - 0x1F | expansion port |