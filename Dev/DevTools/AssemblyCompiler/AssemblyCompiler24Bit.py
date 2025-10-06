def GenerateSourceRegister(pRegister):
    return (pRegister.value & 0x1F) << 8

def GenerateDestinationRegister2(pRegister):
    return (pRegister.value & 0x1F) << 13

