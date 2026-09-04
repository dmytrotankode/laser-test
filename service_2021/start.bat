@echo off
chcp 65001 >nul
title Доведення 2021
cd /d "%~dp0"

rem На робочому місці оператора - власний "venv" поруч (python -m venv venv +
rem pip install -r requirements.txt), там немає сусідньої папки service_5056.
rem На машині розробника - навпаки, є спільний venv. Той самий файл працює
rem в обох місцях без правок.
set PY=venv\Scripts\python.exe
if not exist "%PY%" set PY=..\service_5056\venv\Scripts\python.exe

echo Запускаю сервер...
start "Доведення 2021 - не закривати" "%PY%" app.py

timeout /t 3 /nobreak >nul
start "" http://localhost:2021

echo.
echo Відкрив http://localhost:2021 у браузері.
echo Тримайте вікно "Доведення 2021" відкритим, поки працюєте.
echo Це вікно можна закрити.
timeout /t 5
