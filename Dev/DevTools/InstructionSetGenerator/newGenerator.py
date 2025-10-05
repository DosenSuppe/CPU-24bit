#!python3

import sys
import save_rom

# import save_rom # Assuming you have a separate module for saving the file

# --- Microcode Control Word Bit Definitions (ROM Output: 24 bits) ---
# These are the literal hex values for your core execution phases, derived from your example:
FETCH_STEP_1 = 0x7C0004
FETCH_STEP_2 = 0x00000B
INSTRUCTION_END = 0x000800 # Signal to reset the microcode Step Counter (PC to 0)

def generateInstruction(pInstruction: list[int] = []):
    return [FETCH_STEP_1, FETCH_STEP_2] + [instruction for instruction in pInstruction] + [INSTRUCTION_END]

def generateRegisterLoadImidiate(pRegister: int):
    pass

def generateRegisterLoadMemory(pRegister: int):
    pass

def generateRegisterStoreToMemory(pRegister: int):
    pass


# --- Instruction Set Definition ---
instruction_set = [
    {   
        'name': 'nop',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]}, 
        'steps': generateInstruction()
    },
    {   
        'name': 'halt',
        'flags': {'c': [0, 1], 'z': [0, 1], 'l': [0, 1], 'g': [0, 1]}, 
        'steps': generateInstruction([0x400])
    },
    {
        'name': 'load',
    }
]

# Helper to convert single values to lists if necessary
def cast_array(value):
    return value if isinstance(value, list) else [value]

# The main function to generate the microcode for a single instruction
def create_instruction_microcode(instruction):
    microcode_steps = []
    
    # Get flag dependencies, defaulting to [0, 1] for all if not specified
    cf_states = instruction['flags'].get('c', [0, 1])
    zf_states = instruction['flags'].get('z', [0, 1])
    ltf_states = instruction['flags'].get('l', [0, 1])
    gtf_states = instruction['flags'].get('g', [0, 1])

    # Loop through all relevant flag combinations (max 16)
    for cf in cf_states:
        for zf in zf_states:
            for ltf in ltf_states:
                for gtf in gtf_states:
                    
                    # 1. Calculate the 4-bit Flag Value (the raw value 0-15)
                    # Order: [GT, LT, Z, C] (Bits 3, 2, 1, 0 of the 4-bit value)
                    flag_value = (gtf << 3) | (ltf << 2) | (zf << 1) | cf
                    
                    # 2. Iterate through the instruction steps
                    for step_index, control_word in enumerate(instruction['steps']):
                        
                        # Calculate the 24-bit Microcode ROM Address:
                        # Bits 20-23: Flag Value (Shifted by 20)
                        # Bits 4-19: Opcode Value (Shifted by 4)
                        # Bits 0-3: Step Counter (Shifted by 0)
                        address = (flag_value << 20) | (instruction['op_code'] << 4) | step_index
                        
                        microcode_steps.append({
                            'name': instruction['name'],
                            'address': address,
                            'flag': control_word # The final 24-bit control word
                        })
                        
    return microcode_steps

# Main generation loop
def generate_microcode(instruction_set):
    currentOpCode = 0
    
    microcode = {}
    for instruction in instruction_set:
        instruction['op_code'] = currentOpCode
        currentOpCode += 1
        steps = create_instruction_microcode(instruction)
        for step in steps:
            # Check for address conflict
            if step['address'] in microcode:
                print(f"ERROR: Address conflict at 0x{step['address']:06X}")
                print(f"Instruction '{step['name']}' conflicts with '{microcode[step['address']]['name']}'")
                sys.exit(1)
            microcode[step['address']] = step
            
    return microcode

# Fills the microcode missing addresses with NOP (0x000000)
def fill_microcode_addresses(microcode):
    
    # Max Opcode (0xFFFF) + Max Flags (0xF) + Max Step (0xF)
    MAX_ROM_ADDRESS = (0xFFFF << 4) | (0xF << 20) | 0xF # 0xFFFFFF (16,777,215)
    
    # Initialize the entire ROM space with a NOP control word (0x000000)
    final_output = [0] * (MAX_ROM_ADDRESS + 1)
    
    # Fill in the defined instructions
    for address, data in microcode.items():
        if address <= MAX_ROM_ADDRESS:
            final_output[address] = data['flag']
        else:
            print(f"ERROR: Instruction address {address} exceeds MAX_ROM_ADDRESS.")
            sys.exit(1)
            
    return final_output


# --- Execution Block ---
if __name__ == "__main__":
    
    # 1. Generate the microcode dictionary
    microcode_dict = generate_microcode(instruction_set)
    
    # 2. Fill the entire ROM space (16M addresses)
    print(f"Defined {len(microcode_dict)} microcode words. Filling entire 16MiB ROM space...")
    final_rom_data = fill_microcode_addresses(microcode_dict)
    
    # 3. Save the ROM file 
    print(f"Generated {len(final_rom_data)} total microcode words (48 MiB ROM image).")
    
    # Example for command line saving (replace with your save_rom usage)
    try:
        save_rom.save_file("cpu_microcode.rom", final_rom_data, 24)
        print("ROM data saved successfully.")
    except Exception as e:
        print(f"Failed to save ROM file: {e}")