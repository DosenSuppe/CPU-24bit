; =============================================================================
; Video Display Driver
; =============================================================================
; Driver for the 64x64 pixel video display with 16 colors.
; Hardware address: $VideoDisplay.Start
;
; Pixel write format (packed into one word):
;   Bits 0-5  : X coordinate (0-63)
;   Bits 6-11 : Y coordinate (0-63)
;   Bits 12-15: Color (XTerm16, 0-15)
;
; XTerm16 color palette:
;   0x0 = Black     0x4 = Dark Red    0x8 = Dark Gray    0xC = Light Red
;   0x1 = Dark Blue 0x5 = Purple      0x9 = Blue         0xD = Magenta
;   0x2 = Dark Green 0x6 = Brown      0xA = Green        0xE = Yellow
;   0x3 = Dark Cyan 0x7 = Light Gray  0xB = Cyan         0xF = White
; =============================================================================

.VideoDriver

; -----------------------------------------------------------------------------
; WritePixel - Draw a single pixel on the video display.
; @REA: X coordinate (0-63)
; @REB: Y coordinate (0-63)
; @REC: Color (0-15)
; -----------------------------------------------------------------------------
WritePixel:
    PUSH REN
    PUSH REX

    LDI REN, #6

    MOV REX, REC               ; start with color         (0000 0000 0000 0000 0000 CCCC)
    SHL REX, REN               ; shift left by 6          (0000 0000 0000 00CC CC00 0000)
    ADD REX, REB               ; add Y coordinate         (0000 0000 0000 00CC CCYY YYYY)
    SHL REX, REN               ; shift left by 6          (0000 CCCC YYYY YY00 0000)
    ADD REX, REA               ; add X coordinate         (0000 CCCC YYYY YYXX XXXX)

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
; @REA: Color (0-15)
; -----------------------------------------------------------------------------
FillScreen:
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY

    LDI REX, #0               ; x counter
    LDI REY, #0               ; y counter
    MOV REC, REA               ; color

FillScreenLoopY:
    LDI REX, #0               ; reset x for each row

FillScreenLoopX:
    MOV REA, REX
    MOV REB, REY
    CALL WritePixel            ; draw pixel at (REX, REY) with color REC

    ; increment x
    PUSH REN
    LDI REN, #1
    ADD REX, REN

    ; check if x reached 64
    MOV REA, REX
    LDI REN, #64
    SUB REA, REN
    POP REN
    JPZ FillScreenNextRow

    JP FillScreenLoopX

FillScreenNextRow:
    ; increment y
    PUSH REN
    LDI REN, #1
    ADD REY, REN

    ; check if y reached 64
    MOV REA, REY
    LDI REN, #64
    SUB REA, REN
    POP REN
    JPZ FillScreenDone

    JP FillScreenLoopY

FillScreenDone:
    POP REY
    POP REX
    POP REC
    POP REB
    RTS

; -----------------------------------------------------------------------------
; DrawHLine - Draw a horizontal line.
; @REA: X start (0-15)
; @REB: Y position (0-15)
; @REC: Color (0-15)
; @REX: Length (pixels)
; -----------------------------------------------------------------------------
DrawHLine:
    PUSH REA
    PUSH REX
    PUSH REN

    LDI REN, #1

DrawHLineLoop:
    CALL WritePixel            ; draw pixel at current position
    SUB REX, REN               ; length--
    JPZ DrawHLineDone           ; if length reached 0, done
    ADD REA, REN               ; x++
    JP DrawHLineLoop

DrawHLineDone:
    POP REN
    POP REX
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DrawVLine - Draw a vertical line.
; @REA: X position (0-15)
; @REB: Y start (0-15)
; @REC: Color (0-15)
; @REX: Length (pixels)
; -----------------------------------------------------------------------------
DrawVLine:
    PUSH REB
    PUSH REX
    PUSH REN

    LDI REN, #1

DrawVLineLoop:
    CALL WritePixel            ; draw pixel at current position
    SUB REX, REN               ; length--
    JPZ DrawVLineDone           ; if length reached 0, done
    ADD REB, REN               ; y++
    JP DrawVLineLoop

DrawVLineDone:
    POP REN
    POP REX
    POP REB
    RTS

