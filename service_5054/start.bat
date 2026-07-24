@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
start "Laser Pipeline Server 5054" /min cmd /c "python app.py"
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5054/
