"""
Minimal C preprocessor for cc.py.

Supports just enough to be useful:
    #include "path"     - inline-paste the named file. Path is resolved
                          relative to the directory of the *including* file.
    #pragma once        - mark the current file so further #includes of it
                          are skipped (by canonical absolute path).

Not supported: angle-bracket includes (<stdio.h>), #define, #if/#ifdef,
macro expansion, line directives. Unrecognized `#` directives raise.
"""

import os
import re
from typing import List, Set

from CCompilerComponents.Exceptions import CCompileError


_INCLUDE_RE = re.compile(r'^\s*#\s*include\s+"([^"]+)"\s*$')
_PRAGMA_ONCE_RE = re.compile(r'^\s*#\s*pragma\s+once\s*$')
_DIRECTIVE_RE = re.compile(r'^\s*#')
# Strip trailing `// comment` from a directive line so the regexes above match.
# We only strip on directive lines — full C comment handling is the lexer's job.
_LINE_COMMENT_RE = re.compile(r'//.*$')


class CPreprocessError(CCompileError):
    pass


def Preprocess(pInputPath: str) -> str:
    """Read `pInputPath` and return its fully-preprocessed text.

    The result is plain C source with all `#include`s spliced in. `#pragma
    once` participants are deduplicated by canonical absolute path.
    """
    visited_once: Set[str] = set()
    include_stack: List[str] = []
    out_parts: List[str] = []
    _ProcessFile(pInputPath, out_parts, visited_once, include_stack)
    return "".join(out_parts)


def _ProcessFile(pPath: str, pOut: List[str], pVisitedOnce: Set[str],
                 pStack: List[str]) -> None:
    abs_path = os.path.abspath(pPath)
    if abs_path in pVisitedOnce:
        return
    if abs_path in pStack:
        chain = " -> ".join(pStack + [abs_path])
        raise CPreprocessError(f"Recursive #include: {chain}")
    try:
        with open(pPath, "r") as f:
            text = f.read()
    except FileNotFoundError:
        raise CPreprocessError(f"#include: file not found: {pPath}")

    pStack.append(abs_path)
    base_dir = os.path.dirname(abs_path)
    pragma_once_seen = False

    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        stripped = line.rstrip("\r\n")
        # Only directive lines get their trailing `//comment` stripped here;
        # non-directive lines are forwarded verbatim for the lexer to handle.
        if _DIRECTIVE_RE.match(stripped):
            stripped = _LINE_COMMENT_RE.sub("", stripped).rstrip()

        m_once = _PRAGMA_ONCE_RE.match(stripped)
        if m_once:
            pragma_once_seen = True
            # Emit a blank so line numbers stay roughly aligned for diagnostics.
            pOut.append("\n")
            continue

        m_inc = _INCLUDE_RE.match(stripped)
        if m_inc:
            inc_rel = m_inc.group(1)
            inc_path = os.path.join(base_dir, inc_rel)
            _ProcessFile(inc_path, pOut, pVisitedOnce, pStack)
            # Trailing newline keeps the rest of the file at correct columns.
            pOut.append("\n")
            continue

        if _DIRECTIVE_RE.match(stripped):
            raise CPreprocessError(
                f"{pPath}:{lineno}: unsupported preprocessor directive: "
                f"{stripped.strip()!r}")

        pOut.append(line)

    pStack.pop()
    if pragma_once_seen:
        pVisitedOnce.add(abs_path)
