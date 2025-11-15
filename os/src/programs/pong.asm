.Code

; Address #0x1FF01 = input from buttons
; Address #0x1FF02 = current slider position
; Address #0xE00000 = slider render position (Display)

Main:
    ; setting slider default position
    LDI REA, #7
    LDI REC, #0x1FF02
    STR [REC], REA

    JP RenderLoop
    
RenderLoop:
    CALL RenderFrame
    JP RenderLoop

RenderFrame:
    
    CALL UpdateSlider
    CALL RenderSlider
    
    RTS

RenderSlider:
    PUSH REA
    PUSH REC 
    PUSH REX 

    LDI REX, #0x1FF02
    LDI REA, [REX] ; load current slider position
    LDI REC, #0xE00000  ; address to render slider
    STR [REC], REA
    
    POP REX
    POP REC
    POP REA
    RTS

UpdateSlider:
    PUSH REA
    PUSH REB
    PUSH REC 

    LDI REB, #1
    LDI REC, #0x1FF01 ; address of left slider state (1 = up, 2 = down, 0 = none)
    LDI REA, [REC]    ; load current button state

    SUB REA, REB    ; checking for up-button pressed
    JPZ SliderUp    

    SUB REA, REB    ; checking for down-button pressed
    JPZ SliderDown

    _UpdateFinished:

    LDI REB, #0      ; no button pressed
    STR [REC], REB   ; clear button state
    
    POP REC
    POP REB
    POP REA
    RTS

    SliderUp:
        PUSH REC
        LDI REC, #0x1FF02
        LDI REA, [REC] ; load current slider position
        LDI REB, #1
        SHL REA, REB         ; move slider up 

        STR [REC], REA ; save new slider position
        POP REC
        JP _UpdateFinished

    SliderDown:
        PUSH REC
        LDI REC, #0x1FF02
        LDI REA, [REC] ; load current slider position
        LDI REB, #1
        SHR REA, REB         ; move slider down 

        STR [REC], REA ; save new slider position
        POP REC
        JP _UpdateFinished
