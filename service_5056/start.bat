@echo off
cd /d "%~dp0"
call ..\venv\Scripts\activate.bat 2>nul || call venv\Scripts\activate.bat 2>nul
start "High-Precision Laser Server 5056" /min cmd /c "python app.py"
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5056/
