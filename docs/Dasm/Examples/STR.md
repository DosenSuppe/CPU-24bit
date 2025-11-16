# STR Example

The STR instruction allows values to be stored in memory.

## Syntax
`STR <[Register|Address]>, <Register>`

Values can be stored either by direct or indirect reference.

## Example
<pre>
.Code

LDI REA, #1         ; load decimal value 1 into REA 

; direct reference
STR [0xF000], REA   ; store value of REA in memory at address 0xF0000

; indirect reference
STR [REX], REA      ; store value of REA in memory with the address being the value of REX
</pre>

