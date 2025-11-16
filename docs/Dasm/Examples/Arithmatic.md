# Arithmatic Operations Example

The CPU contains a 24 Bit ALU which can perform various arithmatic operations.

## ALU Operations
- Addition
- Substraction
- Division
- Multiplication
- Bit-Shifting to the left
- Bit-Shifting to the right
- NAND operation
- AND operation
- OR operation
- XOR operation
- NOR operation
- NOT operation

## General Syntax
This is the syntax that applies to most operations.<br>

`<OPERATION> <Register1>, <Register2> [, <Register3>]`

`OPERATION` is any ALU operation except `NOT`. <br>
Any operation in a 2-argument statement is processed as follows: <br>

The value of `Register2` is used in the operation on `Register1`. The result is then stored in `Register1`.

If the operation is a 3-argument statement, the value of `Register2` is used in the operation on `Register1`. The result is then stored in `Register3`.

## Example
<pre>
ADD REA, REX        ; Adding REX to REA and storing the result in REA
ADD REA, REX, REC   ; Adding REX to REA and storing the result in REC
</pre>

## NOT Syntax
`NOT <Register1> [, <Register2>]`

In case of an 1-argument operation, the `Register1` value is being negated. The result is stored in `Register1`.

In case of a 2-argument operation, the `Register1` value is being negated. The result is stored in `Register2`.

## NOT Example
<pre>
NOT REA         ; negates the value stored in REA and stores the result back in REA
NOT REA, REB    ; negates the value stored in REA and stores the result in REB
</pre>


