"""
Image to Sprite Converter for 24-bit CPU.

Converts PNG/BMP/JPG images to assembly sprite data that can be included
in the OS using DW directives and rendered with DrawBitmap or DrawBitmapMono.

Output modes:
  --color    Full-color sprite (one DW per pixel, XTerm256 palette)
             → Use with Video.DrawBitmap
  --mono     Monochrome bitmap (one DW bitmask per row, max 24px wide)
             → Use with Video.DrawBitmapMono

Usage:
    python ImageConverter.py <input_image> <output.asm> <label_name> [options]

Options:
    --color          Full-color output (default)
    --mono           Monochrome packed-bit output
    --threshold N    Brightness threshold for mono mode (0-255, default 128)
    --transparent R,G,B   Treat this RGB color as transparent (default: auto)

Examples:
    python ImageConverter.py logo.png logo_sprite.asm LogoSprite --color
    python ImageConverter.py icon.png icon_sprite.asm IconData --mono --threshold 100

The generated .asm file can be included via !IMPORT or copy-pasted into
your source file's data segment.
"""

import sys
import os

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow")
    sys.exit(1)


# XTerm256 color palette (RGB tuples for colors 0-255)
XTERM256_PALETTE = []

def _InitPalette():
    """Build the XTerm256 color palette."""
    # Standard colors 0-7
    standard = [
        (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
        (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192)
    ]
    # High-intensity colors 8-15
    bright = [
        (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
        (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
    ]
    XTERM256_PALETTE.extend(standard)
    XTERM256_PALETTE.extend(bright)

    # 216-color cube (colors 16-231): 6x6x6
    levels = [0, 95, 135, 175, 215, 255]
    for r in levels:
        for g in levels:
            for b in levels:
                XTERM256_PALETTE.append((r, g, b))

    # Grayscale ramp (colors 232-255): 24 shades
    for i in range(24):
        v = 8 + 10 * i
        XTERM256_PALETTE.append((v, v, v))

_InitPalette()


def RGBToXTerm256(r, g, b):
    """Find the closest XTerm256 color index for an RGB value."""
    bestIdx = 0
    bestDist = float('inf')
    for i, (pr, pg, pb) in enumerate(XTERM256_PALETTE):
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < bestDist:
            bestDist = dist
            bestIdx = i
    return bestIdx


def ConvertColor(image, labelName, transparentColor=None):
    """Convert image to full-color DW sprite data."""
    width, height = image.size
    pixels = image.convert('RGBA')

    lines = []
    lines.append(f"; Full-color sprite: {width}x{height} pixels")
    lines.append(f"; Generated from image file by ImageConverter.py")
    lines.append(f"; Use with Video.DrawBitmap")
    lines.append(f";   LDI REA, #<x>")
    lines.append(f";   LDI REB, #<y>")
    lines.append(f";   LDI REC, {labelName}")
    lines.append(f";   CALL Video.DrawBitmap")
    lines.append(f"")
    lines.append(f"{labelName}:")
    lines.append(f"    DW #{width}, #{height}")

    for y in range(height):
        rowVals = []
        for x in range(width):
            r, g, b, a = pixels.getpixel((x, y))

            # Transparent pixel
            if a < 128:
                rowVals.append("0xFFFFFF")
                continue

            if transparentColor and (r, g, b) == transparentColor:
                rowVals.append("0xFFFFFF")
                continue

            colorIdx = RGBToXTerm256(r, g, b)
            rowVals.append(f"0x{colorIdx:02X}")

        # Write row as DW line(s), max 16 values per line for readability
        for i in range(0, len(rowVals), 16):
            chunk = rowVals[i:i+16]
            prefix = "    DW " if i == 0 else "    DW "
            lines.append(f"{prefix}#" + ", #".join(chunk))

    return "\n".join(lines) + "\n"


def ConvertMono(image, labelName, threshold=128):
    """Convert image to monochrome packed-bit DW sprite data."""
    width, height = image.size

    if width > 24:
        print(f"Warning: Image width {width} exceeds 24px max for mono mode. Cropping.")
        width = 24

    gray = image.convert('L')

    lines = []
    lines.append(f"; Monochrome sprite: {width}x{height} pixels")
    lines.append(f"; Generated from image file by ImageConverter.py")
    lines.append(f"; Threshold: {threshold} (pixels brighter = on)")
    lines.append(f"; Use with Video.DrawBitmapMono")
    lines.append(f";   LDI REA, #<x>")
    lines.append(f";   LDI REB, #<y>")
    lines.append(f";   LDI REC, #<color>")
    lines.append(f";   LDI REX, {labelName}")
    lines.append(f";   CALL Video.DrawBitmapMono")
    lines.append(f"")
    lines.append(f"{labelName}:")
    lines.append(f"    DW #{width}, #{height}")

    for y in range(height):
        bitmask = 0
        pattern = ""
        for x in range(width):
            brightness = gray.getpixel((x, y))
            if brightness >= threshold:
                bitmask |= (1 << (23 - x))
                pattern += "#"
            else:
                pattern += "."
        lines.append(f"    DW #0x{bitmask:06X}         ; {pattern}")

    return "\n".join(lines) + "\n"


def ConvertBinary(image, outputPath, transparentColor=None):
    """Convert image to raw binary file (one byte per pixel, XTerm256 index).
    
    Binary format:
      Byte 0: width
      Byte 1: height
      Bytes 2+: pixel data (row-major), 0xFF = transparent
    
    Use with INCBIN directive:
      MySpriteData:
          DW <width>, <height>      ; header (manual)
          INCBIN "sprite.bin"        ; pixel data
    """
    width, height = image.size
    pixels = image.convert('RGBA')

    data = bytearray()
    data.append(width & 0xFF)
    data.append(height & 0xFF)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels.getpixel((x, y))
            if a < 128:
                data.append(0xFF)
            elif transparentColor and (r, g, b) == transparentColor:
                data.append(0xFF)
            else:
                data.append(RGBToXTerm256(r, g, b))

    with open(outputPath, 'wb') as f:
        f.write(data)

    print(f"Binary sprite written: {outputPath}")
    print(f"  Size: {len(data)} bytes ({width}x{height} pixels)")


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    inputFile = sys.argv[1]
    outputFile = sys.argv[2]
    labelName = sys.argv[3]

    # Parse options
    mode = "color"
    threshold = 128
    transparentColor = None

    i = 4
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--color":
            mode = "color"
        elif arg == "--mono":
            mode = "mono"
        elif arg == "--threshold" and i + 1 < len(sys.argv):
            i += 1
            threshold = int(sys.argv[i])
        elif arg == "--transparent" and i + 1 < len(sys.argv):
            i += 1
            parts = sys.argv[i].split(",")
            transparentColor = (int(parts[0]), int(parts[1]), int(parts[2]))
        elif arg == "--binary":
            mode = "binary"
        else:
            print(f"Unknown option: {arg}")
            sys.exit(1)
        i += 1

    # Load image
    try:
        image = Image.open(inputFile)
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

    print(f"Input: {inputFile} ({image.size[0]}x{image.size[1]})")

    if mode == "binary":
        ConvertBinary(image, outputFile, transparentColor)
    elif mode == "mono":
        result = ConvertMono(image, labelName, threshold)
        with open(outputFile, 'w') as f:
            f.write(result)
        print(f"Mono sprite written: {outputFile}")
        print(f"  Data words: {2 + image.size[1]}")
    else:
        result = ConvertColor(image, labelName, transparentColor)
        with open(outputFile, 'w') as f:
            f.write(result)
        print(f"Color sprite written: {outputFile}")
        print(f"  Data words: {2 + image.size[0] * image.size[1]}")


if __name__ == '__main__':
    main()
