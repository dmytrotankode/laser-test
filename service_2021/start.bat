@echo off
title Dovodka LS - service_2021
cd /d "%~dp0service_2021"

echo Starting server...
start "Dovodka LS - do not close" "..\service_5056\venv\Scripts\python.exe" app.py

timeout /t 3 /nobreak >nul
start "" http://localhost:2021

echo.
echo Opened http://localhost:2021 in browser.
echo Keep the "Dovodka LS" window open while you use it.
echo This window can be closed.
timeout /t 5
