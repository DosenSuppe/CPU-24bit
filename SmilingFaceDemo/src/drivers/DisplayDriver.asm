.DisplayDriver

RenderFrame:
    PUSH REX
    PUSH REA
    PUSH REY
    PUSH REQ
    PUSH REB

    LDI REY, #1                 ; used for counting offset
    LDI REQ, $FrameBuffer.Size  ; end of display memory

    LDI REX, $DisplayStart.Start
    LDI REA, $FrameBuffer.Start

    DisplayRenderLoop:
        LDI REB, [REA]  ; loading buffer column
        STR [REX], REB  ; writing it to the display

        ADD REX, REY    ; incrementing display address
        ADD REA, REY    ; incrementing frame buffer address

        SUB REQ, REY    ; checking if the end has been reached
        ; TODO: CMP REQ == REY, <isTrue>[, <isFalse>]
        JPC DisplayEnd
        JP DisplayRenderLoop

    DisplayEnd:
    
    POP REB
    POP REQ
    POP REY
    POP REA
    POP REX
    RTS

@REA: Displayed bit-map value
@REB: Column offset
DrawColumn:
    PUSH REX
    PUSH REY

    LDI REX, $FrameBuffer.Start
    ADD REX, REB    ; apply frame offset

    LDI REY, [REX]  ; current column data

    OR REY, REA     ; update column

    STR [REX], REY
    
    POP REY
    POP REX
    RTS

@REA: Displayed bit-map value
@REB: Column offset
OverrideColumn:
    PUSH REX

    LDI REX, $FrameBuffer.Start
    ADD REX, REB   ; apply frame offset

    STR [REX], REA ; override column

    POP REX
    RTS

@REA: bit-map value to clear
@REB: Column offset
RemoveFromColumn:
    PUSH REX
    PUSH REY

    LDI REX, $FrameBuffer.Start
    ADD REX, REB    ; apply frame offset

    LDI REY, [REX]  ; current column data
    SUB REY, REA    ; remove bits from column

    STR [REX], REY

    POP REY
    POP REX
    RTS

@REB: Column index
ClearBufferColumn:
    PUSH REX
    PUSH REY

    LDI REX, $FrameBuffer.Start
    ADD REX, REB 

    LDI REY, #0
    STR [REX], REY

    POP REY
    POP REX
    RTS

@REB: Column index
ClearScreenColumn:
    PUSH REX
    PUSH REY

    LDI REX, $DisplayStart.Start
    ADD REX, REB 

    LDI REY, #0
    STR [REX], REY

    POP REY
    POP REX
    RTS

ClearBuffer:
    PUSH REB
    PUSH REZ

    LDI REB, $FrameBuffer.Size
    LDI REZ, #1

    BufferClearingLoop:
        CALL ClearBufferColumn

        SUB REB, REZ
        JPC BufferClearingLoopEnd
        JP BufferClearingLoop
    
    BufferClearingLoopEnd:
    
    POP REZ
    POP REB 
    RTS

ClearScreen:
    PUSH REB
    PUSH REZ

    LDI REB, $DisplayStart.Size
    LDI REZ, #1

    ScreenClearingLoop:
        CALL ClearScreenColumn

        SUB REB, REZ
        JPC ScreenClearingLoopEnd
        JP ScreenClearingLoop
    
    ScreenClearingLoopEnd:
    
    POP REZ
    POP REB 
    RTS
