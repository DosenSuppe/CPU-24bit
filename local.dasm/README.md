# DASM Language Support

This extension provides language support for DASM (D-Assembly) files including:

- Syntax highlighting for .asm and .dasm files  
- Hover information for labels with register annotations
- IntelliSense completion for labels

## Features

### Register Documentation
You can document which registers a label uses by adding register annotations before the label:

```dasm
@REA: ColumnValue
@REB: ColumnIndex
RenderColumn:
    [...] ; implementation of rendering a single column
    RTS
```

When you hover over `RenderColumn` in a CALL instruction or reference, you'll see:

**Uses Registers:**
• **REA**: ColumnValue
• **REB**: ColumnIndex

### Syntax Highlighting
Full syntax highlighting for DASM assembly language including:
- Instructions and keywords
- Registers  
- Labels and references
- Numbers and constants
- Comments
- Directives

## Local Development

This extension can be run locally for testing without publishing.

## Release Notes

### 0.0.1
- Initial release with syntax highlighting and hover support for register annotations
