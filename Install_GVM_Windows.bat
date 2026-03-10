@echo off
TITLE GVM Setup Wizard

:: Always run from the repository root where this script lives
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===================================================
echo     GVM (AlphaHint Generator) - Auto-Installer
echo ===================================================
echo.

:: Check that uv sync has been run (the .venv directory should exist)
if not exist ".venv" (
    echo [ERROR] Project environment not found.
    echo Please run Install_CorridorKey_Windows.bat first!
    pause
    exit /b
)

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] uv is not available in this terminal session.
    echo Close this terminal, open a new one, and try again.
    pause
    exit /b
)

:: 1. Download Weights (all Python deps are already installed by uv sync)
echo [1/1] Downloading GVM Model Weights (approx. 6.5GB download)...
if not exist "gvm_core\weights" mkdir "gvm_core\weights"

echo Downloading GVM weights from HuggingFace...
uv run hf download geyongtao/gvm --local-dir gvm_core\weights
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download GVM weights.
    echo Ensure you have internet access and a valid HuggingFace session if required.
    pause
    exit /b
)

:: Verify required files are present (avoid silent partial installs)
set "MISSING_GVM_FILES="
for %%F in (
    "gvm_core\weights\vae\config.json"
    "gvm_core\weights\vae\diffusion_pytorch_model.safetensors"
    "gvm_core\weights\scheduler\scheduler_config.json"
    "gvm_core\weights\unet\config.json"
    "gvm_core\weights\unet\diffusion_pytorch_model.safetensors"
) do (
    if not exist %%~F (
        echo [ERROR] Missing required GVM file: %%~F
        set "MISSING_GVM_FILES=1"
    )
)

if defined MISSING_GVM_FILES (
    echo.
    echo [ERROR] GVM install incomplete. Re-run this script and make sure the download finishes.
    echo         You may also need to free disk space or authenticate to HuggingFace.
    pause
    exit /b
)

echo [INFO] GVM weights verified.

echo.
echo ===================================================
echo   GVM Setup Complete!
echo ===================================================
pause
