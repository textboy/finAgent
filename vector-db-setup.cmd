@echo off
echo Starting Qdrant vector DB via Docker (Windows native)...
docker pull qdrant/qdrant:1.16.0
docker stop qdrant-finagent 2>nul
docker rm qdrant-finagent 2>nul
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:1.16.0
@REM docker run -d --name qdrant-finagent -p 6333:6333 -p 6334:6334 -v "%CD%\qdrant_storage:/qdrant/storage" qdrant/qdrant:1.16.0
if %ERRORLEVEL% neq 0 (
    echo Docker error. Ensure Docker Desktop running. Fallback to local Qdrant (no server).
    echo No action needed - code uses local by default.
) else (
    echo Monitor Qdrant server at http://localhost:6333/dashboard
    echo Add QDRANT_URL=http://localhost:6333 to config/.env
    echo check collection by http://10.192.237.16:6333/collections/finagent_reports
)
pause