@echo off
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
python -m apps.grok_local_agent.run_agent
