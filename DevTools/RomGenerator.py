import sys
import SaveRom as SaveRom

from pprint import pprint

from Values.Microcode import *
from Values.Registers import *

from Values.MicroInstructions import MicroInstructions as MI
from Values.OperationsALU import ALU

FETCH = [
    MI.LOAD_PC_AS_RAM_ADDRESS, 
    MI.READ_RAM | ENABLE_PC | INSTRUCTION_LOAD
]

INSTRUCTION_END = [INSTRUCTION_READ]

def generateInstruction(pInstruction: list[int] = []):
    return FETCH + [instruction for instruction in pInstruction] + INSTRUCTION_END

# shared across multiple jump instructions:
JUMP_INSTRUCTION = generateInstruction([
    MI.LOAD_PC_AS_RAM_ADDRESS,
    GenerateRegister(Register.PC) | SET_AS_DESTINATION_ADDRESS | REGISTER_STORE | MI.READ_RAM
])

JUMP_ADDR_INSTRUCTION = generateInstruction([
    ENABLE_SOURCE_REGISTER | REGISTER_LOAD
])


instruction_set = [
    {   
        'name': 'nop', 'op_code': 0x00,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]}, 
        'steps': generateInstruction()
    },
    {
        'name': 'halt', 'op_code': 0x01,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]}, 
        'steps': generateInstruction([HALT])
    },
    
    # data movement instructions
    {
        'name': 'mov', 'op_code': 0x02, # moving between registers
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([ENABLE_SOURCE_REGISTER | REGISTER_STORE])
    },
    
    {
        'name': 'ldi', 'op_code': 0x03, # loading immediate to register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            MI.LOAD_PC_AS_RAM_ADDRESS, 
            MI.READ_RAM | REGISTER_STORE | ENABLE_PC
        ])
    },
    {
        'name': 'ldi_addr', 'op_code': 0x04, # loading immediate from RAM location into register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            MI.LOAD_PC_AS_RAM_ADDRESS,
            MI.LOAD_ADDRESS_FROM_RAM,
            MI.READ_RAM | REGISTER_STORE 
        ])
    },
    {
        'name': 'ldi_addr_reg', 'op_code': 0x18, # loading immediate from RAM location from register value into register : LDI REB, [REX]
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            ENABLE_SOURCE_REGISTER | RAM_ADDRESS_LOAD,
            MI.READ_RAM | REGISTER_STORE 
        ])
    },
    
    {
        'name': 'str', 'op_code': 0x05, # storing register value to RAM location : STR 0xff0000, REA
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            MI.LOAD_PC_AS_RAM_ADDRESS,
            MI.LOAD_ADDRESS_FROM_RAM,
            ENABLE_SOURCE_REGISTER | RAM_WRITE 
        ])
    },
    {
        'name': 'str_addr', 'op_code': 0x06, # storing value to RAM location from RAM address in register : STR REB, REA
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            ENABLE_SOURCE_REGISTER | RAM_ADDRESS_LOAD,
            REGISTER_LOAD | RAM_WRITE
        ])
    },
    
    # ALU Operations
    {
        'name': 'add', 'op_code': 0x07,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.ADD)])
    },
    {
        'name': 'sub', 'op_code': 0x08,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.SUB)])
    },
    {
        'name': 'mul', 'op_code': 0x09,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.MUL)])
    },
    {
        'name': 'div', 'op_code': 0x0A,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.DIV)])
    },
    {
        'name': 'shl', 'op_code': 0x0B, # shift bits to left
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.SHL)])
    },
    {
        'name': 'and', 'op_code': 0x0C,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.AND)])
    },
    {
        'name': 'or', 'op_code': 0x0D,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.OR)])
    },
    {
        'name': 'xor', 'op_code': 0x0E,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([MI.STORE_ACC | GenerateALUOperation(ALU.XOR)])
    },
    
    # control flow instructions
    { 
        'name': 'jp', 'op_code': 0x0F, # jump to address: JP 0xff0000 or JP Label
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': JUMP_INSTRUCTION
    },
    {
        'name': 'jp_addr', 'op_code': 0x10, # jump to address in register: JP REA
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        
        # same as MOV, (might as well remove this later and use the compiler to generate the MOV instruction)
        'steps': JUMP_ADDR_INSTRUCTION
    },
    {
        'name': 'jpz', 'op_code': 0x11, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [1], 'l': [0, 1], 'g': [0, 1]},
        'steps': JUMP_INSTRUCTION
    },
    {
        'name': 'jpz_false', 'op_code': 0x11, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [0], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([ENABLE_PC])
    },
    
    {
        'name': 'jpz_addr', 'op_code': 0x12, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [1], 'l': [0, 1], 'g': [0, 1]},
        'steps': JUMP_ADDR_INSTRUCTION
    },
    {
        'name': 'jpz_addr_false', 'op_code': 0x12, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [0], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([ENABLE_PC])
    },
    
    {
        'name': 'jpc', 'op_code': 0x13, # jump if carry flag is set
        'flags': {'c': [1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': JUMP_INSTRUCTION
    },
    {
        'name': 'jpc_false', 'op_code': 0x13, # jump if carry flag is set
        'flags': {'c': [0], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([ENABLE_PC])
    },
    {
        'name': 'jpc_addr', 'op_code': 0x14, # jump if zero flag is set
        'flags': {'c': [1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': JUMP_ADDR_INSTRUCTION
    },
    {
        'name': 'jpc_addr_false', 'op_code': 0x14, # jump if zero flag is set
        'flags': {'c': [0], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([ENABLE_PC])
    },
    
    {
        'name': 'call', 'op_code': 0x15, # call subroutine at address: CALL 0xff0000 or CALL Label
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            MI.LOAD_PC_AS_RAM_ADDRESS,
            RAM_ADDRESS_LOAD | ENABLE_SOURCE_REGISTER | GenerateRegister(Register.SP),
            RAM_WRITE | ENABLE_SOURCE_REGISTER | GenerateRegister(Register.PC) | ENABLE_SP,
            MI.LOAD_PC_AS_RAM_ADDRESS,
            GenerateRegister(Register.PC) | SET_AS_DESTINATION_ADDRESS | REGISTER_STORE | MI.READ_RAM
        ])
    },
    {
        'name': 'call_addr', 'op_code': 0x16, # call subroutine at indirect address: CALL REA or CALL REX
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            RAM_ADDRESS_LOAD | ENABLE_SOURCE_REGISTER | GenerateRegister(Register.SP),
            RAM_WRITE | ENABLE_SOURCE_REGISTER | GenerateRegister(Register.PC) | ENABLE_SP,
            ENABLE_SOURCE_REGISTER | REGISTER_LOAD
        ])
    },
    
    {
        'name': 'rts', 'op_code': 0x17,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            DECREMENT_SP | ENABLE_SP,
            RAM_ADDRESS_LOAD | ENABLE_SOURCE_REGISTER | GenerateRegister(Register.SP),
            MI.READ_RAM | GenerateRegister(Register.PC) | SET_AS_DESTINATION_ADDRESS | REGISTER_STORE,
            ENABLE_PC,
            MI.LOAD_PC_AS_RAM_ADDRESS
        ])
    }
    
]

