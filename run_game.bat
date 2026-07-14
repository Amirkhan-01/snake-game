@echo off
REM Launch the desktop version of Snake Game.
REM Requires Python + dependencies (pip install -r requirements.txt).
cd /d "%~dp0"
python snake.py
if errorlevel 1 pause
