@echo off
REM Build script to convert DevTools Python files to EXEs using PyInstaller

echo Installing PyInstaller...
pip install pyinstaller pillow -q

echo.
echo Building EXE files...
cd /d "%~dp0DevTools"

REM Build each tool
echo Building dasm.exe...
pyinstaller --onefile --name dasm --distpath ..\bin Compiler.py > nul 2>&1

echo Building ImageConverter.exe...
pyinstaller --onefile --name ImageConverter --distpath ..\bin ImageConverter.py > nul 2>&1

echo Building dasm-linker.exe...
pyinstaller --onefile --name dasm-linker --distpath ..\bin Linker.py > nul 2>&1

echo Building RomGenerator.exe...
pyinstaller --onefile --name RomGenerator --distpath ..\bin RomGenerator.py > nul 2>&1

echo Building dasm-cc.exe...
pyinstaller --onefile --name dasm-cc --distpath ..\bin CCompiler.py > nul 2>&1

echo.
echo Cleaning up build artifacts...
rmdir /s /q build > nul 2>&1
del *.spec > nul 2>&1

echo.
echo ===========================================
echo Build complete!
echo.
echo EXE files created in: %~dp0bin\
echo.
echo To use these from anywhere on your PC:
echo 1. Add to PATH (Recommended):
echo    - Right-click 'This PC' ^> Properties
echo    - Click 'Advanced system settings'
echo    - Click 'Environment Variables...'
echo    - Under 'User variables', click 'New...'
echo    - Variable name: PATH
echo    - Variable value: %~dp0bin
echo    - Click OK
echo.
echo 2. Or copy the EXEs to a folder already in PATH
echo.
echo 3. Or create a shortcut on Desktop
echo ===========================================
pause
