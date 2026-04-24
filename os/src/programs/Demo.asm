; =============================================================================
; Demo Programs
; =============================================================================
; Visual demo programs showcasing the 256-color display.
; All routines use the optimized Video driver packed-word rendering.
; =============================================================================

!IMPORT "../drivers/Video.asm" as Video

.Demo

; -----------------------------------------------------------------------------
; ColorPattern - Draw a full 256-color gradient across the display.
; Uses FillRect for fast column-wide fills — each column is a solid color.
; 64 columns × 4 colors per column step = smooth gradient.
; -----------------------------------------------------------------------------
ColorPattern:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN

    CALL Video.ClearScreen

    LDI REN, #0               ; column x = 0

ColorPatternLoop:
    ; color = x * 4 (maps 0-63 → 0-252 across XTerm256 palette)
    LDI REX, #4
    MUL REN, REX, REC         ; REC = x * 4 = color

    ; FillRect: x=REN, y=0, color=REC, width=1, height=64
    MOV REA, REN
    LDI REB, #0
    LDI REX, #1
    LDI REY, #64
    CALL Video.FillRect

    ; x++
    LDI REX, #1
    ADD REN, REX

    ; if x == 64, done
    MOV REA, REN
    LDI REX, #64
    SUB REA, REX
    JPZ ColorPatternDone

    JP ColorPatternLoop

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
; Uses DrawLine for fast diagonal rendering with 256-color palette.
; Draws successive diagonals from top-left to bottom-right.
; -----------------------------------------------------------------------------
DiagonalWipe:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN

    CALL Video.ClearScreen

    LDI REN, #0               ; diagonal index

DiagWipeLoop:
    ; Color = diagonal * 2 (wraps through XTerm256)
    LDI REX, #2
    MUL REN, REX, REC         ; REC = color

    ; Draw diagonal line for this step
    ; For diagonal d: line from (0, d) to (d, 0) if d < 64
    ;                 or from (d-63, 63) to (63, d-63) if d >= 64

    MOV REA, REN
    LDI REX, #63
    SUB REA, REX
    JPZ DiagWipeSecondHalf
    JPC DiagWipeFirstHalf

DiagWipeSecondHalf:
    ; d >= 63: line from (d-63, 63) to (63, d-63)
    MOV REA, REN
    LDI REX, #63
    SUB REA, REX              ; REA = d - 63 = x1
    LDI REB, #63              ; y1 = 63
    LDI REX, #63              ; x2 = 63
    MOV REY, REA              ; y2 = d - 63
    CALL Video.DrawLine
    JP DiagWipeAdvance

DiagWipeFirstHalf:
    ; d < 63: line from (0, d) to (d, 0)
    LDI REA, #0               ; x1 = 0
    MOV REB, REN              ; y1 = d
    MOV REX, REN              ; x2 = d
    LDI REY, #0               ; y2 = 0
    CALL Video.DrawLine

DiagWipeAdvance:
    LDI REX, #1
    ADD REN, REX

    ; if diagonal == 127, done
    MOV REA, REN
    LDI REX, #127
    SUB REA, REX
    JPZ DiagWipeDone

    JP DiagWipeLoop

DiagWipeDone:
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; Checkerboard - Draw a checkerboard pattern using FillRect.
; Draws 8x8 pixel squares in alternating colors.
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
    PUSH REO
    PUSH REP
    PUSH REQ

    CALL Video.ClearScreen

    MOV REO, REA              ; REO = color 1
    MOV REP, REB              ; REP = color 2

    LDI REN, #0               ; tile_y = 0 (tile row: 0,1,2,...,7)

CheckerYLoop:
    LDI REQ, #0               ; tile_x = 0 (tile col: 0,1,2,...,7)

CheckerXLoop:
    ; Determine color: (tile_x + tile_y) & 1
    ADD REQ, REN, REA         ; REA = tile_x + tile_y
    LDI REB, #1
    AND REA, REB              ; REA = (tile_x + tile_y) & 1

    SUB REA, REB              ; if zero, bit was 1 → color 2
    JPZ CheckerUseColor2
    MOV REC, REO              ; color 1
    JP CheckerDraw
CheckerUseColor2:
    MOV REC, REP              ; color 2

CheckerDraw:
    ; FillRect(tile_x*8, tile_y*8, color, 8, 8)
    LDI REX, #8
    MUL REQ, REX, REA         ; REA = tile_x * 8 = pixel x
    MUL REN, REX, REB         ; REB = tile_y * 8 = pixel y
    LDI REX, #8
    LDI REY, #8
    CALL Video.FillRect

    ; tile_x++
    LDI REX, #1
    ADD REQ, REX

    ; if tile_x == 8, next row
    MOV REA, REQ
    LDI REX, #8
    SUB REA, REX
    JPZ CheckerNextRow
    JP CheckerXLoop

CheckerNextRow:
    LDI REX, #1
    ADD REN, REX

    MOV REA, REN
    LDI REX, #8
    SUB REA, REX
    JPZ CheckerDone
    JP CheckerYLoop

CheckerDone:
    POP REQ
    POP REP
    POP REO
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS
