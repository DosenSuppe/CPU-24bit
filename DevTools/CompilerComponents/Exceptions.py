"""Custom exceptions for the assembler and compiler."""


class AssemblerError(Exception):
    """Base exception for assembler errors."""
    pass


class SyntaxError(AssemblerError):
    """Raised when assembly syntax is invalid."""
    
    def __init__(self, message: str, pLineNumber: int = None):
        self.lineNumber = pLineNumber
        if pLineNumber is not None:
            message = f"Line {pLineNumber}: {message}"
        super().__init__(message)


class OperandError(AssemblerError):
    """Raised when operand format or type is invalid."""
    pass


class SegmentError(AssemblerError):
    """Raised when segment-related errors occur."""
    pass


class InstructionError(AssemblerError):
    """Raised when instruction format or usage is invalid."""
    pass
