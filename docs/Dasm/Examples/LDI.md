# LDI Example

The LDI instruction allows immediate values to be loaded into registers.
These values can be by reference or constants.

## Syntax
`LDI <Register>, <Value | [Address | Register]>`

LDI only works on immediates, for moving a value between registers please resort to using the [MOV](./MOV.md) instruction.

## Example
<pre>
.Code
LDI REA, #10        ; load decimal value 10 into REA
LDI REB, [#0xFF10]  ; loads the value at memory address 0xFF10 into REB
LDI REC, [REA]      ; loads the value at memory address of REA (10 / 0x0A)

LDI REX, REA        ; this does not work! use `MOV REX, REA` instead!
</pre>

