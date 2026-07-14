@echo off
REM Play the web version locally. It's plain HTML5/JavaScript - works in any
REM browser, no build needed. This starts a small server (so localStorage and
REM phone testing work) and opens it in your default browser.
cd /d "%~dp0"
start "" http://localhost:8000/
python serve.py
pause
