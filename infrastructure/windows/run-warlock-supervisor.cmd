@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "RUNTIME_DIR=%PROJECT_ROOT%\.warlock\runtime"

if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"

"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%SCRIPT_DIR%warlock-supervisor.ps1" >> "%RUNTIME_DIR%\bootstrap.log" 2>&1

exit /b %errorlevel%
