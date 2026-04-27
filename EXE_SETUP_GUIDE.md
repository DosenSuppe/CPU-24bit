# Converting DevTools to Executables

This guide explains how to convert your Python DevTools to standalone `.exe` files that can be run from anywhere on your PC.

## Quick Start

### Option 1: Batch File (Easiest)
1. Double-click `BUILD_EXES.bat` in your project root
2. Wait for the build to complete
3. Follow the instructions to add the `bin` folder to your system PATH

### Option 2: PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\BUILD_EXES.ps1
```

## What Gets Built

The build process converts these Python tools to standalone EXEs:
- `Compiler.exe` - Assembly compiler
- `ImageConverter.exe` - Image to sprite converter (requires Pillow)
- `Linker.exe` - Object file linker
- `RomGenerator.exe` - ROM file generator

## Adding to PATH (Make Them Accessible Globally)

After building the EXEs, add them to your PATH environment variable so you can run them from any command prompt.

### Method 1: GUI (Recommended for beginners)
1. Press `Win + Pause/Break` (or right-click "This PC" → Properties)
2. Click **"Advanced system settings"**
3. Click **"Environment Variables..."** button
4. Under "User variables for [your username]", click **"New..."**
5. **Variable name:** `PATH`
6. **Variable value:** `C:\Users\Niklas\Documents\Logisim\newCPU\bin`
7. Click OK three times
8. **Restart your terminal** for the changes to take effect

### Method 2: PowerShell (Automatic)
Run this command in PowerShell:
```powershell
$binPath = "C:\Users\Niklas\Documents\Logisim\newCPU\bin"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$binPath", "User")
```

Then restart your terminal.

### Method 3: Command Prompt (Automatic)
```cmd
setx PATH "%PATH%;C:\Users\Niklas\Documents\Logisim\newCPU\bin"
```

Then restart your terminal.

## Usage Examples

Once added to PATH, you can run the tools from any directory:

```cmd
# Compile an assembly file
Compiler C:\path\to\file.asm

# Convert an image to sprite data
ImageConverter logo.png logo_sprite.asm LogoSprite --color

# Link object files
Linker input1.obj input2.obj -o output.obj

# Generate ROM
RomGenerator
```

## Troubleshooting

### "Not recognized as an internal or external command"
- Make sure you've added the `bin` folder to PATH
- Restart your terminal/command prompt after adding to PATH
- Verify the EXE files exist in the `bin` folder

### ImageConverter says "Pillow is required"
Run this before building:
```cmd
pip install Pillow
```

### Building fails with "pyinstaller not found"
Ensure PyInstaller is installed:
```cmd
pip install pyinstaller
```

## Technical Details

- **PyInstaller** is used to bundle Python code into standalone executables
- `--onefile` flag creates a single `.exe` file instead of a folder
- EXEs are created in the `bin/` folder at your project root
- Original `.py` files remain unchanged
- Build artifacts (temp files) are cleaned up automatically

## Rebuilding After Changes

If you modify any Python files in DevTools, simply run `BUILD_EXES.bat` or `BUILD_EXES.ps1` again to rebuild all EXEs.

## Distributing the EXEs

If you want to share these EXEs with others:
1. Only the files in the `bin/` folder are needed
2. Users don't need Python installed
3. Make sure to include `ImageConverter.exe` if they need image conversion (includes Pillow runtime)
