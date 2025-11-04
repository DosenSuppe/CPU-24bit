from Values.Microcode import *
from Values.Registers import *

class MicroInstructions:
    LOAD_PC_AS_RAM_ADDRESS = RAM_READ | PC_ADDRESS_OUT
    READ_RAM = RAM_READ
    
    
    