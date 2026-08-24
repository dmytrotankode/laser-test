@echo off
title Generation LS - service_3030
cd /d "%~dp0service_3030"

echo Starting server...
start "Generation LS - do not close" "..\service_5056\venv\Scripts\python.exe" production_app.py

timeout /t 3 /nobreak >nul
start "" http://localhost:3031

echo.
echo Opened http://localhost:3031 in browser.
echo Keep the "Generation LS" window open while you use it.
echo This window can be closed.
timeout /t 5
