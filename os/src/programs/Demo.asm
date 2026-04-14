; =============================================================================
; Demo Programs
; =============================================================================
; Visual demo programs that can be triggered from the shell.
; These demonstrate the CPU's capabilities on the 64x64 display.
; =============================================================================

!IMPORT "../drivers/Video.asm" as Video

.Demo

; -----------------------------------------------------------------------------
; ColorPattern - Draw a color gradient pattern across the display.
; Each column gets a color (column mod 16), creating a repeating rainbow.
; -----------------------------------------------------------------------------
ColorPattern:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN

    CALL Video.ClearScreen

    LDI REX, #0               ; x = 0 (also serves as color index)

ColorPatternOuterLoop:
    LDI REY, #0               ; y = 0

ColorPatternInnerLoop:
    MOV REA, REX               ; x coordinate
    MOV REB, REY               ; y coordinate
    MOV REC, REX               ; color = column index mod 16
    PUSH REN
    LDI REN, #0x0F
    AND REC, REN               ; color = x & 0xF
    POP REN
    CALL Video.WritePixel

    ; y++
    LDI REN, #1
    ADD REY, REN

    ; if y == 64, next column
    MOV REA, REY
    LDI REN, #64
    SUB REA, REN
    JPZ ColorPatternNextCol

    JP ColorPatternInnerLoop

ColorPatternNextCol:
    ; x++
    LDI REN, #1
    ADD REX, REN

    ; if x == 64, done
    MOV REA, REX
    LDI REN, #64
    SUB REA, REN
    JPZ ColorPatternDone

    JP ColorPatternOuterLoop

ColorPatternDone:
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DiagonalWipe - Animate a diagonal color wipe across the display.
; Draws pixels along diagonals with incrementing colors.
; -----------------------------------------------------------------------------
DiagonalWipe:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REQ

    CALL Video.ClearScreen

    LDI REQ, #0               ; diagonal index (0-30 covers all diagonals)
    LDI REN, #1

DiagWipeOuterLoop:
    ; For each diagonal d, draw pixels where x+y == d
    LDI REX, #0               ; x = 0

DiagWipeInnerLoop:
    ; y = diagonal - x
    MOV REY, REQ
    SUB REY, REX

    ; if y < 0 (carry flag set from underflow), skip
    JPC DiagWipeSkipPixel

    ; if y >= 64, skip
    MOV REA, REY
    PUSH REN
    LDI REN, #64
    SUB REA, REN
    POP REN
    JPZ DiagWipeSkipPixel
    ; if no zero and no carry, y >= 16 (positive result means y > 16)
    ; Actually need to check differently. If REA >= 0 and not zero, y > 16.
    ; For simplicity, just check if y > 15 using carry
    ; After SUB: if result is 0, y==16 (skip). If carry, y<16 (draw).

    ; Verify x is in range (0-63)
    MOV REA, REX
    PUSH REN
    LDI REN, #64
    SUB REA, REN
    POP REN
    JPZ DiagWipeSkipPixel

    ; Draw the pixel
    MOV REA, REX               ; x
    MOV REB, REY               ; y
    ; Color = diagonal index mod 16
    MOV REC, REQ
    PUSH REN
    LDI REN, #0x0F
    AND REC, REN               ; color = diag & 0xF
    POP REN
    CALL Video.WritePixel

DiagWipeSkipPixel:
    ; x++
    ADD REX, REN

    ; if x == 64, advance to next diagonal
    MOV REA, REX
    PUSH REN
    LDI REN, #64
    SUB REA, REN
    POP REN
    JPZ DiagWipeNextDiag

    JP DiagWipeInnerLoop

DiagWipeNextDiag:
    ; diagonal++
    ADD REQ, REN

    ; if diagonal == 127, done
    MOV REA, REQ
    PUSH REN
    LDI REN, #127
    SUB REA, REN
    POP REN
    JPZ DiagWipeDone

    JP DiagWipeOuterLoop

DiagWipeDone:
    POP REQ
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; Checkerboard - Draw a checkerboard pattern.
; @REA: Color 1
; @REB: Color 2
; -----------------------------------------------------------------------------
Checkerboard:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REQ

    CALL Video.ClearScreen

    MOV REQ, REA               ; save color 1 in REQ
    PUSH REB                   ; save color 2 on stack

    LDI REX, #0               ; x = 0

CheckerOuterLoop:
    LDI REY, #0               ; y = 0

CheckerInnerLoop:
    ; Determine color: (x + y) & 1
    MOV REA, REX
    ADD REA, REY
    LDI REN, #1
    AND REA, REN               ; REA = (x+y) & 1

    SUB REA, REN               ; if result is 0, bit was 1
    JPZ CheckerColor2

    ; Use color 1
    MOV REC, REQ
    JP CheckerDraw

CheckerColor2:
    ; Use color 2
    POP REC                    ; pop color 2
    PUSH REC                   ; re-push it for next iteration

CheckerDraw:
    MOV REA, REX               ; x
    MOV REB, REY               ; y
    CALL Video.WritePixel

    ; y++
    LDI REN, #1
    ADD REY, REN

    ; if y == 64, next column
    MOV REA, REY
    LDI REN, #64
    SUB REA, REN
    JPZ CheckerNextCol

    JP CheckerInnerLoop

CheckerNextCol:
    ; x++
    LDI REN, #1
    ADD REX, REN

    ; if x == 64, done
    MOV REA, REX
    LDI REN, #64
    SUB REA, REN
    JPZ CheckerDone

    JP CheckerOuterLoop

CheckerDone:
    POP REB                    ; clean up color 2 from stack

    POP REQ
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS

