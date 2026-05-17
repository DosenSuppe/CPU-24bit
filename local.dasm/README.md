# DASM Language Support

This extension provides language support for DASM (D-Assembly) files including:

- Syntax highlighting for `.asm` and `.dasm` files
- Hover information for labels with annotations
- Context-aware autocomplete

## Features

### Label Annotations

Document labels with annotations placed on the lines immediately before the label.
Comment lines (`;`) and blank lines do not break the annotation block; any other
non-annotation line resets it.

| Annotation                    | Purpose                                       |
| ----------------------------- | --------------------------------------------- |
| `@REG: description`           | Document a register parameter (REA, REB, ...) |
| `@description: text`          | Free-form description (also `@desc:`)         |
| `@returns REG[, description]` | The register the label leaves its result in   |
| `@deprecated [reason]`        | Mark the label as deprecated                  |
| `@wip [reason]`               | Mark the label as work in progress            |

```dasm
@description: Render a single column of pixels onto the framebuffer.
@REA: ColumnValue
@REB: ColumnIndex
@returns REC, framebuffer offset just written
@wip needs scrolling support
RenderColumn:
    [...]
    RTS
```

Hovering `RenderColumn` (or `Video.RenderColumn` from another file) will show
the description, register parameters, return register, and any
deprecated/WIP markers.

### Namespace-aware hover

Labels with the same name in different files no longer collide. Hovering
`TTYDriver.Handle` resolves to the `Handle` label inside `TTYDriver.asm`,
while `KeyboardDriver.handle` resolves to the one in `KeyboardDriver.asm`.

The namespace prefix matches either an `!IMPORT "X.asm" as Alias` alias in the
current file, or the basename of any `.asm` / `.dasm` file in the workspace.

### Context-aware autocomplete

- At the start of a line: only instructions (`MOV`, `LDI`, `CALL`, ...) and
  directives (`!IMPORT`, `!DECLARE`).
- After a label-taking instruction (`CALL`, `JP`, `SET_IVR`, ...): namespace
  bases plus labels in the current file.
- After typing `Namespace.`: only labels inside that namespace.

### Syntax highlighting

Full syntax highlighting for DASM assembly language including instructions,
registers, labels and namespaced references, numbers, comments, directives,
and label annotations.

## Release Notes

### 0.0.3
- Hover disambiguation between same-named labels across files.
- Context-aware completion (instructions on a bare line, namespace-scoped on
  `Namespace.`, namespaces + local labels after instructions like `CALL`).
- New annotations: `@description`, `@returns`, `@deprecated`, `@wip`.

### 0.0.1
- Initial release with syntax highlighting and hover support for register annotations.
