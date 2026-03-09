@echo off
title BotBoundary Setup
color 0A

echo.
echo  ========================================
echo   BotBoundary - CacheMeOutside Setup
echo  ========================================
echo.

REM ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo         Download it from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo [OK] Python found.

REM ── Check Node.js ─────────────────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found.
    echo         Download it from https://nodejs.org/  (LTS version)
    pause
    exit /b 1
)
echo [OK] Node.js found.

echo.
echo  ----------------------------------------
echo   Step 1/3 - Setting up Python backend
echo  ----------------------------------------
echo.

cd /d "%~dp0Model\login_auth"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists, skipping.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] pip install failed. Check your internet connection and try again.
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed.

echo.
echo  ----------------------------------------
echo   Step 2/3 - Setting up React frontend
echo  ----------------------------------------
echo.

cd /d "%~dp0FrontEnd"

echo Installing Node dependencies...
call npm install

if errorlevel 1 (
    echo [ERROR] npm install failed. Check your internet connection and try again.
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed.

echo.
echo  ----------------------------------------
echo   Step 3/3 - Launching both servers
echo  ----------------------------------------
echo.
echo  Backend  ->  http://localhost:8000
echo  Frontend ->  http://localhost:5173
echo  API docs ->  http://localhost:8000/docs
echo.
echo  Two terminal windows will open.
echo  Close them to stop the servers.
echo.
pause

REM ── Start backend in a new window ─────────────────────────────────────────────
start "BotBoundary Backend" cmd /k "cd /d "%~dp0Model\login_auth" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

REM ── Small delay so backend starts first ───────────────────────────────────────
timeout /t 3 /nobreak >nul

REM ── Start frontend in a new window ───────────────────────────────────────────
start "BotBoundary Frontend" cmd /k "cd /d "%~dp0FrontEnd" && npm run dev"

echo.
echo  [OK] Both servers are starting up!
echo  Open your browser to http://localhost:5173
echo.
pause
