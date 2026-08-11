@echo off
cd /d "%~dp0"
call ..\service_5056\venv\Scripts\activate.bat 2>nul
start "Service 3030 - line marking" /min cmd /c "python app.py"
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:3030/
