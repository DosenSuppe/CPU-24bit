from Microcode import *

class MicroInstructions:
    LOAD_PC_AS_RAM_ADDRESS = RAM_ADDRESS_LOAD | ENABLE_SOURCE_REGISTER | GenerateDestinationRegister(Register.PC)
    READ_RAM = ENABLE_RAM_OUTPUT | RAM_READ
    LOAD_ADDRESS_FROM_RAM = READ_RAM | RAM_ADDRESS_LOAD | ENABLE_PC
    
    STORE_ACC = REGISTER_STORE | GenerateDestinationRegister(Register.ACC) | SET_AS_DESTINATION_ADDRESS
    
    