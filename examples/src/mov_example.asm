.Code
LDI REA, #0x1
LDI REB, #0x2

MOV REX, REA        ; Move REA to REX
MOV REY, REB        ; Move REB to REY

ADD REX, REA        ; Add REA to REX, store in REX
ADD REY, REB, REZ   ; Add REB to REY, store in REZ

HALT 