; -----------------------------------------------------------------------------
; DrawBox - Draw a rectangle outline.
; @REA: X start
; @REB: Y start
; @REC: Color
; @REX: Width
; @REY: Height
; -----------------------------------------------------------------------------
DrawBox:
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY
    PUSH REN

    ; Save original params
    PUSH REA                   ; save X
    PUSH REB                   ; save Y
    PUSH REX                   ; save Width
    PUSH REY                   ; save Height

    ; Top horizontal line
    POP REY                    ; height (not needed yet)
    PUSH REY
    POP REX                    ; pop into scratch, then get Width
    POP REX                    ; Width
    PUSH REX
    POP REB                    ; Y
    PUSH REB
    POP REA                    ; X
    PUSH REA

    ; Simpler approach: draw 4 lines using current params
    ; Top line: draw from (X, Y) length = Width
    POP REA                    ; restore X
    POP REB                    ; restore Y
    POP REX                    ; restore Width
    POP REY                    ; restore Height

    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY

    CALL DrawHLine             ; top edge

    ; Bottom line
    POP REY
    POP REX
    POP REB
    POP REA
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY

    ; Move Y to bottom: Y + Height - 1
    LDI REN, #1
    ADD REB, REY
    SUB REB, REN
    CALL DrawHLine             ; bottom edge

    ; Left vertical line
    POP REY
    POP REX
    POP REB
    POP REA
    PUSH REA
    PUSH REB
    PUSH REX
    PUSH REY

    MOV REX, REY              ; length = height
    CALL DrawVLine             ; left edge

    ; Right vertical line
    POP REY
    POP REX
    POP REB
    POP REA

    LDI REN, #1
    ADD REA, REX
    SUB REA, REN               ; X = X + Width - 1
    MOV REX, REY              ; length = height
    CALL DrawVLine             ; right edge

    POP REN
    POP REY
    POP REX
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DrawBootLogo - Draw the DosB OS boot logo on a 64x64 display.
; Shows a colored border with a large "D" letter in the center.
; -----------------------------------------------------------------------------
DrawBootLogo:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX
    PUSH REY

    ; Draw green border (1 pixel inset from edge)
    LDI REC, #0x0A            ; green color

    ; Top border line
    LDI REA, #1
    LDI REB, #1
    LDI REX, #62
    CALL DrawHLine

    ; Bottom border line
    LDI REA, #1
    LDI REB, #62
    LDI REX, #62
    CALL DrawHLine

    ; Left border line
    LDI REA, #1
    LDI REB, #1
    LDI REX, #62
    CALL DrawVLine

    ; Right border line
    LDI REA, #62
    LDI REB, #1
    LDI REX, #62
    CALL DrawVLine

    ; Draw "D" letter shape in white
    LDI REC, #0x0F            ; white

    ; Vertical bar of D (left side): x=18, y=14 to y=49 (length 36)
    LDI REA, #18
    LDI REB, #14
    LDI REX, #36
    CALL DrawVLine

    ; Make the bar 2 pixels wide: x=19
    LDI REA, #19
    LDI REB, #14
    LDI REX, #36
    CALL DrawVLine

    ; Top horizontal of D: x=20 to x=34, y=14 (length 15)
    LDI REA, #20
    LDI REB, #14
    LDI REX, #15
    CALL DrawHLine

    ; Top horizontal 2px thick: y=15
    LDI REA, #20
    LDI REB, #15
    LDI REX, #15
    CALL DrawHLine

    ; Bottom horizontal of D: x=20 to x=34, y=49 (length 15)
    LDI REA, #20
    LDI REB, #49
    LDI REX, #15
    CALL DrawHLine

    ; Bottom horizontal 2px thick: y=48
    LDI REA, #20
    LDI REB, #48
    LDI REX, #15
    CALL DrawHLine

    ; Top-right curve: diagonal from (35,16) down to (37,18)
    LDI REA, #35
    LDI REB, #16
    CALL WritePixel
    LDI REA, #35
    LDI REB, #17
    CALL WritePixel
    LDI REA, #36
    LDI REB, #16
    CALL WritePixel
    LDI REA, #36
    LDI REB, #17
    CALL WritePixel
    LDI REA, #36
    LDI REB, #18
    CALL WritePixel
    LDI REA, #37
    LDI REB, #18
    CALL WritePixel
    LDI REA, #37
    LDI REB, #19
    CALL WritePixel
    LDI REA, #38
    LDI REB, #19
    CALL WritePixel
    LDI REA, #38
    LDI REB, #20
    CALL WritePixel
    LDI REA, #39
    LDI REB, #20
    CALL WritePixel
    LDI REA, #39
    LDI REB, #21
    CALL WritePixel

    ; Right straight section: x=40, y=22 to y=41 (length 20)
    LDI REA, #40
    LDI REB, #22
    LDI REX, #20
    CALL DrawVLine

    ; Right straight 2px wide: x=39
    LDI REA, #39
    LDI REB, #22
    LDI REX, #20
    CALL DrawVLine

    ; Bottom-right curve: diagonal from (39,42) up-left to (35,46)
    LDI REA, #39
    LDI REB, #42
    CALL WritePixel
    LDI REA, #39
    LDI REB, #43
    CALL WritePixel
    LDI REA, #38
    LDI REB, #43
    CALL WritePixel
    LDI REA, #38
    LDI REB, #44
    CALL WritePixel
    LDI REA, #37
    LDI REB, #44
    CALL WritePixel
    LDI REA, #37
    LDI REB, #45
    CALL WritePixel
    LDI REA, #36
    LDI REB, #45
    CALL WritePixel
    LDI REA, #36
    LDI REB, #46
    CALL WritePixel
    LDI REA, #35
    LDI REB, #46
    CALL WritePixel
    LDI REA, #35
    LDI REB, #47
    CALL WritePixel

    POP REY
    POP REX
    POP REC
    POP REB
    POP REA
    RTS

