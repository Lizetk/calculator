@echo off
cd /d "%~dp0\.."
where node >nul 2>nul || (echo Node.js 20+ is required.& pause& exit /b 1)
cd frontend
call npm install
call npm run build
pause
