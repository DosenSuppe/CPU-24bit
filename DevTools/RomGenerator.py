import sys
import SaveRom as SaveRom

from pprint import pprint

from Values.Microcode import *
from Values.Registers import *

from Values.MicroInstructions import MicroInstructions as MI
from Values.OperationsALU import ALU

FETCH = [MAR_WRITE | PC_ADDRESS_OUT,  PC_ADDRESS_OUT | RAM_READ | INSTRUCTION_LOAD | PC_INCREMENT]

def generateInstruction(pInstruction: list[int] = []):
    return FETCH + [instruction for instruction in pInstruction] + [INSTRUCTION_END | INTERRUPT_CHECK]

# shared across multiple jump instructions:
JUMP_INSTRUCTION = generateInstruction([
    PC_ADDRESS_OUT | MAR_WRITE,
    PC_ADDRESS_OUT | PC_WRITE | RAM_READ
])

JUMP_ADDR_INSTRUCTION = generateInstruction([
    GPR_DATA_OUT | PC_WRITE | PC_ADDRESS_OUT | MAR_WRITE,
])



instruction_set = [
    {   
        'name': 'nop', 'op_code': 0x00,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]}, 
        'steps': generateInstruction()
    },
    {
        'name': 'halt', 'op_code': 0x01,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]}, 
        'steps': generateInstruction([HALT])
    },
    
    # data movement instructions
    {
        'name': 'mov', 'op_code': 0x02, # moving between registers
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GPR_DATA_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'ldi', 'op_code': 0x03, # loading immediate to register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            PC_ADDRESS_OUT | MAR_WRITE,
            RAM_READ | GPR_B_WRITE | PC_ADDRESS_OUT | PC_INCREMENT
        ])
    },
    {
        'name': 'ldi_addr', 'op_code': 0x04, # loading immediate from RAM location into register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            PC_ADDRESS_OUT | MAR_WRITE,
            PC_ADDRESS_OUT | RAM_READ | MAR_WRITE | MAR_SOURCE_SELECT,
            PC_ADDRESS_OUT | RAM_READ | GPR_B_WRITE | PC_INCREMENT
        ])
    },
    {
        'name': 'ldi_addr_reg', 'op_code': 0x05, # loading immediate from RAM location from register value into register : LDI REB, [REX]
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            GPR_ADDRESS_OUT | MAR_WRITE,
            PC_ADDRESS_OUT | RAM_READ | GPR_B_WRITE
        ])
    },
    {
        'name': 'str', 'op_code': 0x06, # storing register value to RAM location : STR 0xff0000, REA
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            PC_ADDRESS_OUT | MAR_WRITE,
            PC_ADDRESS_OUT | RAM_READ | MAR_WRITE | MAR_SOURCE_SELECT,
            PC_ADDRESS_OUT | GPR_DATA_OUT | RAM_WRITE | PC_INCREMENT
        ])
    },
    {
        'name': 'str_addr', 'op_code': 0x07, # storing value to RAM location from RAM address in register : STR REB, REA
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            GPR_B_ADDRESS_OUT | MAR_WRITE,                  # load address from B-Register
            GPR_B_ADDRESS_OUT | GPR_DATA_OUT | RAM_WRITE    # load value to write from A-Register
        ])
    },
    
    # ALU Operations (ALU operations could be optimized to include the Instruction_End cycle within the ALU operation itself, making them 3 cycles instead of 4)
    {
        'name': 'add', 'op_code': 0x08, # adding values with registers only (e.g. ADD REA, REB or ADD REA, REB, REZ)
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.ADD) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'sub', 'op_code': 0x09,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.SUB) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'mul', 'op_code': 0x0A,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.MUL) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'div', 'op_code': 0x0B,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.DIV) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'shl', 'op_code': 0x0C, # shift bits to left
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.SHL) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'shr', 'op_code': 0x0D,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.SHR) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'nand', 'op_code': 0x0E,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.NAND) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'and', 'op_code': 0x0F,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.AND) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'or', 'op_code': 0x10,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.OR) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'xor', 'op_code': 0x11,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.XOR) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'nor', 'op_code': 0x12,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.NOR) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    {
        'name': 'not', 'op_code': 0x13,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([GenerateALUOperation(ALU.NOT) | FR_WRITE | ALU_OUT | GPR_B_WRITE | PC_ADDRESS_OUT])
    },
    
    # control flow instructions
    { 
        'name': 'jp', 'op_code': 0x14, # jump to address: JP 0xff0000 or JP Label
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': JUMP_INSTRUCTION
    },
    {
        'name': 'jp_addr', 'op_code': 0x15, # jump to address in register: JP REA
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': JUMP_ADDR_INSTRUCTION
    },
    {
        'name': 'jpz', 'op_code': 0x16, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': JUMP_INSTRUCTION
    },
    {
        'name': 'jpz_false', 'op_code': 0x16, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [0], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([PC_INCREMENT])
    },
    {
        'name': 'jpz_addr', 'op_code': 0x17, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': JUMP_ADDR_INSTRUCTION
    },
    {
        'name': 'jpz_addr_false', 'op_code': 0x17, # jump if zero flag is set
        'flags': {'c': [0, 1], 'z': [0], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([PC_INCREMENT])
    },
    {
        'name': 'jpc', 'op_code': 0x18, # jump if carry flag is set
        'flags': {'c': [1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': JUMP_INSTRUCTION
    },
    {
        'name': 'jpc_false', 'op_code': 0x18, # jump if carry flag is set
        'flags': {'c': [0], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([PC_INCREMENT])
    },
    {
        'name': 'jpc_addr', 'op_code': 0x19, # jump if carry flag is set
        'flags': {'c': [1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': JUMP_ADDR_INSTRUCTION
    },
    {
        'name': 'jpc_addr_false', 'op_code': 0x19, # jump if carry flag is set
        'flags': {'c': [0], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([PC_INCREMENT])
    },
    
    {
        'name': 'call', 'op_code': 0x1A, # call subroutine at address: CALL 0xff0000 or CALL Label
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_ADDRESS_OUT | MAR_WRITE,
            RAM_WRITE | PC_DATA_OUT | SP_DECREMENT,
            PC_ADDRESS_OUT | MAR_WRITE,
            RAM_READ | PC_WRITE | PC_ADDRESS_OUT | PC_INCREMENT
        ])
    },
    {
        'name': 'call_addr', 'op_code': 0x1B, # call subroutine at indirect address: CALL REA or CALL REX
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_ADDRESS_OUT | MAR_WRITE,
            RAM_WRITE | PC_DATA_OUT | SP_DECREMENT,
            GPR_ADDRESS_OUT | MAR_WRITE | GPR_DATA_OUT | PC_WRITE,
        ])
    },
    {
        'name': 'rts', 'op_code': 0x1C,
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_INCREMENT,
            SP_ADDRESS_OUT | MAR_WRITE,
            SP_ADDRESS_OUT | RAM_READ | PC_WRITE,
            PC_ADDRESS_OUT | MAR_WRITE
        ])
    },

    {
        'name': 'push', 'op_code': 0x1D, # pushes value from a register onto the stack
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_ADDRESS_OUT | MAR_WRITE,
            GPR_DATA_OUT | RAM_WRITE | SP_DECREMENT,
            PC_ADDRESS_OUT | MAR_WRITE
         ])
    },
    {
        'name': 'push_addr', 'op_code': 0x1E, # pushes value from a register onto the stack
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_ADDRESS_OUT | MAR_WRITE,
            GPR_DATA_OUT | RAM_WRITE | SP_DECREMENT,
            PC_ADDRESS_OUT | MAR_WRITE
         ])
    },
    {
        'name': 'pop', 'op_code': 0x1F, # pops value from the stack into a register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_INCREMENT,
            SP_ADDRESS_OUT | MAR_WRITE,
            GPR_B_WRITE | RAM_READ | SP_ADDRESS_OUT,
            PC_ADDRESS_OUT | MAR_WRITE
         ])
    },

    {
        'name': 'setsp', 'op_code': 0x20, # sets the stack pointer
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            PC_ADDRESS_OUT | MAR_WRITE,
            SP_WRITE | RAM_READ | PC_ADDRESS_OUT | PC_INCREMENT
         ])
    },
    {
        'name': 'getsp', 'op_code': 0x21, # gets the stack pointer
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_DATA_OUT | GPR_B_WRITE | PC_ADDRESS_OUT
        ])
    },
    {
        'name': 'getpc', 'op_code': 0x22, # gets the program counter
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            PC_DATA_OUT | GPR_B_WRITE | PC_ADDRESS_OUT
        ])
    },
    {
        'name': 'setivr', 'op_code': 0x23, # sets the interrupt vector register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            PC_ADDRESS_OUT | MAR_WRITE,
            PC_ADDRESS_OUT | RAM_READ | IVR_WRITE | PC_INCREMENT
        ])
    },
    
    # interrupt instructions
    {
        'name': 'rti', 'op_code': 0xfe, # return from interrupt
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_INCREMENT,
            SP_ADDRESS_OUT | MAR_WRITE,
            
            FR_WRITE_FROM_RAM | FR_WRITE | RAM_READ | SP_ADDRESS_OUT,
            SP_INCREMENT,
            
            SP_ADDRESS_OUT | MAR_WRITE,
            PC_WRITE | RAM_READ | SP_ADDRESS_OUT,
            
            INTERRUPT_REQUEST_ACKNOWLEDGE
        ])
    },
    {
        'name': 'int_trigger', 'op_code': 0xff, # trigger an interrupt
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1], 'e': [0, 1]},
        'steps': generateInstruction([
            SP_ADDRESS_OUT | MAR_WRITE,
            PC_DATA_OUT | RAM_WRITE | SP_DECREMENT,
            
            SP_ADDRESS_OUT | MAR_WRITE,
            FR_DATA_OUT | RAM_WRITE | SP_DECREMENT,
            
            PC_WRITE | IVR_OUT | PC_ADDRESS_OUT
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
    etf_states = instruction['flags'].get('e', [0, 1])

    for cf in cf_states:
        for zf in zf_states:
            for ltf in ltf_states:
                for gtf in gtf_states:
                    for etf in etf_states:
                        flag_value = (cf << 4) | (zf << 3) | (ltf << 2) | (gtf << 1) | etf

                        for step_index, control_word in enumerate(instruction['steps']):
                            address = (flag_value << 19) | (instruction['op_code'] << 5) | step_index
                            
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
    
    MAX_ROM_ADDRESS = (0x1F << 19) | (0xFF << 5) | 0x1F
    print(f"MAX_ROM_ADDRESS: {MAX_ROM_ADDRESS} (0x{MAX_ROM_ADDRESS:06X})")
    
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
        SaveRom.save_file("machinecode/machinecode.rom", final_rom_data, 32)
        print("ROM data saved successfully.")
    except Exception as e:
        print(f"Failed to save ROM file: {e}")