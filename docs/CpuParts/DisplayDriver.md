# Display Driver (Matrix Driver)
The display driver provides developers an easier way to write to a logisim LED-Matrix.

## Subroutines

### RenderFrame
The RenderFrame subroutine copies all values from the `display buffer` memory space to the display.

Code example:
```
!IMPORT "./drivers/DisplayDriver.asm" as DisplayDriver ; import the display driver

.Code

SET_SP $Stack.Start ; set up the stack pointer

LDI REA, #8                     ; bit-map value 8
LDI REB, #5                     ; 6th column index, offset of 5
CALL DisplayDriver.DrawColumn   ; drawing the column to the frame buffer

; .DrawColumn only writes to the Frame-Buffer, not the display itself.
; For that, the .RenderFrame subroutine is used.

CALL DisplayDriver.RenderFrame  ; copies the buffer to the display

HALT
```
---

### DrawColumn
```
@REA : The bit-map value to be drawn
@REB : Column offset
```

The Draw Column subroutine takes two paramters:
1. The value to be displayed by the column, stored in REA
2. The offset of the column from the frame buffer, stored in REB

Code example:
```
.Code

SET_SP $Stack.Start ; set up the stack pointer

LDI REA, #8                     ; bit-map value 8
LDI REB, #5                     ; 6th column index, offset of 5
CALL DisplayDriver.DrawColumn   ; drawing the column to the frame buffer
; .DrawColumn only writes to the Frame-Buffer, not the display itself.

HALT
```
