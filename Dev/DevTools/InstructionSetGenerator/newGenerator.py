import sys
import save_rom
from pprint import pprint
from Microcode import *
from Registers import *

FETCH = [
    RAM_ADDRESS_LOAD | REGISTER_LOAD | GenerateDestinationRegister(Register.PC), 
    ENABLE_RAM_OUTPUT | RAM_READ | ENABLE_PC | INSTRUCTION_LOAD
]

INSTRUCTION_END = [INSTRUCTION_READ]

def generateInstruction(pInstruction: list[int] = []):
    return FETCH + [instruction for instruction in pInstruction] + INSTRUCTION_END

instruction_set = [
    {   
        'name': 'nop',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]}, 
        'steps': generateInstruction()
    },
    {
        'name': 'halt',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]}, 
        'steps': generateInstruction([HALT])
    },
    
    # data movement instructions
    {
        'name': 'mov', # moving between registers
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([ENABLE_SOURCE_REGISTER | REGISTER_STORE])
    },
    
    {
        'name': 'ldi', # loading immediate to register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            RAM_ADDRESS_LOAD | REGISTER_LOAD | GenerateDestinationRegister(Register.PC), 
            ENABLE_RAM_OUTPUT | REGISTER_STORE | ENABLE_PC | RAM_READ
        ])
    },
    {
        'name': 'ldi_addr', # loading immediate from RAM location into register
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction() # TODO
    },
    
    {
        'name': 'str', # storing register value to RAM location
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([
            RAM_ADDRESS_LOAD | REGISTER_LOAD |GenerateDestinationRegister(Register.PC),
            0x01000E, 
            0x020010
        ])
    },
    {
        'name': 'str_addr', # storing immediate value to RAM location
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction() # TODO
    },
    
    # ALU Operations
    {
        'name': 'add',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([0x880000])
    },
    {
        'name': 'sub',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([0x881000])
    },
    {
        'name': 'mul',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([0x882000])
    },
    {
        'name': 'div',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([0x883000])
    },
    {
        'name': 'div',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]},
        'steps': generateInstruction([0x884000])
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
    currentOpCode = 0
    
    microcode = {}
    for instruction in instruction_set:
        instruction['op_code'] = currentOpCode
        instructions[instruction['name']] = f"0x{currentOpCode:06X}"
        currentOpCode += 1
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
        save_rom.save_file("bytecode/cpu_microcode.rom", final_rom_data, 24)
        print("ROM data saved successfully.")
    except Exception as e:
        print(f"Failed to save ROM file: {e}")