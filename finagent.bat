@echo off
pushd "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "finagent.ps1"
pause
