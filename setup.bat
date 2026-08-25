@echo off
setlocal
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip || exit /b 1
python -m pip install --cache-dir .pip-cache -r backend\requirements.txt || exit /b 1
pushd backend
python -m alembic upgrade head
if errorlevel 1 (
  popd
  exit /b 1
)
popd
echo Setup complete. Copy .env.example to .env and use start.bat.
