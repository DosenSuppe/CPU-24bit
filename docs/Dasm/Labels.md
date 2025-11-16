# Labels
Labels are similar to [Segments](./Segments.md). They enable partioning code into blocks. The difference to Segments is that Labels are relative to their Segment.

Labels can be used to access code from other memory addresses using various instructions (e.g. JP, CALL, etc.)

## How to use them
Syntax: <br>
`LabelName:`

Example:
<pre>
.Code

JP MyFirstLabel ; jump to the "MyFirstLabel" Label

MyFirstLabel:
    LDI REA, #10 ; load decimal value 10 into REA

    CALL MyOtherLabel ; Calling "MyOtherLabel"

    HALT    ; Halt CPU execution

MyOtherLabel:
    LDI REB, #0xFF  ; loads hex value 0xFF into REB
    RTS             ; returning to the origin of the call
</pre>