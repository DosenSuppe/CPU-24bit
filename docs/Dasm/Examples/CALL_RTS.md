# CALL Example

The CALL instruction allows to unconditionally execute code referenced to a [Label](../Labels.md).

Unlike [JP](./JP.md), when invoking a CALL instruction, the [PC](../../CpuParts/PC.md) is pushed onto the [Stack](../../CpuParts/Stack.md).<br>
This allows the program to later resume at this position.

## Syntax
`CALL [Label | Value]`


## Example
<pre>
.Code

CALL MyLabel    ; Jump to "MyLabeL"

MyLabel:
    LDI REA, #10    ; loading decimal value 10 into REA
    HALT            ; halt CPU execution
</pre>
<br>

# 
# RTS Example

The RTS instruction allows to resume execute from the latest CALL origin.

The RTS will pop the top most stack value and place it into the [PC](../../CpuParts/PC.md).

## Syntax
`RTS`


## Example
<pre>
.Code

CALL MyLabel    ; Jump to "MyLabeL"
HALT            ; halt CPU execution

MyLabel:
    LDI REA, #10    ; loading decimal value 10 into REA
    RTS             ; return to the CALL origin
</pre>