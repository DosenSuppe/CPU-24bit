# Stack Pointer Operations

The Stackpointer is a register that points to a location in memory defined as Stack". <br>
The "[Stack]() is used to store values for [CALL](), [INT]() and [PUSH]() instructions. 

D-Asm offers two instruction to read from / write to the stack.
The stack pointer decrements when pushing new values onto it and increments when release these values again.

**Please note that as of now, there is no stack protection!**<br>
**stack overflow is very possible and can corrupt your program!**

## SET_SP
The SET_SP instruction sets the origin location for the stack pointer.

## Syntax
`SET_SP <Value>` 

## SET_SP Example
<pre>
.Code

SET_SP #0xF00000    ; sets the stack pointer to start at 0xF00000

PUSH REA    ; Pushes REA onto the stack (on location 0xF00000) -> stack pointer goes to 0xEFFFFF
</pre>


## GET_SP
The GET_SP instruction loads the current value of the stack pointer in a register.

## Syntax
`GET_SP <Register>`

## SET_SP Example
<pre>
.Code

GET_SP REA 
</pre>
