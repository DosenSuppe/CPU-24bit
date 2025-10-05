class Instruction:
    def __init__(self, pName: str, pOpCode: int):
        self.Name = pName
        self.OpCode = pOpCode
        
        self.PossibleFlags = []

    def AddPossibleFlags(self, pFlags: list[int]):
        self.PossibleFlags = pFlags
        return self
    
    def AddEnd(self, pSequence: list[int]):
        self.EndSequence = pSequence
        return self
    
    def AddMain(self, pSequence: list[int]):
        self.MainSequence = pSequence
        return self
    
    def AddFetch(self, pSequence: list[int]):
        self.FetchSequence = pSequence
        return self
    
    def Compile() -> list[int]:

        return []