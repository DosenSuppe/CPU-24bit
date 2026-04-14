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

; -----------------------------------------------------------------------------
; RayTrace - Render a ray-traced sphere scene on the 64x64 display.
;
; Scene:
;   - Shaded sphere centered at (32, 26), radius 18
;   - Specular highlight near top-left (26, 18)
;   - Sky gradient background (blue tones)
;   - Checkerboard ground plane (bottom half)
;   - Soft shadow below sphere
;
; Uses integer math only: |dx|, |dy|, MUL for dist_sq, threshold shading.
; -----------------------------------------------------------------------------
RayTrace:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REQ
    PUSH RER
    PUSH REX
    PUSH REY
    PUSH REN

    CALL Video.ClearScreen

    LDI REY, #0               ; y = 0

RayOuterLoop:
    LDI REX, #0               ; x = 0

RayInnerLoop:
    ; =====================================================
    ; Compute dx = |x - 32| → REQ
    ; =====================================================
    MOV REA, REX
    LDI REB, #32
    SUB REA, REB               ; x - 32: carry if x < 32
    JPC RayXLess
    MOV REQ, REA               ; dx = x - 32
    JP RayGotDx
RayXLess:
    LDI REQ, #32
    SUB REQ, REX               ; dx = 32 - x
RayGotDx:

    ; =====================================================
    ; Compute dy = |y - 26| → RER
    ; =====================================================
    MOV REA, REY
    LDI REB, #26
    SUB REA, REB               ; y - 26: carry if y < 26
    JPC RayYLess
    MOV RER, REA               ; dy = y - 26
    JP RayGotDy
RayYLess:
    LDI RER, #26
    SUB RER, REY               ; dy = 26 - y
RayGotDy:

    ; =====================================================
    ; dist_sq = dx*dx + dy*dy → REA
    ; =====================================================
    MOV REA, REQ
    MUL REA, REQ               ; dx*dx
    MOV REB, RER
    MUL REB, RER               ; dy*dy
    ADD REA, REB               ; dist_sq = dx^2 + dy^2

    ; Check if inside sphere: dist_sq <= 324 (18*18)
    MOV REB, REA               ; save dist_sq in REB
    LDI REA, #324
    SUB REA, REB               ; 324 - dist_sq: carry if dist_sq > 324
    JPC RayBackground

    ; =====================================================
    ; INSIDE SPHERE — compute highlight shading
    ; Highlight center at (26, 18) → lx = |x-26|, ly = |y-18|
    ; =====================================================

    ; |x - 26| → REQ
    MOV REA, REX
    LDI REB, #26
    SUB REA, REB
    JPC RayLxLess
    MOV REQ, REA
    JP RayGotLx
RayLxLess:
    LDI REQ, #26
    SUB REQ, REX
RayGotLx:

    ; |y - 18| → RER
    MOV REA, REY
    LDI REB, #18
    SUB REA, REB
    JPC RayLyLess
    MOV RER, REA
    JP RayGotLy
RayLyLess:
    LDI RER, #18
    SUB RER, REY
RayGotLy:

    ; light_dist = lx*lx + ly*ly → REB
    MOV REA, REQ
    MUL REA, REQ
    MOV REB, RER
    MUL REB, RER
    ADD REB, REA               ; REB = light_dist_sq

    ; --- Shading bands based on distance from highlight ---
    ;   < 16  → White (0x0F) specular highlight
    ;   < 50  → Cyan (0x0B) bright
    ;   < 120 → Dark Cyan (0x03) mid
    ;   < 220 → Blue (0x09) dim
    ;   else  → Dark Blue (0x01) edge
    LDI REA, #16
    SUB REA, REB               ; 16 - light_dist
    JPC RayShade1
    LDI REC, #0x0F             ; white highlight
    JP RayDrawSphere

RayShade1:
    LDI REA, #50
    SUB REA, REB
    JPC RayShade2
    LDI REC, #0x0B             ; cyan
    JP RayDrawSphere

RayShade2:
    LDI REA, #120
    SUB REA, REB
    JPC RayShade3
    LDI REC, #0x03             ; dark cyan
    JP RayDrawSphere

RayShade3:
    LDI REA, #220
    SUB REA, REB
    JPC RayShade4
    LDI REC, #0x09             ; blue
    JP RayDrawSphere

RayShade4:
    LDI REC, #0x01             ; dark blue (edge)

RayDrawSphere:
    MOV REA, REX
    MOV REB, REY
    CALL Video.WritePixel
    JP RayNextPixel

    ; =====================================================
    ; OUTSIDE SPHERE — background
    ; =====================================================
RayBackground:

    ; --- Check for shadow zone (oval below sphere) ---
    ; y in [46..50], x in [25..39]
    MOV REA, REY
    LDI REB, #46
    SUB REA, REB               ; y - 46: carry if y < 46
    JPC RayNoShadow
    LDI REA, #51
    SUB REA, REY               ; 51 - y: carry if y > 50
    JPC RayNoShadow
    MOV REA, REX
    LDI REB, #25
    SUB REA, REB               ; x - 25: carry if x < 25
    JPC RayNoShadow
    LDI REA, #40
    SUB REA, REX               ; 40 - x: carry if x > 39
    JPC RayNoShadow
    ; In shadow
    LDI REC, #0x08             ; dark gray
    JP RayDrawBg

RayNoShadow:
    ; --- Sky or ground? Split at y=38 (horizon) ---
    MOV REA, REY
    LDI REB, #38
    SUB REA, REB               ; y - 38: carry if y < 38
    JPC RaySky

    ; --- Ground: checkerboard pattern ---
    ; checker = ((x >> 2) + (y >> 2)) & 1
    MOV REA, REX
    LDI REB, #2
    SHR REA, REB               ; x >> 2
    MOV REC, REY
    SHR REC, REB               ; y >> 2
    ADD REA, REC
    LDI REB, #1
    AND REA, REB               ; (x/4 + y/4) & 1
    JPZ RayGroundDark
    LDI REC, #0x06             ; brown tile
    JP RayDrawBg
RayGroundDark:
    LDI REC, #0x02             ; dark green tile
    JP RayDrawBg

    ; --- Sky gradient ---
RaySky:
    MOV REA, REY
    LDI REB, #12
    SUB REA, REB               ; y - 12: carry if y < 12
    JPC RaySkyBright
    MOV REA, REY
    LDI REB, #25
    SUB REA, REB               ; y - 25: carry if y < 25
    JPC RaySkyMid
    ; low sky (y 25-37)
    LDI REC, #0x01             ; dark blue
    JP RayDrawBg
RaySkyBright:
    ; top sky (y 0-11)
    LDI REC, #0x09             ; blue
    JP RayDrawBg
RaySkyMid:
    ; mid sky (y 12-24)
    LDI REC, #0x03             ; dark cyan
    JP RayDrawBg

RayDrawBg:
    MOV REA, REX
    MOV REB, REY
    CALL Video.WritePixel

    ; =====================================================
    ; Advance to next pixel
    ; =====================================================
RayNextPixel:
    LDI REN, #1
    ADD REX, REN
    MOV REA, REX
    LDI REN, #64
    SUB REA, REN
    JPZ RayNextRow
    JP RayInnerLoop

RayNextRow:
    LDI REN, #1
    ADD REY, REN
    MOV REA, REY
    LDI REN, #64
    SUB REA, REN
    JPZ RayDone
    JP RayOuterLoop

RayDone:
    POP REN
    POP REY
    POP REX
    POP RER
    POP REQ
    POP REC
    POP REB
    POP REA
    RTS
