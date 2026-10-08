@echo off
cd /d "%~dp0"
if exist "%~dp0dist\JARVIS\JARVIS.exe" (
    cd /d "%~dp0dist\JARVIS"
    start "" "%~dp0dist\JARVIS\JARVIS.exe"
) else (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
)