; -----------------------------------------------------------------------------
; DrawMenu - Draw the key-option menu at the bottom of the screen.
; Shows color-coded 3x5 pixel digits: 1 2 3 4 0
;   1 (cyan)   = Color demo
;   2 (blue)   = Animation
;   3 (gray)   = Clear screen
;   4 (green)  = Boot logo
;   5 (purple) = Ray trace
;   0 (red)    = Shutdown
; Placed at y=55..59 inside the border.
; -----------------------------------------------------------------------------
DrawMenu:
    PUSH REA
    PUSH REB
    PUSH REC
    PUSH REX

    ; --- Separator line above menu (dark gray) ---
    LDI REC, #0x08            ; dark gray
    LDI REA, #4
    LDI REB, #53
    LDI REX, #56
    CALL DrawHLine

    ; ===== "1" at x=4, y=55 in cyan =====
    LDI REC, #0x0B            ; cyan
    ; .#.
    LDI REA, #5
    LDI REB, #55
    CALL WritePixel
    ; ##.
    LDI REA, #4
    LDI REB, #56
    CALL WritePixel
    LDI REA, #5
    LDI REB, #56
    CALL WritePixel
    ; .#.
    LDI REA, #5
    LDI REB, #57
    CALL WritePixel
    ; .#.
    LDI REA, #5
    LDI REB, #58
    CALL WritePixel
    ; ###
    LDI REA, #4
    LDI REB, #59
    LDI REX, #3
    CALL DrawHLine

    ; ===== "2" at x=14, y=55 in blue =====
    LDI REC, #0x09            ; blue
    ; ###
    LDI REA, #14
    LDI REB, #55
    LDI REX, #3
    CALL DrawHLine
    ; ..#
    LDI REA, #16
    LDI REB, #56
    CALL WritePixel
    ; ###
    LDI REA, #14
    LDI REB, #57
    LDI REX, #3
    CALL DrawHLine
    ; #..
    LDI REA, #14
    LDI REB, #58
    CALL WritePixel
    ; ###
    LDI REA, #14
    LDI REB, #59
    LDI REX, #3
    CALL DrawHLine

    ; ===== "3" at x=24, y=55 in light gray =====
    LDI REC, #0x07            ; light gray
    ; ###
    LDI REA, #24
    LDI REB, #55
    LDI REX, #3
    CALL DrawHLine
    ; ..#
    LDI REA, #26
    LDI REB, #56
    CALL WritePixel
    ; ###
    LDI REA, #24
    LDI REB, #57
    LDI REX, #3
    CALL DrawHLine
    ; ..#
    LDI REA, #26
    LDI REB, #58
    CALL WritePixel
    ; ###
    LDI REA, #24
    LDI REB, #59
    LDI REX, #3
    CALL DrawHLine

    ; ===== "4" at x=34, y=55 in green =====
    LDI REC, #0x0A            ; green
    ; #.#
    LDI REA, #34
    LDI REB, #55
    CALL WritePixel
    LDI REA, #36
    LDI REB, #55
    CALL WritePixel
    ; #.#
    LDI REA, #34
    LDI REB, #56
    CALL WritePixel
    LDI REA, #36
    LDI REB, #56
    CALL WritePixel
    ; ###
    LDI REA, #34
    LDI REB, #57
    LDI REX, #3
    CALL DrawHLine
    ; ..#
    LDI REA, #36
    LDI REB, #58
    CALL WritePixel
    ; ..#
    LDI REA, #36
    LDI REB, #59
    CALL WritePixel

    ; ===== "5" at x=44, y=55 in purple =====
    LDI REC, #0x05            ; purple
    ; ###
    LDI REA, #44
    LDI REB, #55
    LDI REX, #3
    CALL DrawHLine
    ; #..
    LDI REA, #44
    LDI REB, #56
    CALL WritePixel
    ; ###
    LDI REA, #44
    LDI REB, #57
    LDI REX, #3
    CALL DrawHLine
    ; ..#
    LDI REA, #46
    LDI REB, #58
    CALL WritePixel
    ; ###
    LDI REA, #44
    LDI REB, #59
    LDI REX, #3
    CALL DrawHLine

    ; ===== "0" at x=54, y=55 in red =====
    LDI REC, #0x0C            ; light red
    ; ###
    LDI REA, #54
    LDI REB, #55
    LDI REX, #3
    CALL DrawHLine
    ; #.#
    LDI REA, #54
    LDI REB, #56
    CALL WritePixel
    LDI REA, #56
    LDI REB, #56
    CALL WritePixel
    ; #.#
    LDI REA, #54
    LDI REB, #57
    CALL WritePixel
    LDI REA, #56
    LDI REB, #57
    CALL WritePixel
    ; #.#
    LDI REA, #54
    LDI REB, #58
    CALL WritePixel
    LDI REA, #56
    LDI REB, #58
    CALL WritePixel
    ; ###
    LDI REA, #54
    LDI REB, #59
    LDI REX, #3
    CALL DrawHLine

    POP REX
    POP REC
    POP REB
    POP REA
    RTS
