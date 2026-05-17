"""Custom exceptions for the C compiler."""


class CCompileError(Exception):
    """Base exception for C compiler errors."""
    pass


class CLexError(CCompileError):
    """Raised when tokenization fails."""

    def __init__(self, message: str, pLine: int = None, pColumn: int = None):
        self.line = pLine
        self.column = pColumn
        if pLine is not None:
            message = f"Line {pLine}, col {pColumn}: {message}"
        super().__init__(message)


class CParseError(CCompileError):
    """Raised when parsing fails."""

    def __init__(self, message: str, pLine: int = None, pColumn: int = None):
        self.line = pLine
        self.column = pColumn
        if pLine is not None:
            message = f"Line {pLine}, col {pColumn}: {message}"
        super().__init__(message)


class CSemanticError(CCompileError):
    """Raised when semantic analysis fails (type errors, undeclared symbols)."""

    def __init__(self, message: str, pLine: int = None):
        self.line = pLine
        if pLine is not None:
            message = f"Line {pLine}: {message}"
        super().__init__(message)


class CCodeGenError(CCompileError):
    """Raised when code generation hits an unexpected condition."""
    pass
