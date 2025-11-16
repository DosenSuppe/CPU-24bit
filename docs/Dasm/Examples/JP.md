# JP Example

The JP instruction is used to unconditionally jump to a section in a program.
It does not safe the current value of the [PC]() to the [Stack]()!

## Syntax
`JP <[Label | Address]>`

## Example
<pre>
.Code

JP MyLabel

MyLabel:
    LDI REA, #10 ; loads decimal value 10 into REA
    HALT         ; halt CPU execution
</pre>
<br>

# JPC Example

Similar to the JP instruction, the JPC instruction jumps to a label or reference in memory. However, it only jumps if the previous arithmatic operation triggered a carry-flag.

<pre>
.Code

; loading values for operation
LDI REA, #1
LDI REB, #0xFFFFFF

ADD REA, REB    ; 0xFFFFFF + 1 results in a carry

JPC MyLabel     ; jumps to "MyLabel"

; loading values for operation
LDI REA, #1     
LDI REB, #0

ADD REA, REB    ; 0x1 + 0x0 does not result in a carry

JPC OtherLabel  ; does not jump

MyLabel:
    [...]

OtherLabel:
    [...]
</pre>


# JPZ Example

Similar to the JPC instruction, the JPZ instruction jumps to a label or reference in memory only if a certain condition is fulfilled. For JPZ, the condition is that the previous arithmatic operation triggered the zero-flag.

<pre>
.Code

; loading values for operation
LDI REA, #1
LDI REB, #1

SUB REA, REB    ; 1 - 1 = 0 -> the zero-flag is being set

JPZ MyLabel     ; jumps to "MyLabel"

; loading values for operation
LDI REA, #1     
LDI REB, #0

SUB REA, REB    ; 0x1 - 0x0 does not result in a zero-flag

JPZ OtherLabel  ; does not jump

MyLabel:
    [...]

OtherLabel:
    [...]
</pre>
