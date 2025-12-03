# ImageConverter - Converting Images to Sprites

The **ImageConverter** tool converts PNG, BMP, and JPG images into assembly sprite data that can be rendered on the 24-bit CPU's video display.

## Overview

ImageConverter generates assembly code with sprite bitmap data in two formats:

- **Color Mode** (`--color`): Full-color sprites using the XTerm256 palette
- **Monochrome Mode** (`--mono`): Packed-bit monochrome bitmaps

Generated sprites can be integrated directly into your assembly code and rendered using the video driver functions.

## Installation

ImageConverter requires Python 3 and the Pillow library:

```bash
pip install Pillow
```

## Basic Usage

```bash
python ImageConverter.py <input_image> <output.asm> <label_name> [options]
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `input_image` | Path to PNG, BMP, or JPG image file |
| `output.asm` | Output assembly file with sprite data |
| `label_name` | Assembly label name for the sprite data |

### Options

| Option | Description |
|--------|-------------|
| `--color` | Full-color output using XTerm256 palette (default) |
| `--mono` | Monochrome packed-bit output (max 24px wide) |
| `--threshold N` | Brightness threshold for mono mode (0-255, default: 128) |
| `--transparent R,G,B` | Treat this RGB color as transparent |

## Color Mode (Full-Color Sprites)

Color mode converts each pixel to an XTerm256 color index.

### Usage

```bash
python ImageConverter.py logo.png logo_sprite.asm LogoSprite --color
```

### Output Format

```asm
LogoSprite:
    DW #<width>, #<height>
    DW #0xRR, #0xGG, #0xBB      ; Pixel row 0
    DW #0x...
```

Each pixel is stored as one 8-bit XTerm256 color index. Transparent pixels are encoded as `0xFF`.

### Assembly Integration

```asm
; Include or import the generated sprite
!IMPORT "logo_sprite.asm" as LogoSprites

; Render the sprite
.main:
    LDI REA, #10            ; X position
    LDI REB, #15            ; Y position
    LDI REC, LogoSprites.LogoSprite
    CALL Video.DrawBitmap
```

### XTerm256 Color Palette

The XTerm256 palette has 256 colors:

- **0-7**: Standard colors (black, red, green, yellow, blue, magenta, cyan, white)
- **8-15**: Bright variants of standard colors
- **16-231**: 6×6×6 RGB color cube
- **232-255**: 24-level grayscale ramp

When converting images, colors are automatically mapped to the nearest XTerm256 index.

## Monochrome Mode (Packed-Bit Sprites)

Monochrome mode converts images to black-and-white packed bitmaps. Each row is packed into a single 24-bit word with one bit per pixel.

### Constraints

- **Maximum width**: 24 pixels (will be cropped if larger)
- **Unlimited height**
- **Storage**: Very efficient (1 DW per row = 3 bytes per row)

### Usage

```bash
python ImageConverter.py icon.png icon_sprite.asm IconData --mono --threshold 100
```

### Output Format

```asm
IconData:
    DW #<width>, #<height>
    DW #0xBBBBBB         ; Row 0 bitmask
    DW #0xBBBBBB         ; Row 1 bitmask
```

The bitmask format: bit 23 = leftmost pixel, bit 0 = rightmost pixel.
Pixels brighter than the threshold become `1` (on), darker pixels become `0` (off).

### Assembly Integration

```asm
!IMPORT "icon_sprite.asm" as Icons

.main:
    LDI REA, #5             ; X position
    LDI REB, #10            ; Y position
    LDI REC, #0x0F          ; Color (white)
    LDI REX, Icons.IconData
    CALL Video.DrawBitmapMono
```

## Transparency

### Auto-Detect Transparency

If your image has an alpha channel, pixels with alpha < 128 are automatically treated as transparent:

```bash
python ImageConverter.py image.png out.asm MySprite --color
```

### Manual Transparency Color

Specify a specific RGB color as transparent:

```bash
python ImageConverter.py image.png out.asm MySprite --color --transparent 255,0,255
```

This treats magenta (RGB 255,0,255) as transparent in the output.

## Threshold Control (Monochrome)

The threshold determines which pixels are considered "on" in monochrome mode.

- **Threshold 0**: All pixels are on
- **Threshold 128** (default): Standard 50% brightness cutoff
- **Threshold 255**: Only pure white pixels are on

### Examples

```bash
# High contrast (bright pixels only)
python ImageConverter.py icon.png icon.asm IconData --mono --threshold 200

# Low threshold (most pixels on)
python ImageConverter.py icon.png icon.asm IconData --mono --threshold 50
```

## Complete Workflow Example

### Step 1: Prepare Your Image

Create or find an image file. For best results:

- **Color sprites**: Any size, will be converted to XTerm256 palette
- **Monochrome sprites**: Keep width ≤ 24 pixels, use high contrast

### Step 2: Run ImageConverter

```bash
cd DevTools
python ImageConverter.py ../my_icon.png ../os/sprites/icon.asm MyIcon --mono --threshold 120
```

### Step 3: Include in Assembly

```asm
; sprites.asm
!IMPORT "./sprites/icon.asm" as SpriteData

.main:
    LDI REA, #30            ; X
    LDI REB, #20            ; Y
    LDI REC, #0x0A          ; Green color
    LDI REX, SpriteData.MyIcon
    CALL Video.DrawBitmapMono
    
    HALT
```

### Step 4: Compile and Run

```bash
python Compiler.py ./sprites.asm ./sprites.o
python Linker.py ./sprites.o ./mem.cfg ./sprites.bin
```

## Common Issues

### "Pillow is required"

Install Pillow:
```bash
pip install Pillow
```

### Image width exceeds 24px (Monochrome)

Monochrome mode only supports up to 24 pixels wide. The tool will auto-crop, but for best results:

- Resize your image before converting:
  ```bash
  # Using ImageMagick
  convert input.png -resize 24x output.png
  python ImageConverter.py output.png output.asm Label --mono
  ```

### Colors look wrong

The XTerm256 palette is limited. If color accuracy is critical:

1. Try dithering your image before conversion
2. Use monochrome mode for higher contrast
3. Pre-process the image to reduce the color palette

## Performance Tips

### Memory Usage

- **Color sprite (32×32)**: 2 + 32×32 = 1,026 DW (3,078 bytes)
- **Monochrome sprite (24×32)**: 2 + 32 = 34 DW (102 bytes)

Monochrome is ideal for icons, logos, and UI elements.

### Rendering Speed

Both `DrawBitmap` and `DrawBitmapMono` perform pixel-by-pixel rendering. For optimal performance:

- Keep sprite sizes reasonable (< 64×64 pixels)
- Use monochrome for small UI elements
- Cache frequently-drawn sprites in ROM

## Advanced: Binary Sprites

For very large images, use binary mode to store raw palette indices:

```bash
python ImageConverter.py huge.png huge.bin MySprite --binary
```

This creates a compact binary file without assembly overhead. Include it with `INCBIN`:

```asm
MySpriteData:
    DW #<width>, #<height>
    INCBIN "huge.bin"
```

## See Also

- [Video Driver Documentation](../CpuParts/index.md) - Rendering functions
- [Assembler](Compiler.md) - Code compilation
- [Linker](Linker.md) - Linking and ROM generation