def cast_array(value):
    return value if isinstance(value, list) else [value]

def create_instruction_microcode(instruction):
    microcode_steps = []
    
    cf_states = instruction['flags'].get('c', [0, 1])
    zf_states = instruction['flags'].get('z', [0, 1])
    ltf_states = instruction['flags'].get('l', [0, 1])
    gtf_states = instruction['flags'].get('g', [0, 1])

    for cf in cf_states:
        for zf in zf_states:
            for ltf in ltf_states:
                for gtf in gtf_states:
                    flag_value = (cf << 3) | (zf << 2) | (ltf << 1) | gtf
                    
                    for step_index, control_word in enumerate(instruction['steps']):
                        address = (flag_value << 20) | (instruction['op_code'] << 4) | step_index
                        
                        microcode_steps.append({
                            'name': instruction['name'],
                            'address': address,
                            'flag': control_word
                        })
                        
    return microcode_steps

instructions = {}
def generate_microcode(instruction_set):
    global instructions
    
    
    microcode = {}
    for instruction in instruction_set:
        
        instructions[instruction['name']] = f"0x{instruction['op_code']:04X}"

        steps = create_instruction_microcode(instruction)
        for step in steps:
            if step['address'] in microcode:
                print(f"ERROR: Address conflict at 0x{step['address']:06X}")
                print(f"Instruction '{instruction['name']}' (Opcode 0x{instruction['op_code']:04X}) conflicts with '{microcode[step['address']]['name']}' at address 0x{step['address']:06X}")
                sys.exit(1)
            microcode[step['address']] = step
            
    return microcode

def fill_microcode_addresses(microcode):
    
    MAX_ROM_ADDRESS = (0xFFFF << 4) | (0xF << 20) | 0xF
    
    final_output = [0] * (MAX_ROM_ADDRESS + 1)
    
    for address, data in microcode.items():
        if address <= MAX_ROM_ADDRESS:
            final_output[address] = data['flag']
        else:
            print(f"ERROR: Instruction address {address} exceeds MAX_ROM_ADDRESS.")
            sys.exit(1)
            
    return final_output


if __name__ == "__main__":
    
    microcode_dict = generate_microcode(instruction_set)
    
    print(f"Defined {len(microcode_dict)} microcode words. Filling entire 16MiB ROM space...")
    final_rom_data = fill_microcode_addresses(microcode_dict)
    
    print(f"Generated {len(final_rom_data)} total microcode words (16 MiB ROM image).")
    pprint(f"Microcode generation complete. Opcodes:\n{instructions}")
    
    try:
        SaveRom.save_file("machinecode/machinecode.rom", final_rom_data, 24)
        print("ROM data saved successfully.")
    except Exception as e:
        print(f"Failed to save ROM file: {e}")