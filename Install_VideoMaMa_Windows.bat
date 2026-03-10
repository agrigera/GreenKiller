@echo off
TITLE VideoMaMa Setup Wizard

:: Always run from the repository root where this script lives
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===================================================
echo   VideoMaMa (AlphaHint Generator) - Auto-Installer
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
echo [1/2] Downloading VideoMaMa fine-tuned weights...
if not exist "VideoMaMaInferenceModule\checkpoints\VideoMaMa" mkdir "VideoMaMaInferenceModule\checkpoints\VideoMaMa"

echo Downloading VideoMaMa weights from HuggingFace...
uv run hf download SammyLim/VideoMaMa --local-dir VideoMaMaInferenceModule\checkpoints\VideoMaMa
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download VideoMaMa fine-tuned weights.
    pause
    exit /b
)

echo.
echo [2/2] Downloading Stable Video Diffusion base components...
if not exist "VideoMaMaInferenceModule\checkpoints\stable-video-diffusion-img2vid-xt" mkdir "VideoMaMaInferenceModule\checkpoints\stable-video-diffusion-img2vid-xt"

echo NOTE: This requires acceptance of the StabilityAI model license on HuggingFace.
uv run hf download stabilityai/stable-video-diffusion-img2vid-xt --local-dir VideoMaMaInferenceModule\checkpoints\stable-video-diffusion-img2vid-xt --include "feature_extractor/*" "image_encoder/*" "vae/*" "model_index.json"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download Stable Video Diffusion base components.
    echo Make sure you accepted the model license on HuggingFace first.
    pause
    exit /b
)

echo.
echo ===================================================
echo   VideoMaMa Setup Complete!
echo ===================================================
pause
