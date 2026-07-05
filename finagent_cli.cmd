@echo off
pushd "%~dp0"

echo ==================================== FinAgent CLI ===================================

:: 1. Prompt for Symbol
set /p SYMBOL="Enter stock symbol (e.g., GOOG): "
if "%SYMBOL%"=="" (
    echo Error: Symbol cannot be empty.
    pause
    exit /b 1
)

:: 2. Selectable Menu for Period
echo.
echo Select Period:
echo   1^) short+  ^(within 2 weeks^)
echo   2^) short   ^(2 weeks to 1 month^)
echo   3^) medium  ^(1 month to 1 year^)
echo   4^) long    ^(1 year to 2 years^)
echo.
set /p CHOICE="Enter option [1-4]: "

if "%CHOICE%"=="1" set PERIOD=short+
if "%CHOICE%"=="2" set PERIOD=short
if "%CHOICE%"=="3" set PERIOD=medium
if "%CHOICE%"=="4" set PERIOD=long
if "%PERIOD%"=="" (
    echo Invalid selection. Exiting.
    pause
    exit /b 1
)

:: 3. Activate environment and run
echo.
echo Activating conda environment...
call conda activate finagent
if %ERRORLEVEL% neq 0 (
    echo Error: Run setup first to create 'finagent' environment.
    pause
    exit /b 1
)

echo Running FinAgent for %SYMBOL% (%PERIOD%)...
echo.
python finagent_cli.py --symbol %SYMBOL% --period %PERIOD%

echo.
echo Finished.
pause
