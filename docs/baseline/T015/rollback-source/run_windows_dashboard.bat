@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo No Python environment. See README.md to install requirements.
  pause
  exit /b 1
)
if not exist "app\static\index.html" (
  echo Dashboard not built. Run: npm --prefix frontend install
  echo Then: npm --prefix frontend run build
  pause
  exit /b 1
)
if "%MODEL_PATH%"=="" (
  echo Please enter your full ViSoBERT folder path on this computer:
  set /p MODEL_PATH=MODEL_PATH:
)
echo Starting local dashboard: http://127.0.0.1:8000/dashboard/
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
