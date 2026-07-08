@echo off
setlocal enabledelayedexpansion

echo =================================== FinAgent Backend (Local) ===================================

:: Get script directory
cd /d "%~dp0"

:: ==================================== 1. Check/Install Virtual Environment ====================================
echo.
echo [1/5] Checking virtual environment...

set "VENV_DIR=finagent"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

if not exist "%VENV_ACTIVATE%" (
    echo   Virtual environment not found. Creating...
    pip install virtualenv -q
    virtualenv -p python "%VENV_DIR%"
    echo   [OK] Virtual environment created
) else (
    echo   [OK] Virtual environment found
)

:: Activate virtual environment
call "%VENV_ACTIVATE%"

:: ==================================== 2. Install/Update Dependencies ====================================
echo.
echo [2/5] Installing dependencies...

pip install -r requirements.txt -q
echo   [OK] Python dependencies installed

:: Build frontend
echo.
echo   Building frontend...
if exist "web\package.json" (
    cd web
    echo   Cleaning old build files...
    if exist dist rmdir /s /q dist
    if exist node_modules\.vite rmdir /s /q node_modules\.vite
    echo   Installing npm dependencies...
    call npm install 2>nul
    echo   Running build...
    call npm run build
    if exist dist (
        echo   [OK] Frontend built successfully
    ) else (
        echo   [ERROR] Frontend build failed
    )
    cd ..
) else (
    echo   [WARNING] web\package.json not found, skipping frontend build
)

:: ==================================== 3. Check/Install Docker & Qdrant ====================================
echo.
echo [3/5] Checking Docker and Qdrant...

:: Check if Qdrant is already running
curl -s http://localhost:6333/health >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [OK] Qdrant is already running
) else (
    docker --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo   Docker found. Starting Qdrant...
        docker pull qdrant/qdrant:1.16.0 -q 2>nul
        docker stop qdrant-finagent 2>nul
        docker rm qdrant-finagent 2>nul
        docker run -d --name qdrant-finagent -p 6333:6333 -p 6334:6334 qdrant/qdrant:1.16.0 2>nul
        timeout /t 2 /nobreak >nul
        curl -s http://localhost:6333/health >nul 2>&1
        if %ERRORLEVEL% equ 0 (
            echo   [OK] Qdrant started successfully
        ) else (
            echo   [WARNING] Qdrant failed to start. Memory features will be limited.
        )
    ) else (
        echo   [WARNING] Docker not found. Memory features will be limited.
    )
)

:: ==================================== 4. Check Environment Variables ====================================
echo.
echo [4/5] Checking environment variables...

if defined ZENMUX_API_KEY (
    echo   [OK] ZENMUX_API_KEY is set
) else (
    if exist "config\.env" (
        for /f "tokens=1,* delims==" %%a in ('findstr /v "^#" config\.env') do (
            set "%%a=%%b"
        )
    )
    if defined FINAGENT_ZENMUX_API_KEY (
        set "ZENMUX_API_KEY=!FINAGENT_ZENMUX_API_KEY!"
        echo   [OK] ZENMUX_API_KEY set from FINAGENT_ZENMUX_API_KEY
    ) else (
        echo   [ERROR] ZENMUX_API_KEY is not set
        exit /b 1
    )
)

if defined AGNES_API_KEY (
    echo   [OK] AGNES_API_KEY is set
) else (
    echo   [WARNING] AGNES_API_KEY is not set ^(optional^)
)

if defined NVIDIA_API_KEY (
    echo   [OK] NVIDIA_API_KEY is set
) else (
    echo   [WARNING] NVIDIA_API_KEY is not set ^(optional^)
)

:: ==================================== 5. Stop Existing Server & Start New ====================================
echo.
echo [5/5] Checking port...

:: Check if port 8000 is in use
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [WARNING] Port 8000 is already in use. Stopping existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        taskkill /PID %%a /F 2>nul
    )
    timeout /t 2 /nobreak >nul
    echo   [OK] Existing process stopped
)

:: ==================================== Start Server ====================================
echo.
echo =================================== Starting Local Server ===================================
echo   Access URL: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo.

python finagent_api.py
