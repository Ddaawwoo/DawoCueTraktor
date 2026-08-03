@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (
  echo Python nebyl nalezen.
  echo Pouzijte NAVOD_GIT_CZ.md a nechte EXE sestavit zdarma na GitHubu.
  pause
  exit /b 1
)

if not exist .venv (
  py -3.11 -m venv .venv
  if errorlevel 1 goto :error
)

.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error
.venv\Scripts\python.exe main.py
exit /b %errorlevel%

:error
echo Instalace nebo spusteni se nezdarilo.
pause
exit /b 1
