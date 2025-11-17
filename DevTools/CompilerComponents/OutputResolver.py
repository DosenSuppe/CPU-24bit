"""Output path utilities for the compiler."""

import os
from typing import Optional


class OutputPathResolver:
    """Resolves output paths for compiled object files."""
    
    @staticmethod
    def ResolveOutputPath(pInputFile: str, pOutputFile: Optional[str]) -> str:
        """
        Resolve the output path for an object file.
        
        Rules:
        1. If output_file is provided, use it
        2. If input contains 'src' directory, mirror structure in 'bin'
        3. Otherwise, use input filename without extension in current directory
        
        Args:
            input_file: Input assembly file path
            output_file: Optional explicit output path
            
        Returns:
            Resolved output path (without .obj extension)
        """
        # Use explicit output if provided
        if pOutputFile is not None:
            outputDir = os.path.dirname(pOutputFile + ".obj")
            if outputDir and not os.path.exists(outputDir):
                os.makedirs(outputDir, exist_ok=True)
            return pOutputFile
        
        # Auto-determine from input path
        inputPath = os.path.normpath(pInputFile)
        inputParts = inputPath.split(os.sep)
        
        # Check for 'src' directory in path
        if 'src' in inputParts:
            return OutputPathResolver._ResolveSrcToBin(inputParts)
        
        # Fallback: use input filename in current directory
        return os.path.splitext(os.path.basename(pInputFile))[0]
    
    @staticmethod
    def _ResolveSrcToBin(pInputParts: list) -> str:
        """Mirror src/ structure to bin/ directory."""
        srcIndex = pInputParts.index('src')
        
        # Get path before 'src'
        basePath = os.sep.join(pInputParts[:srcIndex])
        
        # Get relative path after 'src'
        relativePath = os.sep.join(pInputParts[srcIndex + 1:])
        
        # Remove .asm extension
        relativePathNoExt = os.path.splitext(relativePath)[0]
        
        # Create bin directory structure
        binDir = os.path.join(basePath, 'bin', os.path.dirname(relativePathNoExt))
        if binDir and not os.path.exists(binDir):
            os.makedirs(binDir, exist_ok=True)
        
        # Return final output path
        return os.path.join(basePath, 'bin', relativePathNoExt)