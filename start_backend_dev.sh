#!/bin/bash
set -e

echo "=================================== FinAgent Backend (Development) ==================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ==================================== 1. Check/Install Virtual Environment ====================================
echo ""
echo "[1/4] Checking virtual environment..."

VENV_DIR="finagent"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "  Virtual environment not found. Creating..."
    pip install virtualenv -q
    virtualenv -p python3 "$VENV_DIR"
    echo "  ✅ Virtual environment created"
else
    echo "  ✅ Virtual environment found"
fi

# Activate virtual environment
source "$VENV_ACTIVATE"

# ==================================== 2. Install/Update Dependencies ====================================
echo ""
echo "[2/4] Installing dependencies..."

pip install -r requirements.txt -q
echo "  ✅ Dependencies installed"

# ==================================== 3. Check/Install Vector DB (Qdrant) ====================================
echo ""
echo "[3/4] Checking vector database (Qdrant)..."

# Check if Qdrant is already running
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "  ✅ Qdrant is already running"
elif command -v docker &> /dev/null; then
    echo "  Docker found. Starting Qdrant..."
    docker pull qdrant/qdrant:1.16.0 -q 2>/dev/null || true
    docker stop qdrant-finagent 2>/dev/null || true
    docker rm qdrant-finagent 2>/dev/null || true
    docker run -d --name qdrant-finagent -p 6333:6333 -p 6334:6334 qdrant/qdrant:1.16.0 2>/dev/null
    sleep 2
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo "  ✅ Qdrant started successfully"
    else
        echo "  ⚠️  Qdrant failed to start. Memory features will be limited."
    fi
else
    echo "  ⚠️  Docker not found. Memory features will be limited."
fi

# ==================================== 4. Check Environment Variables ====================================
echo ""
echo "[4/4] Checking environment variables..."

if [ -n "$ZENMUX_API_KEY" ]; then
    echo "  ✅ ZENMUX_API_KEY is set"
else
    if [ -f "$SCRIPT_DIR/config/.env" ]; then
        export $(grep -v '^#' "$SCRIPT_DIR/config/.env" | xargs) 2>/dev/null || true
    fi
    if [ -n "$FINAGENT_ZENMUX_API_KEY" ]; then
        export ZENMUX_API_KEY="$FINAGENT_ZENMUX_API_KEY"
        echo "  ✅ ZENMUX_API_KEY set from FINAGENT_ZENMUX_API_KEY"
    else
        echo "  ❌ ZENMUX_API_KEY is not set"
        exit 1
    fi
fi

if [ -n "$AGNES_API_KEY" ]; then
    echo "  ✅ AGNES_API_KEY is set"
else
    echo "  ⚠️  AGNES_API_KEY is not set (optional)"
fi

if [ -n "$NVIDIA_API_KEY" ]; then
    echo "  ✅ NVIDIA_API_KEY is set"
else
    echo "  ⚠️  NVIDIA_API_KEY is not set (optional)"
fi

# ==================================== Start Server ====================================
echo ""
echo "=================================== Starting Development Server ==================================="
exec python finagent_api.py
