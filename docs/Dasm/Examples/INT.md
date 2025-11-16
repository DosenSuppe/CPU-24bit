# Interrupts

Interrupts are essential for I/O processing. Interrupts allow the CPU to disengage from it's current task for a moment to complete different tasks.

The CPU offers interrupt capability for up to 7 devices (0 - 6). Each device has it's own ID and can output data specific to the interrupt it caused.

The priority of the device is handled by it's ID where a higher ID equals a higher Priority.

When an interrupt is invoked, the CPU stores the content of the [Flag-Register]() and [PC]() onto the [Stack]().

## Priority Example
Lets say we have the following devices:
- Keyboard : ID = 3
- a single button : ID = 6

If only the Keyboard sends an interrupt signal, the CPU will process it right away.

If however the Keyboard and the button send an interrupt around the same time (~ 1cycle difference) the button get's priority due to the higher ID.

## INT Instruction
The INT instruction generates an interrupt through software. This can be used to trigger internal processes in a program.

## Syntax
`INT`

## INT Example
<pre>
.Code
; assuming the Reset-Vector and stack pointer have been set already.
INT     ; this will cause the CPU to resume at the .ResetVector segment
HALT    ; stop CPU execution

.ResetVector
    LDI REA, #10
    RTI ; returning from the interrupt to latest execution step
</pre>

## RTI Example
The RTI instruction is similar to the [RTS]() instruction. The different is mainly that RTI pops two values from the Stack back into registers. These being the PC and Flag-Register's values. These values have been pushed onto the stack by the interrupt.

## Syntax
`RTI`

## GET_INT_ID Example
The GET_INT_ID instruction makes it possible for the software to read the ID of the device that caused the interrupt. The ID is loaded into a [Register]().

## Syntax
`GET_INT_ID <Register>`

## GET_INT_ID Example
Assuming that the ResetVector and Stack-Pointer have been set up already.
<pre>
.ResetVector    ; an incoming interrupt from a device
    PUSH REA    ; preserving the value of REA by pushing it onto the stack
    PUSH REB

    GET_INT_ID REA  ; getting the ID of the device that caused the interrupt

    LDI REB, #1

    SUB REA, REB    ; substracting 1 from the ID to check for device 1
    JPZ Device1Driver   ; if the zero flag has triggered -> jump to it's driver

Device1Driver:
    [...]
    POP REB     ; restoring modified registers
    POP REA

    RTI     ; returning from the interrupt 
</pre>

## GET_INT_DATA Example
The GET_INT_DATA instruction makes it possible for the software to read data associated by the interrupt and load it into a [Register]().

## Syntax
`GET_INT_DATA <Register>`

## GET_INT_DATA Example
Assuming that the ResetVector and Stack-Pointer have been set up already.
<pre>
.ResetVector    ; an incoming interrupt from a device
    PUSH REA    ; preserving the value of REA by pushing it onto the stack
    PUSH REB

    GET_INT_DATA REA  ; getting the ID of the device that caused the interrupt

    LDI REB, #1

    SUB REA, REB    ; substracting 1 from the data to check for the action context
    JPZ IncrementCounter    ; increment the counter
    JP DecrementCounter     ; else we decrement the counter

IncrementCounter:
    [...]
    POP REB     ; restoring modified registers
    POP REA

    RTI     ; returning from the interrupt 

DecrementCounter:
    [...]
    POP REB     ; restoring modified registers
    POP REA

    RTI     ; returning from the interrupt 
</pre>