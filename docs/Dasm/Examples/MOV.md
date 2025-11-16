# MOV Example

The MOV instruction allows values to be moved between registers.

## Syntax
`MOV <Register1>, <Register2>`

Value of `Register2` is loaded into `Register1`.

MOV only works on two registers. It cannot load immediates into a register.
If you want to load immediates into a register, please have a look at [LDI](./LDI.md).

## Example
<pre>
.Code
LDI REA, #10    ; load decimal value 10 into REA
MOV REX, REA    ; move the value of REA into REX
                ; REA will retain it's value of 10
</pre>

