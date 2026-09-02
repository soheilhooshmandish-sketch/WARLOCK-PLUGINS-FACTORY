@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Warlock virtual environment not found.
    exit /b 1
)

echo Starting Warlock Local Agent...

".venv\Scripts\python.exe" -m apps.local_agent.run_agent

endlocal
