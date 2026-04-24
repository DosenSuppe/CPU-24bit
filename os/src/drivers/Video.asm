; =============================================================================
; Video Display Driver
; =============================================================================
; Driver for the 64x64 pixel video display with 256 colors (XTerm256).
; Hardware address: $VideoDisplay.Start
;
; Pixel write format (packed into one 24-bit word):
;   Bits 0-5  : X coordinate (0-63)
;   Bits 6-11 : Y coordinate (0-63)
;   Bits 12-19: Color (XTerm256, 0-255)
;   Bit  23   : Clear flag (1 = clear entire screen)
;
; Packed pixel = (color << 12) | (y << 6) | x
;
; Dev tip — fast custom rendering:
;   1. Call PackPixel to build a packed word
;   2. Incrementing the packed word by 1 advances X
;   3. Incrementing by 64 (#0x40) advances Y
;   4. Write directly: LDI reg, $VideoDisplay.Start ; STR [reg], packed
; =============================================================================

.VideoDriver

; =============================================================================
; CORE
; =============================================================================

; -----------------------------------------------------------------------------
; PackPixel - Pack (x, y, color) into a display word.
; Returns the packed pixel in REX. Does not write to the display.
; Useful for building custom fast renderers.
; -----------------------------------------------------------------------------
@REA: X coordinate (0-63)
@REB: Y coordinate (0-63)
@REC: Color (0-255)
; Returns: REX = packed pixel word
PackPixel:
    PUSH REN
    LDI REN, #6
    MOV REX, REC
    SHL REX, REN
    ADD REX, REB
    SHL REX, REN
    ADD REX, REA
    POP REN
    RTS

; -----------------------------------------------------------------------------
; WritePixel - Draw a single pixel on the video display.
; -----------------------------------------------------------------------------
@REA: X coordinate (0-63)
@REB: Y coordinate (0-63)
@REC: Color (0-255)
WritePixel:
    PUSH REN
    PUSH REX

    LDI REN, #6
    MOV REX, REC
    SHL REX, REN
    ADD REX, REB
    SHL REX, REN
    ADD REX, REA

    LDI REN, $VideoDisplay.Start
    STR [REN], REX

    POP REX
    POP REN
    RTS

; -----------------------------------------------------------------------------
; ClearScreen - Clear the entire display (fill with black).
; -----------------------------------------------------------------------------
ClearScreen:
    PUSH REX
    PUSH REY

    LDI REX, #0x900000
    LDI REY, $VideoDisplay.Start
    STR [REY], REX

    POP REY
    POP REX
    RTS

; -----------------------------------------------------------------------------
; FillScreen - Fill the entire display with a single color.
; -----------------------------------------------------------------------------
@REA: Color (0-255)
FillScreen:
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY

    LDI REB, #12
    MOV REX, REA
    SHL REX, REB              ; REX = color << 12

    LDI REY, $VideoDisplay.Start
    LDI REB, #1
    LDI REC, #0x1000          ; 4096 pixels (64*64)

FillScreenLoop:
    STR [REY], REX
    ADD REX, REB
    SUB REC, REB
    JPZ FillScreenDone
    JP FillScreenLoop

FillScreenDone:
    POP REY
    POP REX
    POP REC
    POP REB
    RTS

; =============================================================================
; LINES
; =============================================================================

; -----------------------------------------------------------------------------
; DrawHLine - Draw a horizontal line (fast packed-word loop).
; -----------------------------------------------------------------------------
@REA: X start (0-63)
@REB: Y position (0-63)
@REC: Color (0-255)
@REX: Length (pixels, >= 1)
DrawHLine:
    PUSH REA
    PUSH REX
    PUSH REN
    PUSH REY

    LDI REN, #6
    MOV REY, REC
    SHL REY, REN
    ADD REY, REB
    SHL REY, REN
    ADD REY, REA

    LDI REA, $VideoDisplay.Start
    LDI REN, #1

DrawHLineLoop:
    STR [REA], REY
    SUB REX, REN
    JPZ DrawHLineDone
    ADD REY, REN
    JP DrawHLineLoop

DrawHLineDone:
    POP REY
    POP REN
    POP REX
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DrawVLine - Draw a vertical line (fast packed-word loop, +64 per step).
; -----------------------------------------------------------------------------
@REA: X position (0-63)
@REB: Y start (0-63)
@REC: Color (0-255)
@REX: Length (pixels, >= 1)
DrawVLine:
    PUSH REB
    PUSH REX
    PUSH REN
    PUSH REY
    PUSH REA

    LDI REN, #6
    MOV REY, REC
    SHL REY, REN
    ADD REY, REB
    SHL REY, REN
    ADD REY, REA

    LDI REB, $VideoDisplay.Start
    LDI REA, #64
    LDI REN, #1

DrawVLineLoop:
    STR [REB], REY
    SUB REX, REN
    JPZ DrawVLineDone
    ADD REY, REA
    JP DrawVLineLoop

DrawVLineDone:
    POP REA
    POP REY
    POP REN
    POP REX
    POP REB
    RTS

; -----------------------------------------------------------------------------
; DrawLine - Draw an arbitrary line using Bresenham's algorithm.
;            Uses packed-word increments (+1 for X, +/-64 for Y).
; -----------------------------------------------------------------------------
@REA: X1
@REB: Y1
@REC: Color (0-255)
@REX: X2
@REY: Y2
DrawLine:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REO
    PUSH REP
    PUSH REQ
    PUSH RES
    PUSH RET
    PUSH REU

    ; ---- Precompute color << 12 ----
    LDI REN, #12
    MOV REP, REC
    SHL REP, REN

    ; ---- Compute dx, x_step ----
    MOV REC, REX
    SUB REC, REA
    JPC DrawLine_NegDX
    MOV REN, REC
    LDI REO, #1
    JP DrawLine_CalcDY

DrawLine_NegDX:
    MOV REC, REA
    SUB REC, REX
    MOV REN, REC
    LDI REO, #0xFFFFFF

DrawLine_CalcDY:
    ; ---- Compute dy, y_step ----
    MOV REC, REY
    SUB REC, REB
    JPC DrawLine_NegDY
    MOV REQ, REC
    LDI RES, #64
    JP DrawLine_Setup

DrawLine_NegDY:
    MOV REC, REB
    SUB REC, REY
    MOV REQ, REC
    LDI RES, #0xFFFFC0

DrawLine_Setup:
    ; REN=dx, REQ=dy, REO=x_step, RES=y_step, REP=color<<12
    ; Pack start pixel into REU
    LDI REC, #6
    MOV REU, REB
    SHL REU, REC
    ADD REU, REA
    ADD REU, REP

    LDI REB, $VideoDisplay.Start

    ; ---- Determine major axis ----
    MOV REC, REN
    SUB REC, REQ
    JPC DrawLine_VertMajor

    ; ---- Horizontal major ----
    MOV REC, REN
    LDI REA, #1
    SHR REC, REA
    MOV REX, REN
    ADD REX, REA

DrawLine_HLoop:
    STR [REB], REU
    SUB REX, REA
    JPZ DrawLine_Done
    ADD REU, REO
    SUB REC, REQ
    JPC DrawLine_HAdjust
    JP DrawLine_HLoop

DrawLine_HAdjust:
    ADD REC, REN
    ADD REU, RES
    JP DrawLine_HLoop

DrawLine_VertMajor:
    ; ---- Vertical major ----
    MOV REC, REQ
    LDI REA, #1
    SHR REC, REA
    MOV REX, REQ
    ADD REX, REA

DrawLine_VLoop:
    STR [REB], REU
    SUB REX, REA
    JPZ DrawLine_Done
    ADD REU, RES
    SUB REC, REN
    JPC DrawLine_VAdjust
    JP DrawLine_VLoop

DrawLine_VAdjust:
    ADD REC, REQ
    ADD REU, REO
    JP DrawLine_VLoop

DrawLine_Done:
    POP REU
    POP RET
    POP RES
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

; =============================================================================
; RECTANGLES
; =============================================================================

; -----------------------------------------------------------------------------
; DrawRect - Draw a rectangle outline (4 lines).
; -----------------------------------------------------------------------------
@REA: X start
@REB: Y start
@REC: Color (0-255)
@REX: Width
@REY: Height
DrawRect:
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY
    PUSH REN

    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY

    ; Top edge
    CALL DrawHLine

    ; Bottom edge
    POP REY
    POP REX
    POP REB
    POP REA
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY
    LDI REN, #1
    ADD REB, REY
    SUB REB, REN
    CALL DrawHLine

    ; Left edge
    POP REY
    POP REX
    POP REB
    POP REA
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY
    MOV REX, REY
    CALL DrawVLine

    ; Right edge
    POP REY
    POP REX
    POP REB
    POP REA
    LDI REN, #1
    ADD REA, REX
    SUB REA, REN
    MOV REX, REY
    CALL DrawVLine

    POP REN
    POP REY
    POP REX
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; FillRect - Fill a solid rectangle (fast packed-word row scanning).
;            Inner loop: ~5 instructions per pixel.
; -----------------------------------------------------------------------------
@REA: X start
@REB: Y start
@REC: Color (0-255)
@REX: Width (>= 1)
@REY: Height (>= 1)
FillRect:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REQ
    PUSH REO
    PUSH RES

    ; Compute row advance = 65 - width
    LDI REQ, #65
    SUB REQ, REX

    ; Pack start pixel
    PUSH REX
    PUSH REY
    CALL PackPixel            ; REX = packed pixel
    MOV REA, REX
    POP REY
    POP REX

    LDI REB, $VideoDisplay.Start
    MOV RES, REX
    LDI REN, #1

FillRectRowLoop:
    MOV REO, RES

FillRectPixelLoop:
    STR [REB], REA
    SUB REO, REN
    JPZ FillRectNextRow
    ADD REA, REN
    JP FillRectPixelLoop

FillRectNextRow:
    SUB REY, REN
    JPZ FillRectDone
    ADD REA, REQ
    JP FillRectRowLoop

FillRectDone:
    POP RES
    POP REO
    POP REQ
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; =============================================================================
; CIRCLES
; =============================================================================

; -----------------------------------------------------------------------------
; DrawCircle - Draw a circle outline (midpoint algorithm, 8-way symmetry).
; -----------------------------------------------------------------------------
@REA: Center X
@REB: Center Y
@REC: Color (0-255)
@REX: Radius
DrawCircle:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REO
    PUSH REP
    PUSH REQ
    PUSH RES
    PUSH RET

    MOV REO, REA              ; REO = cx
    MOV REP, REB              ; REP = cy
    MUL REX, REX, RES         ; RES = r^2
    MOV REN, REX              ; REN = circle_x = radius
    LDI REQ, #0               ; REQ = circle_y = 0

DrawCircle_Loop:
    ; Plot 8 symmetric points
    ADD REO, REN, REA
    ADD REP, REQ, REB
    CALL WritePixel
    SUB REO, REN, REA
    ADD REP, REQ, REB
    CALL WritePixel
    ADD REO, REN, REA
    SUB REP, REQ, REB
    CALL WritePixel
    SUB REO, REN, REA
    SUB REP, REQ, REB
    CALL WritePixel
    ADD REO, REQ, REA
    ADD REP, REN, REB
    CALL WritePixel
    SUB REO, REQ, REA
    ADD REP, REN, REB
    CALL WritePixel
    ADD REO, REQ, REA
    SUB REP, REN, REB
    CALL WritePixel
    SUB REO, REQ, REA
    SUB REP, REN, REB
    CALL WritePixel

    ; Advance: y++
    LDI RET, #1
    ADD REQ, RET

    ; Check y > x → done
    MOV RET, REQ
    SUB RET, REN
    JPZ DrawCircle_Last
    JPC DrawCircle_Check
    JP DrawCircle_Done

DrawCircle_Last:
    ; y == x: plot final point and done
    ADD REO, REN, REA
    ADD REP, REQ, REB
    CALL WritePixel
    SUB REO, REN, REA
    ADD REP, REQ, REB
    CALL WritePixel
    ADD REO, REN, REA
    SUB REP, REQ, REB
    CALL WritePixel
    SUB REO, REN, REA
    SUB REP, REQ, REB
    CALL WritePixel
    JP DrawCircle_Done

DrawCircle_Check:
    ; Check if x^2 + y^2 > r^2 → x--
    MUL REN, REN, RET         ; RET = x^2
    MUL REQ, REQ, REY         ; REY = y^2
    ADD RET, REY
    SUB RET, RES
    JPZ DrawCircle_Loop
    JPC DrawCircle_Loop
    LDI RET, #1
    SUB REN, RET
    JP DrawCircle_Loop

DrawCircle_Done:
    POP RET
    POP RES
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

; -----------------------------------------------------------------------------
; FillCircle - Fill a circle using horizontal spans per row.
;              Computes x-extent via squared-distance shrink.
; -----------------------------------------------------------------------------
@REA: Center X
@REB: Center Y
@REC: Color (0-255)
@REX: Radius
FillCircle:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REO
    PUSH REP
    PUSH REQ
    PUSH RES
    PUSH RET
    PUSH REU

    MOV REO, REA              ; cx
    MOV REP, REB              ; cy
    MOV REU, REC              ; color (saved)
    MUL REX, REX, RES         ; RES = r^2
    MOV REN, REX              ; REN = cur_x = r
    LDI REQ, #0               ; REQ = dy = 0

FillCircle_Loop:
    ; ---- Span at cy + dy ----
    MOV REC, REU
    ADD REP, REQ, REB         ; y = cy + dy
    SUB REO, REN, REA         ; x = cx - cur_x
    ADD REN, REN, REX         ; REX = 2 * cur_x
    LDI RET, #1
    ADD REX, RET              ; REX = 2*cur_x + 1 = span length
    CALL DrawHLine

    ; Restore cur_x from span length
    SUB REX, RET
    LDI RET, #1
    SHR REX, RET
    MOV REN, REX

    ; ---- Span at cy - dy (if dy > 0) ----
    LDI RET, #0
    MOV REY, REQ
    SUB REY, RET
    JPZ FillCircle_Advance

    MOV REC, REU
    SUB REP, REQ, REB         ; y = cy - dy
    SUB REO, REN, REA         ; x = cx - cur_x
    ADD REN, REN, REX
    LDI RET, #1
    ADD REX, RET
    CALL DrawHLine

    ; Restore cur_x
    SUB REX, RET
    LDI RET, #1
    SHR REX, RET
    MOV REN, REX

FillCircle_Advance:
    LDI RET, #1
    ADD REQ, RET              ; dy++

    ; Terminate when dy^2 > r^2
    MUL REQ, REQ, RET         ; RET = dy^2
    SUB RET, RES
    JPZ FillCircle_Done
    JPC FillCircle_Shrink
    JP FillCircle_Done

FillCircle_Shrink:
    ; Shrink x while x^2 + dy^2 > r^2
    MUL REN, REN, RET         ; RET = x^2
    MUL REQ, REQ, REY         ; REY = dy^2
    ADD RET, REY
    SUB RET, RES
    JPZ FillCircle_Loop
    JPC FillCircle_Loop
    LDI RET, #1
    SUB REN, RET
    JP FillCircle_Shrink

FillCircle_Done:
    POP REU
    POP RET
    POP RES
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

; =============================================================================
; TRIANGLES
; =============================================================================

; -----------------------------------------------------------------------------
; FillTri - Fill a triangle using scanline DDA edge interpolation.
;           Sorts vertices by Y, then walks two edges with fixed-point X,
;           drawing horizontal spans per scanline. Uses 8.8 fixed-point.
; -----------------------------------------------------------------------------
@REA: X1
@REB: Y1
@REC: X2
@REX: Y2
@REY: X3
@REN: Y3
@REQ: Color (0-255)
FillTri:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REO
    PUSH REP
    PUSH REQ
    PUSH RES
    PUSH RET
    PUSH REU
    PUSH REV
    PUSH REW

    ; ---- Sort vertices by Y (bubble sort) ----
    ; v0=(REA,REB), v1=(REC,REX), v2=(REY,REN)

    ; if y0 > y1: swap v0 ↔ v1
    MOV RET, REB
    SUB RET, REX
    JPZ FillTri_Sort1Done
    JPC FillTri_Sort1Done
    ; swap
    MOV RET, REA
    MOV REA, REC
    MOV REC, RET
    MOV RET, REB
    MOV REB, REX
    MOV REX, RET
FillTri_Sort1Done:

    ; if y1 > y2: swap v1 ↔ v2
    MOV RET, REX
    SUB RET, REN
    JPZ FillTri_Sort2Done
    JPC FillTri_Sort2Done
    MOV RET, REC
    MOV REC, REY
    MOV REY, RET
    MOV RET, REX
    MOV REX, REN
    MOV REN, RET
FillTri_Sort2Done:

    ; if y0 > y1: swap v0 ↔ v1 again
    MOV RET, REB
    SUB RET, REX
    JPZ FillTri_Sort3Done
    JPC FillTri_Sort3Done
    MOV RET, REA
    MOV REA, REC
    MOV REC, RET
    MOV RET, REB
    MOV REB, REX
    MOV REX, RET
FillTri_Sort3Done:

    ; Now: v0=(REA,REB)=top, v1=(REC,REX)=mid, v2=(REY,REN)=bottom
    ; y0 <= y1 <= y2

    ; Degenerate check: if y0 == y2, triangle is flat
    MOV RET, REB
    SUB RET, REN
    JPZ FillTri_Done

    ; Save sorted vertices on stack for second half
    PUSH REA               ; x_top
    PUSH REB               ; y_top
    PUSH REC               ; x_mid
    PUSH REX               ; y_mid
    PUSH REY               ; x_bot
    PUSH REN               ; y_bot
    PUSH REQ               ; color

    ; ---- Compute long edge slope: top → bottom ----
    ; step_long = ((x_bot - x_top) << 8) / (y_bot - y_top), signed
    MOV REO, REY
    SUB REO, REA              ; dx_long = x_bot - x_top  (may be neg in 2's comp)
    MOV REP, REN
    SUB REP, REB              ; dy_long = y_bot - y_top  (positive, > 0)

    ; Signed fixed-point division: (dx << 8) / dy
    ; Check sign of dx via ADD trick
    MOV RET, REO
    ADD RET, RET              ; double: bit 23 → carry
    JPC FillTri_LongNeg

    ; Positive dx
    LDI RET, #8
    SHL REO, RET
    DIV REO, REP              ; REO = step_long (positive)
    JP FillTri_LongDone

FillTri_LongNeg:
    LDI RET, #0
    SUB RET, REO              ; RET = abs(dx)
    LDI REO, #8
    SHL RET, REO
    DIV RET, REP              ; RET = abs(step)
    LDI REO, #0
    SUB REO, RET              ; REO = -step (negative 2's comp)

FillTri_LongDone:
    ; REO = step_long (8.8 fixed-point, signed)

    ; ---- Compute short edge slope: top → mid ----
    MOV RES, REC
    SUB RES, REA              ; dx_short = x_mid - x_top
    MOV REU, REX
    SUB REU, REB              ; dy_short = y_mid - y_top

    ; If dy_short == 0 (flat top), skip top half
    LDI RET, #0
    MOV REV, REU
    SUB REV, RET
    JPZ FillTri_SkipTopHalf

    MOV RET, RES
    ADD RET, RET
    JPC FillTri_ShortNeg1

    LDI RET, #8
    SHL RES, RET
    DIV RES, REU              ; RES = step_short (positive)
    JP FillTri_TopHalf

FillTri_ShortNeg1:
    LDI RET, #0
    SUB RET, RES
    LDI RES, #8
    SHL RET, RES
    DIV RET, REU
    LDI RES, #0
    SUB RES, RET

FillTri_TopHalf:
    ; ---- Render top half: from y_top to y_mid - 1 ----
    ; REO = step_long, RES = step_short
    ; x_long and x_short both start at x_top << 8
    LDI RET, #8
    MOV REU, REA
    SHL REU, RET              ; REU = x_long (fixed-point)
    MOV REV, REA
    SHL REV, RET              ; REV = x_short (fixed-point)
    MOV REW, REB              ; REW = current_y = y_top

FillTri_TopLoop:
    ; Check if current_y reached y_mid
    MOV RET, REW
    SUB RET, REX              ; current_y - y_mid
    JPZ FillTri_SkipTopHalf   ; reached mid vertex

    ; Compute integer x from both edges
    PUSH REO                  ; save step_long
    PUSH RES                  ; save step_short

    LDI RET, #8
    MOV REA, REU
    SHR REA, RET              ; left_x = x_long >> 8
    MOV REP, REV
    SHR REP, RET              ; right_x = x_short >> 8

    ; Ensure left <= right: swap if needed
    MOV RET, REA
    SUB RET, REP
    JPZ FillTri_TopDraw
    JPC FillTri_TopDraw       ; REA < REP, correct order
    ; Swap
    MOV RET, REA
    MOV REA, REP
    MOV REP, RET

FillTri_TopDraw:
    ; Draw span: REA=x_start, REB=y, REC=color, REX=length
    MOV REB, REW              ; y = current_y
    ; Retrieve color from stack (it's deep in the stack frame)
    ; For simplicity, push and use REQ which still holds color
    POP RES
    POP REO
    POP REQ                   ; color
    PUSH REQ
    PUSH REO
    PUSH RES
    MOV REC, REQ
    SUB REP, REA, REX         ; REX = right - left
    LDI RET, #1
    ADD REX, RET              ; REX = right - left + 1 = length
    CALL DrawHLine

    POP RES
    POP REO

    ; Step both edges
    ADD REU, REO              ; x_long += step_long
    ADD REV, RES              ; x_short += step_short
    LDI RET, #1
    ADD REW, RET              ; y++

    JP FillTri_TopLoop

FillTri_SkipTopHalf:
    ; ---- Compute short edge slope: mid → bottom ----
    ; Retrieve sorted vertices from stack
    POP REQ                   ; color
    POP REN                   ; y_bot
    POP REY                   ; x_bot
    POP REX                   ; y_mid
    POP REC                   ; x_mid
    POP REB                   ; y_top
    POP REA                   ; x_top
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REQ

    ; dx_short2 = x_bot - x_mid
    MOV RES, REY
    SUB RES, REC
    ; dy_short2 = y_bot - y_mid
    MOV REU, REN
    SUB REU, REX

    ; If dy_short2 == 0 (flat bottom), skip bottom half
    LDI RET, #0
    MOV REV, REU
    SUB REV, RET
    JPZ FillTri_Done2

    MOV RET, RES
    ADD RET, RET
    JPC FillTri_ShortNeg2

    LDI RET, #8
    SHL RES, RET
    DIV RES, REU
    JP FillTri_BottomHalf

FillTri_ShortNeg2:
    LDI RET, #0
    SUB RET, RES
    LDI RES, #8
    SHL RET, RES
    DIV RET, REU
    LDI RES, #0
    SUB RES, RET

FillTri_BottomHalf:
    ; ---- Render bottom half: from y_mid to y_bot ----
    ; x_long continues from where it was (REU still valid? No, it was clobbered)
    ; Recompute x_long at y_mid:
    ;   x_long_at_mid = x_top + step_long * (y_mid - y_top) [in fixed point]
    ; This is complex. Instead, recompute from scratch:
    ;   x_long_at_mid = x_top << 8 + step_long * (y_mid - y_top)
    ;   The top-half loop already advanced REU to this position IF we ran the top half.
    ;   If we skipped the top half (flat top), we need to compute it.

    ; For simplicity: recompute x_long at y_mid position
    MOV REU, REX
    SUB REU, REB              ; dy_to_mid = y_mid - y_top
    MUL REO, REU, REU         ; REU = step_long * dy_to_mid
    LDI RET, #8
    MOV REV, REA
    SHL REV, RET              ; REV = x_top << 8
    ADD REU, REV              ; REU = x_long at y_mid (fixed-point)

    ; x_short starts at x_mid << 8
    LDI RET, #8
    MOV REV, REC
    SHL REV, RET              ; REV = x_mid << 8

    MOV REW, REX              ; REW = current_y = y_mid

FillTri_BotLoop:
    ; Check if current_y > y_bot
    MOV RET, REW
    SUB RET, REN
    JPZ FillTri_BotLast
    JPC FillTri_BotDraw
    JP FillTri_Done2

FillTri_BotLast:
    ; Draw last row and exit

FillTri_BotDraw:
    PUSH REO
    PUSH RES

    LDI RET, #8
    MOV REA, REU
    SHR REA, RET
    MOV REP, REV
    SHR REP, RET

    ; Ensure left <= right
    MOV RET, REA
    SUB RET, REP
    JPZ FillTri_BotDrawSpan
    JPC FillTri_BotDrawSpan
    MOV RET, REA
    MOV REA, REP
    MOV REP, RET

FillTri_BotDrawSpan:
    MOV REB, REW
    ; Get color from stack
    POP RES
    POP REO
    POP REQ
    PUSH REQ
    PUSH REO
    PUSH RES
    MOV REC, REQ

    SUB REP, REA, REX
    LDI RET, #1
    ADD REX, RET
    CALL DrawHLine

    POP RES
    POP REO

    ADD REU, REO
    ADD REV, RES
    LDI RET, #1
    ADD REW, RET

    ; Check if we just drew the last row (y_bot)
    MOV RET, REW
    SUB RET, REN
    JPZ FillTri_Done2
    JPC FillTri_BotLoop

FillTri_Done2:
    ; Clean up stack
    POP REQ
    POP REN
    POP REY
    POP REX
    POP REC
    POP REB
    POP REA

FillTri_Done:
    POP REW
    POP REV
    POP REU
    POP RET
    POP RES
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

; =============================================================================
; BITMAP / SPRITE RENDERING
; =============================================================================

; -----------------------------------------------------------------------------
; DrawBitmap - Draw a rectangular bitmap from a data table in memory.
;
; Data format (each entry is one 24-bit word):
;   Word 0  : Width  (pixels)
;   Word 1  : Height (pixels)
;   Word 2+ : Pixel colors in row-major order (left-to-right, top-to-bottom).
;             Value 0xFFFFFF = transparent (pixel is not drawn).
;             Values 0-255   = XTerm256 color index.
;
; Usage:
;   1. Define sprite data using DW directives with a label:
;        MySpriteData:
;            DW 3, 2            ; 3 wide, 2 tall
;            DW #0x0F, #0x0C, #0x0F
;            DW #0x0C, #0x0F, #0x0C
;
;   2. Call DrawBitmap:
;        LDI REA, #10          ; X=10
;        LDI REB, #20          ; Y=20
;        LDI REC, MySpriteData ; pointer to data
;        CALL Video.DrawBitmap
;
;   3. For external images: use INCBIN "file.bin" to include a binary file
;      where each byte becomes one data word (color index).
;      Prepend width and height with DW, then INCBIN the pixel data.
;
; Performance: ~13 instructions per visible pixel, ~8 per transparent pixel.
; A 20x20 sprite (400 px) renders in ~0.3-0.4 seconds at 1.2 kHz.
; -----------------------------------------------------------------------------
@REA: X position (top-left corner)
@REB: Y position (top-left corner)
@REC: Address of sprite data (pointer to [width, height, pixels...])
DrawBitmap:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REN
    PUSH REO
    PUSH REP
    PUSH REQ
    PUSH RER
    PUSH RES
    PUSH RET
    PUSH REU
    PUSH REV
    PUSH REW
    PUSH REX
    PUSH REY

    ; Load constants
    LDI REQ, #1
    LDI RES, #12
    LDI REV, $VideoDisplay.Start
    LDI REW, #64

    ; Build packed position = (y << 6) | x
    LDI REN, #6
    MOV REU, REB
    SHL REU, REN
    ADD REU, REA

    ; Read width from data
    LDI RER, [REC]
    ADD REC, REQ

    ; Read height from data
    LDI REP, [REC]
    ADD REC, REQ

DrawBitmapRowLoop:
    MOV REO, RER

DrawBitmapPixelLoop:
    LDI RET, [REC]
    ADD REC, REQ

    ; Check transparency (color == 0xFFFFFF means skip)
    LDI REX, #0xFFFFFF
    MOV REY, RET
    SUB REY, REX
    JPZ DrawBitmapSkip

    ; Pack: (color << 12) | position
    MOV REY, RET
    SHL REY, RES
    ADD REY, REU
    STR [REV], REY

DrawBitmapSkip:
    ADD REU, REQ
    SUB REO, REQ
    JPZ DrawBitmapNextRow
    JP DrawBitmapPixelLoop

DrawBitmapNextRow:
    ; Move to next row: subtract width (already consumed), add 64
    SUB REU, RER
    ADD REU, REW
    SUB REP, REQ
    JPZ DrawBitmapDone
    JP DrawBitmapRowLoop

DrawBitmapDone:
    POP REY
    POP REX
    POP REW
    POP REV
    POP REU
    POP RET
    POP RES
    POP RER
    POP REQ
    POP REP
    POP REO
    POP REN
    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DrawBitmapMono - Draw a monochrome bitmap from packed bitmask data.
;
; Data format (each entry is one 24-bit word):
;   Word 0  : Width  (pixels, max 24)
;   Word 1  : Height (pixels)
;   Word 2+ : One bitmask word per row.
;             Bit 23 = leftmost pixel, bit 22 = second pixel, etc.
;             Bit set = draw pixel in given color. Bit clear = transparent.
;
; Rendering: uses ADD-to-self to shift the bitmask left one bit; the carry
; flag captures bit 23 (the MSB). Each drawn pixel is a single STR with a
; pre-computed packed-pixel word, no CALL overhead.
;
; Usage:
;        LDI REA, #10            ; X
;        LDI REB, #20            ; Y
;        LDI REC, #0x0F          ; color
;        LDI REX, MySprite       ; pointer to [width, height, rows...]
;        CALL Video.DrawBitmapMono
; -----------------------------------------------------------------------------
@REA: X position (top-left corner)
@REB: Y position (top-left corner)
@REC: Color for "on" pixels (0-255)
@REX: Address of sprite data (pointer to [width, height, bitmask_rows...])
DrawBitmapMono:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY
    PUSH REN
    PUSH REO
    PUSH REP
    PUSH REQ
    PUSH RER
    PUSH RET
    PUSH REU
    PUSH REV
    PUSH REW

    ; Constants
    LDI REQ, #1
    LDI REV, $VideoDisplay.Start
    LDI REW, #64

    ; Pre-compute color << 12
    LDI RET, #12
    SHL REC, RET
    MOV RET, REC              ; RET = color << 12

    ; Build start position = (y << 6) | x
    LDI REC, #6
    MOV REU, REB
    SHL REU, REC
    ADD REU, REA              ; REU = (y << 6) | x

    ; Read header from data
    LDI REN, [REX]            ; REN = width
    ADD REX, REQ
    LDI REP, [REX]            ; REP = height
    ADD REX, REQ

DrawBitmapMonoRowLoop:
    LDI REO, [REX]            ; REO = row bitmask
    ADD REX, REQ
    MOV RER, REN              ; RER = column counter
    ; Compute packed pixel for start of this row
    MOV REY, RET              ; REY = color << 12
    ADD REY, REU              ; REY = packed pixel at (x, current_y)

DrawBitmapMonoPixelLoop:
    ; Shift bitmask left by 1: bit 23 goes into carry flag
    ADD REO, REO
    JPC DrawBitmapMonoDraw
    JP DrawBitmapMonoAfterDraw

DrawBitmapMonoDraw:
    ; Bit was set → draw pixel (single STR, no CALL)
    STR [REV], REY

DrawBitmapMonoAfterDraw:
    ADD REY, REQ              ; Advance packed pixel (+1 = next X)
    SUB RER, REQ              ; Column counter--
    JPZ DrawBitmapMonoNextRow
    JP DrawBitmapMonoPixelLoop

DrawBitmapMonoNextRow:
    ADD REU, REW              ; Advance row position by 64 (next Y, same X)
    SUB REP, REQ              ; Height counter--
    JPZ DrawBitmapMonoDone
    JP DrawBitmapMonoRowLoop

DrawBitmapMonoDone:
    POP REW
    POP REV
    POP REU
    POP RET
    POP RER
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

; =============================================================================
; APPLICATION-SPECIFIC
; =============================================================================

; -----------------------------------------------------------------------------
; DrawBootLogo - Draw the DosB OS boot logo on a 64x64 display.
; Shows a colored border with a large "D" letter rendered from sprite data.
; -----------------------------------------------------------------------------
DrawBootLogo:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX

    ; Draw green border (1 pixel inset from edge)
    LDI REC, #0x0A

    LDI REA, #1
    LDI REB, #1
    LDI REX, #62
    CALL DrawHLine

    LDI REA, #1
    LDI REB, #62
    LDI REX, #62
    CALL DrawHLine

    LDI REA, #1
    LDI REB, #1
    LDI REX, #62
    CALL DrawVLine

    LDI REA, #62
    LDI REB, #1
    LDI REX, #62
    CALL DrawVLine

    ; Draw "D" letter from sprite data (centered)
    LDI REA, #25
    LDI REB, #21
    LDI REC, #0x0F
    LDI REX, DLetterSprite
    CALL DrawBitmapMono

    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DrawMenu - Draw the key-option menu at the bottom of the screen.
;   1 (cyan)   = Color demo
;   2 (blue)   = Animation
;   3 (gray)   = Clear screen
;   4 (green)  = Boot logo
;   5 (yellow) = Show image
;   0 (red)    = Shutdown
; Placed at y=55..59 inside the border.
; All digit shapes are loaded from sprite data.
; -----------------------------------------------------------------------------
DrawMenu:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX

    ; Separator line
    LDI REC, #0x08
    LDI REA, #4
    LDI REB, #53
    LDI REX, #56
    CALL DrawHLine

    ; "1" at x=4, y=55 in cyan
    LDI REA, #4
    LDI REB, #55
    LDI REC, #0x0B
    LDI REX, Digit1Sprite
    CALL DrawBitmapMono

    ; "2" at x=14, y=55 in blue
    LDI REA, #14
    LDI REB, #55
    LDI REC, #0x09
    LDI REX, Digit2Sprite
    CALL DrawBitmapMono

    ; "3" at x=24, y=55 in gray
    LDI REA, #24
    LDI REB, #55
    LDI REC, #0x07
    LDI REX, Digit3Sprite
    CALL DrawBitmapMono

    ; "4" at x=34, y=55 in green
    LDI REA, #34
    LDI REB, #55
    LDI REC, #0x0A
    LDI REX, Digit4Sprite
    CALL DrawBitmapMono

    ; "5" at x=44, y=55 in yellow
    LDI REA, #44
    LDI REB, #55
    LDI REC, #0x0E
    LDI REX, Digit5Sprite
    CALL DrawBitmapMono

    ; "0" at x=54, y=55 in red
    LDI REA, #54
    LDI REB, #55
    LDI REC, #0x0C
    LDI REX, Digit0Sprite
    CALL DrawBitmapMono

    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; =============================================================================
; SPRITE DATA
; =============================================================================
; Sprite data tables used by DrawBitmapMono.
; Format: [width] [height] [bitmask_row_0] [bitmask_row_1] ...
; Each bitmask word: bit 23 = leftmost pixel, bit set = draw.
;
; To create new sprites:
;   - Define a label and use DW directives
;   - Use the ImageConverter tool to generate from PNG files
;   - Or use INCBIN to include pre-built binary sprite data
; =============================================================================

; "D" letter for boot logo (14 pixels wide, 21 pixels tall)
; 1px stroke width for a clean, thin look.
DLetterSprite:
    DW #14, #21
    DW #0xFF8000         ; Row 0:  #########.....
    DW #0x804000         ; Row 1:  #........#....
    DW #0x802000         ; Row 2:  #.........#...
    DW #0x801000         ; Row 3:  #..........#..
    DW #0x800800         ; Row 4:  #...........#.
    DW #0x800400         ; Row 5:  #............#
    DW #0x800400         ; Row 6:  #............#
    DW #0x800400         ; Row 7:  #............#
    DW #0x800400         ; Row 8:  #............#
    DW #0x800400         ; Row 9:  #............#
    DW #0x800400         ; Row 10: #............#
    DW #0x800400         ; Row 11: #............#
    DW #0x800400         ; Row 12: #............#
    DW #0x800400         ; Row 13: #............#
    DW #0x800400         ; Row 14: #............#
    DW #0x800800         ; Row 15: #...........#.
    DW #0x801000         ; Row 16: #..........#..
    DW #0x802000         ; Row 17: #.........#...
    DW #0x804000         ; Row 18: #........#....
    DW #0xFF8000         ; Row 19: #########.....
    DW #0xFF8000         ; Row 20: #########.....

; Digit "1" for menu (5 wide, 7 tall)
Digit1Sprite:
    DW #5, #7
    DW #0x200000         ; ..#..
    DW #0x600000         ; .##..
    DW #0x200000         ; ..#..
    DW #0x200000         ; ..#..
    DW #0x200000         ; ..#..
    DW #0x200000         ; ..#..
    DW #0x700000         ; .###.

; Digit "2" for menu (5 wide, 7 tall)
Digit2Sprite:
    DW #5, #7
    DW #0x700000         ; .###.
    DW #0x880000         ; #...#
    DW #0x080000         ; ....#
    DW #0x300000         ; ..##.
    DW #0x400000         ; .#...
    DW #0x800000         ; #....
    DW #0xF80000         ; #####

; Digit "3" for menu (5 wide, 7 tall)
Digit3Sprite:
    DW #5, #7
    DW #0x700000         ; .###.
    DW #0x880000         ; #...#
    DW #0x080000         ; ....#
    DW #0x300000         ; ..##.
    DW #0x080000         ; ....#
    DW #0x880000         ; #...#
    DW #0x700000         ; .###.

; Digit "4" for menu (5 wide, 7 tall)
Digit4Sprite:
    DW #5, #7
    DW #0x900000         ; #..#.
    DW #0x900000         ; #..#.
    DW #0x900000         ; #..#.
    DW #0xF80000         ; #####
    DW #0x100000         ; ...#.
    DW #0x100000         ; ...#.
    DW #0x100000         ; ...#.

; Digit "5" for menu (5 wide, 7 tall)
Digit5Sprite:
    DW #5, #7
    DW #0xF80000         ; #####
    DW #0x800000         ; #....
    DW #0xF00000         ; ####.
    DW #0x080000         ; ....#
    DW #0x080000         ; ....#
    DW #0x880000         ; #...#
    DW #0x700000         ; .###.

; Digit "0" for menu (5 wide, 7 tall)
Digit0Sprite:
    DW #5, #7
    DW #0x700000         ; .###.
    DW #0x880000         ; #...#
    DW #0x880000         ; #...#
    DW #0x880000         ; #...#
    DW #0x880000         ; #...#
    DW #0x880000         ; #...#
    DW #0x700000         ; .###.
