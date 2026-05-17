# Build script to convert DevTools Python files to EXEs using PyInstaller

Write-Host "Installing PyInstaller and dependencies..."
pip install pyinstaller pillow -q

Write-Host ""
Write-Host "Building EXE files..."
Push-Location "$PSScriptRoot/DevTools"

# Source file -> output exe name. Source on the left, output (without .exe) on the right.
$tools = @(
    @{ Source = "Compiler";       Output = "dasm" },
    @{ Source = "ImageConverter"; Output = "ImageConverter" },
    @{ Source = "Linker";         Output = "dasm-linker" },
    @{ Source = "RomGenerator";   Output = "RomGenerator" },
    @{ Source = "CCompiler";      Output = "dasm-cc" }
)

foreach ($tool in $tools) {
    Write-Host "Building $($tool.Output).exe..."
    pyinstaller --onefile --name $tool.Output --distpath ../bin "$($tool.Source).py" 2>&1 | Out-Null
}

Write-Host ""
Write-Host "Cleaning up build artifacts..."
Remove-Item -Path "build", "*.spec" -Force -ErrorAction SilentlyContinue

Pop-Location

Write-Host ""
Write-Host "==========================================="
Write-Host "Build complete!"
Write-Host ""
Write-Host "EXE files created in: $(Resolve-Path "$PSScriptRoot/bin")"
Write-Host ""
Write-Host "To use these from anywhere on your PC:"
Write-Host ""
Write-Host "Option 1: Add to PATH (Recommended)"
Write-Host "  `$ExePath = '$(Resolve-Path "$PSScriptRoot/bin")'`"
Write-Host "  `[Environment]::SetEnvironmentVariable('PATH', `$env:PATH + ';' + `$ExePath, 'User')`"
Write-Host ""
Write-Host "Option 2: Run this command to add to PATH automatically:"
$addToPathCmd = "`$env:PATH += ';$(Resolve-Path "$PSScriptRoot/bin")'`"
Write-Host "  $addToPathCmd"
Write-Host ""
Write-Host "==========================================="
