
## Segments 
Segments are used to partition code into specific addresses of memory. <br>
Segments are defined the in `memory.cfg` file:

memory.cfg:
<pre>
.Code : Start = 0x0, Size = 0xFF
.ResetVector : Start = 0x100, Size = 0xFF
</pre>

The shown config file defines two segments, called ".Code" and ".ResetVector". <br>
The .Code segement starts at memory address 0x0 and is 0xFF Words long. <br>
The .ResetVector segment starts at memory address 0x100 and is also 0xFF words long.

These segments can be used within assembly files as such:
<pre>
.Code           ; Code below will be placed in the .Code segment
LDI REA, #0x10  

LDI REB, ResetVector ; this will load the start address of the .ResetVector segement into REB

.ResetVector    
HALT            ; Halt is placed in the ResetVector 
</pre>
