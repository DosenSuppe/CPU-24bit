"""
Helper class for writing DASM lines to an in-memory buffer.

Handles formatting (consistent indent, comment alignment) and strips
characters that would be misinterpreted by the assembler (`@` doc-tag,
stray `;`) from generated comments.
"""

from io import StringIO


class AsmEmitter:

    INDENT = "    "

    def __init__(self):
        self._buf = StringIO()
        self._current_segment = None

    # ------------------------------------------------------------------
    # Output API
    # ------------------------------------------------------------------

    def Segment(self, pName: str) -> None:
        """Start a new segment. No-op if already in this segment."""
        if self._current_segment == pName:
            return
        self._current_segment = pName
        self._buf.write(f"\n.{pName}\n\n")

    def Label(self, pName: str) -> None:
        self._buf.write(f"{pName}:\n")

    def Instr(self, pMnemonic: str, *operands, pComment: str = None) -> None:
        """Emit a single instruction with optional aligned comment."""
        line = self.INDENT + pMnemonic
        if operands:
            line += " " + ", ".join(str(o) for o in operands)
        if pComment:
            line = line.ljust(40) + "; " + self._SanitizeComment(pComment)
        self._buf.write(line + "\n")

    def Raw(self, pText: str) -> None:
        """Emit raw text verbatim (for inline asm). Caller-supplied formatting."""
        for line in pText.split("\n"):
            self._buf.write(line.rstrip() + "\n")

    def Comment(self, pText: str) -> None:
        """Emit a free-standing comment line."""
        self._buf.write(f"; {self._SanitizeComment(pText)}\n")

    def Blank(self) -> None:
        self._buf.write("\n")

    def Header(self, pText: str) -> None:
        """Emit a section/function header comment block."""
        sanitized = self._SanitizeComment(pText)
        self._buf.write(f"; --- {sanitized} ---\n")

    def DataWord(self, *values, pComment: str = None) -> None:
        """Emit a DW directive with one or more values."""
        body = ", ".join(str(v) for v in values)
        line = f"{self.INDENT}DW {body}"
        if pComment:
            line = line.ljust(40) + "; " + self._SanitizeComment(pComment)
        self._buf.write(line + "\n")

    def Result(self) -> str:
        return self._buf.getvalue()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _SanitizeComment(pText: str) -> str:
        """Strip characters that the DASM assembler would treat as line-enders."""
        return pText.replace("@", "(at)").replace(";", ",").replace("\n", " ")
