.Code
LDI REB, #0xff

ReadInput:
    MOV EP0, EP1

    MOV REA, EP0   
    JPZ End
    JP ReadInput

End:
    HALT
