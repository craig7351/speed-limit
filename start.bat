@echo off
cd /d "%~dp0"
echo Starting Bandwidth Limiter...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Program crashed or exited with error.
    pause
)
