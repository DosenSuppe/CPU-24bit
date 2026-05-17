"""Unique label minting for compiler-generated control flow and data."""


class LabelGenerator:
    """
    Generates unique DASM labels per output file.

    Names follow these patterns:
        L_<func>_<kind>_<n>     intra-function (if/while/short-circuit)
        __cc_str_<n>            string literal
        __cc_g_<n>              other compiler-internal globals
    """

    def __init__(self):
        self._counter = 0
        self._str_counter = 0
        self._global_counter = 0

    def NewLabel(self, pFunc: str, pKind: str = "L") -> str:
        n = self._counter
        self._counter += 1
        # Sanitize function name (DASM labels are alphanumeric + underscore)
        safe = pFunc.replace(".", "_")
        return f"L_{safe}_{pKind}_{n}"

    def NewStringLabel(self) -> str:
        n = self._str_counter
        self._str_counter += 1
        return f"__cc_str_{n}"

    def NewGlobalLabel(self) -> str:
        n = self._global_counter
        self._global_counter += 1
        return f"__cc_g_{n}"
