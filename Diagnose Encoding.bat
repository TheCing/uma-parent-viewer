@echo off
chcp 65001 >nul 2>&1
echo Running encoding diagnostic...
echo.
python diagnose_encoding.py
if errorlevel 1 (
    echo.
    echo Python not found or script failed.
    echo Make sure Python is installed and in your PATH.
    pause
)
