@echo off
echo Starting Qdrant MCP server via Docker (Windows native)...
docker pull qdrant/qdrant:latest
docker stop qdrant-finagent 2>nul
docker rm qdrant-finagent 2>nul
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
@REM docker run -d --name qdrant-finagent -p 6333:6333 -p 6334:6334 -v "%CD%\qdrant_storage:/qdrant/storage" qdrant/qdrant:latest
if %ERRORLEVEL% neq 0 (
    echo Docker error. Ensure Docker Desktop running. Fallback to local Qdrant (no server).
    echo No action needed - code uses local by default.
) else (
    echo Monitor Qdrant server at http://localhost:6333/dashboard
    echo Add QDRANT_URL=http://localhost:6333 to config/.env
)
pause