# PUSH and POP Examples

## PUSH
The PUSH instruction is used to push the value of a [Register]() onto the [Stack]().<br>
It's used to preserve values when jumping to another routine. These values can later be restored using the POP instruction.

## Syntax
`PUSH <Register>`

Pushes the value of `Register` onto the [Stack]().

## PUSH Example
<pre>
.Code

LDI REA, #10    ; loads decimal value 10 into REA

PUSH REA        ; pushes the value of REA onto the stack

LDI REA, #20    ; loads decimal value 20 into REA
...

; the previous value of REA is safely stored on the stack.
</pre>

# POP
The POP instruction is used to retrieve values from the stack. It takes the top-most value and places it back into a [Register]().

## Syntax
`POP <Register>`

Pops the top-most value from the stack and places it into the `Register`.

## POP Example
Building upon the PUSH Example:
<pre>
.Code

LDI REA, #10    ; loads decimal value 10 into REA

PUSH REA        ; pushes the value of REA onto the stack

LDI REA, #20    ; loads decimal value 20 into REA

POP REA         ; loads the saved decimal 20 value back into REA
</pre>

## Practical Example
<pre>
.Code

LDI REA, #10    ; loading decimal value 10 into REA

CALL CountREA   

ADD REA, REA    ; adding REA to itself (10 + 10)

HALT    ; halt CPU execution

; Counts up a value in REA
CountREA:
    PUSH REA
    PUSH REB

    LDI REA, #0     ; loading value 0 into REA
    LDI REB, #1     ; loading value 1 into REB

    ADD REA, REB    ; 0 + 1 , storing result in REA
    
    POP REB         ; restoring REB value
    POP REA         ; restoring REA value

    RTS             ; returning to call origin
</pre>

