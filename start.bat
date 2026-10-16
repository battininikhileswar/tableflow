@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe goto run

set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD (
  where python >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
  if exist "%USERPROFILE%\Python311\python.exe" set "PY_CMD=%USERPROFILE%\Python311\python.exe"
)

if not defined PY_CMD (
  echo Python was not found. Please install Python or add it to PATH.
  pause
  exit /b 1
)

%PY_CMD% -m venv .venv
if errorlevel 1 (
  echo Could not create the environment. Check Python installation and retry.
  pause
  exit /b 1
)

:run
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and retry.
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8000 in your browser.
.venv\Scripts\python.exe run.py
pause
