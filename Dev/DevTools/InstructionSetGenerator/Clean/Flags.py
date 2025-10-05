from enum import Enum 

class Flags(Enum):
    Zero = 0x400000
    Carry = 0x600000

    Greater = 0x100000
    Less = 0x200000
    Equal = Zero
