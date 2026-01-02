@echo off
call conda activate finagent
if %ERRORLEVEL% neq 0 (
    echo Please run setup.cmd first to create the environment.
    pause
    exit /b 1
)
python finagent.py %*
pause