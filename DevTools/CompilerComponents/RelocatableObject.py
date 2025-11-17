"""Relocatable object file representation."""

from typing import Dict, List, Tuple, Any


class RelocatableObject:
    """
    Represents a compiled object file with relocation information.
    
    This class stores the compiled segments, symbol labels, relocation entries,
    and import dependencies for an assembly source file. It provides serialization
    to enable linking multiple object files together.
    
    Attributes:
        filename: Source filename this object was compiled from
        segments: Dictionary mapping segment names to lists of bytecode words
        labels: Dictionary mapping label names to (segment, offset) tuples
        relocations: List of relocation entries for unresolved symbols
        imports: List of imported file dependencies
    """
    
    def __init__(self, pFilename: str):
        """
        Initialize a new relocatable object.
        
        Args:
            pFilename: The source filename being compiled
        """
        self.filename = pFilename
        self.segments: Dict[str, List[int]] = {}
        self.labels: Dict[str, Tuple[str, int]] = {}
        self.relocations: List[Dict[str, Any]] = []
        self.imports: List[str] = []
        self.declarations: Dict[str, str] = {}  # Variable name -> expression string
    
    def AddLabel(self, pLabelName: str, pSegment: str, pOffset: int) -> None:
        """
        Add a label definition to the object file.
        
        Args:
            pLabelName: Name of the label
            pSegment: Segment where the label is defined
            pOffset: Offset within the segment
        """
        self.labels[pLabelName] = (pSegment, pOffset)
    
    def AddRelocation(self, pSegment: str, pOffset: int, pSymbol: str, 
                      pRelocationType: str = 'absolute') -> None:
        """
        Add a relocation entry for an unresolved symbol reference.
        
        Args:
            pSegment: Segment containing the reference
            pOffset: Offset within the segment where relocation is needed
            pSymbol: Symbol name to resolve
            pRelocationType: Type of relocation ('absolute' or 'relative')
        """
        self.relocations.append({
            'segment': pSegment,
            'offset': pOffset,
            'type': pRelocationType,
            'symbol': pSymbol
        })
    
    def AddImport(self, pImportFile: str) -> None:
        """
        Add an import dependency.
        
        Args:
            pImportFile: Filename being imported
        """
        if pImportFile not in self.imports:
            self.imports.append(pImportFile)
    
    def AddDeclaration(self, pVariableName: str, pExpression: str) -> None:
        """
        Add a variable declaration.
        
        Args:
            pVariableName: Name of the declared variable
            pExpression: Expression string to evaluate (e.g., "$FrameBuffer.Start + 1")
        """
        self.declarations[pVariableName] = pExpression
    
    def EnsureSegment(self, pSegmentName: str) -> None:
        """
        Ensure a segment exists, creating it if necessary.
        
        Args:
            pSegmentName: Name of the segment
        """
        if pSegmentName not in self.segments:
            self.segments[pSegmentName] = []
    
    def AppendToSegment(self, pSegmentName: str, pValue: int) -> int:
        """
        Append a value to a segment and return the offset.
        
        Args:
            pSegmentName: Name of the segment
            pValue: Bytecode word to append
            
        Returns:
            The offset where the value was appended
        """
        self.EnsureSegment(pSegmentName)
        offset = len(self.segments[pSegmentName])
        self.segments[pSegmentName].append(pValue)
        return offset
    
    def GetSegmentOffset(self, pSegmentName: str) -> int:
        """
        Get the current offset (size) of a segment.
        
        Args:
            pSegmentName: Name of the segment
            
        Returns:
            Current offset in the segment
        """
        return len(self.segments.get(pSegmentName, []))
    
    def ToDict(self) -> dict:
        """
        Serialize the object file to a dictionary for JSON export.
        
        Returns:
            Dictionary representation of the object file
        """
        return {
            'filename': self.filename,
            'segments': self.segments,
            'labels': self.labels,
            'relocations': self.relocations,
            'imports': self.imports,
            'declarations': self.declarations
        }
    
    @staticmethod
    def FromDict(data: dict) -> 'RelocatableObject':
        """
        Deserialize an object file from a dictionary.
        
        Args:
            data: Dictionary containing object file data
            
        Returns:
            Reconstructed RelocatableObject instance
        """
        obj = RelocatableObject(data['filename'])
        obj.segments = data['segments']
        obj.labels = data['labels']
        obj.relocations = data['relocations']
        obj.imports = data['imports']
        obj.declarations = data.get('declarations', {})  # Support older files without declarations
        return obj
    
    def __repr__(self) -> str:
        return (f"RelocatableObject(filename={self.filename}, "
                f"segments={list(self.segments.keys())}, "
                f"labels={len(self.labels)}, "
                f"relocations={len(self.relocations)})")
