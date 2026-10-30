@echo off
setlocal
cd /d "%~dp0\.."
set "PYTHON=python"
where python >nul 2>nul || (echo Python 3.11+ is required.& pause& exit /b 1)

if not exist ".venv\Scripts\python.exe" (
  %PYTHON% -m venv .venv >nul 2>&1
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1

if not exist "frontend\dist\index.html" (echo Frontend build is missing.& pause& exit /b 1)

start "3D Print Manager Backend" /min cmd /c ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
set "URL=http://127.0.0.1:8000"
for /l %%i in (1,1,30) do (
  powershell -NoProfile -Command "try { iwr -UseBasicParsing http://127.0.0.1:8000/api/health | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 goto ready
  timeout /t 1 /nobreak >nul
)
echo Не удалось запустить сервер.
pause
exit /b 1

:ready
start "" "%URL%"
echo %URL%
endlocal
