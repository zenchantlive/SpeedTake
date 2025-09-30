param(
    [string]$EntryPoint = "audio.py",
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Python = Join-Path $projectRoot ".venv/Scripts/python.exe" # Use the venv python

Push-Location $projectRoot
try {
    if (-not (Test-Path $Python)) {
        Write-Error "Python executable not found at $Python. Please create the virtual environment."
        exit 1
    }

    # Install dependencies from requirements.txt
    if (Test-Path "requirements.txt") {
        Write-Host "Installing dependencies from requirements.txt..."
        & $Python -m pip install -r requirements.txt
    }

    # Check if PyInstaller is installed, and install if not
    & $Python -m PyInstaller --version 2>$null 1>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller not found in the virtual environment. Installing..."
        & $Python -m pip install pyinstaller
    }

    if ($Clean) {
        Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
        Remove-Item SpeedTake.spec -ErrorAction SilentlyContinue
    }

    $ffmpegPath = "C:\Users\Zenchant\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
    $arguments = @(
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name","SpeedTake",
        "--add-binary","$ffmpegPath;.",
        "--hidden-import","yt_dlp",
        $EntryPoint
    )

    & $Python -m PyInstaller @arguments

    $outputDir = Join-Path $projectRoot "dist"
    $outputPath = Join-Path $outputDir "AudioExtractor.exe"
    if (Test-Path $outputPath) {
        Write-Host "Executable created at $outputPath"
    } else {
        Write-Warning "PyInstaller finished but the expected executable was not found."
    }
} finally {
    Pop-Location
}
