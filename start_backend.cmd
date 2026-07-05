@echo off
setlocal enabledelayedexpansion

echo =================================== FinAgent Backend (Production) ===================================

:: Get script directory
cd /d "%~dp0"

:: =================================== 1. Check/Install Virtual Environment ===================================
echo.
echo [1/4] Checking virtual environment...

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

:: =================================== 2. Install/Update Dependencies ===================================
echo.
echo [2/4] Installing dependencies...

pip install -r requirements.txt -q
echo   [OK] Dependencies installed

:: =================================== 3. Check/Install Vector DB (Qdrant) ===================================
echo.
echo [3/4] Checking vector database (Qdrant)...

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

:: =================================== 4. Check Environment Variables ===================================
echo.
echo [4/4] Checking environment variables...

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

:: =================================== Start Server ===================================
echo.
echo =================================== Starting Production Server ===================================
gunicorn -w 2 -k uvicorn.workers.UvicornWorker finagent_api:app --bind 0.0.0.0:8000 --timeout 480 --log-level debug
