@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo Run setup.bat first.
  pause
  exit /b 1
)
cd /d "%~dp0backend"
echo Starting DBL AssetHub at http://localhost:8000
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
