#!/bin/bash

echo "=================================== FinAgent Backend (Local) ==================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo "❌ Failed to change directory"; exit 1; }

# ==================================== 1. Check/Install Virtual Environment ====================================
echo ""
echo "[1/5] Checking virtual environment..."

VENV_DIR="finagent"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "  Virtual environment not found. Creating..."
    python3 -m venv "$VENV_DIR" 2>/dev/null || {
        pip install virtualenv -q
        virtualenv -p python3 "$VENV_DIR"
    }
    echo "  ✅ Virtual environment created"
else
    echo "  ✅ Virtual environment found"
fi

# Activate virtual environment
source "$VENV_ACTIVATE" || { echo "❌ Failed to activate virtual environment"; exit 1; }

# ==================================== 2. Install/Update Dependencies ====================================
echo ""
echo "[2/5] Installing dependencies..."

pip install -r requirements.txt -q 2>/dev/null || {
    echo "  ⚠️  Some dependencies may have failed to install"
}
echo "  ✅ Python dependencies installed"

# Build frontend
echo ""
echo "  Building frontend..."
if [ -f "$SCRIPT_DIR/web/package.json" ]; then
    cd "$SCRIPT_DIR/web" || { echo "  ❌ Cannot access web directory"; }
    echo "  Working directory: $(pwd)"

    # Clean old build
    echo "  Cleaning old build files..."
    rm -rf dist node_modules/.vite 2>/dev/null || true

    # Install dependencies
    echo "  Installing npm dependencies..."
    npm install 2>&1 | tail -3

    # Build
    echo "  Running build..."
    npm run build 2>&1

    if [ -d "dist" ]; then
        echo "  ✅ Frontend built successfully"
    else
        echo "  ❌ Frontend build failed - dist directory not created"
    fi
    cd "$SCRIPT_DIR"
else
    echo "  ⚠️  web/package.json not found, skipping frontend build"
fi

# ==================================== 3. Check/Install Docker & Qdrant ====================================
echo ""
echo "[3/5] Checking Docker and Qdrant..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "  Docker not found. Installing..."
    if command -v apt-get &> /dev/null; then
        apt-get update -qq 2>/dev/null || true
        apt-get install -y -qq docker.io 2>/dev/null || {
            echo "  ⚠️  Could not install Docker automatically"
        }
    fi
    if command -v docker &> /dev/null; then
        echo "  ✅ Docker installed"
    fi
fi

# Check if Qdrant is already running
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "  ✅ Qdrant is already running"
elif command -v docker &> /dev/null; then
    echo "  Starting Qdrant..."
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
echo "[4/5] Checking environment variables..."

# Load from .env file if exists
if [ -f "$SCRIPT_DIR/config/.env" ]; then
    set -a
    source "$SCRIPT_DIR/config/.env" 2>/dev/null || true
    set +a
fi

if [ -n "$FINAGENT_ZENMUX_API_KEY" ]; then
    export ZENMUX_API_KEY="$FINAGENT_ZENMUX_API_KEY"
    echo "  ✅ ZENMUX_API_KEY set from FINAGENT_ZENMUX_API_KEY"
elif [ -n "$ZENMUX_API_KEY" ]; then
    echo "  ✅ ZENMUX_API_KEY is set"
else
    echo "  ❌ ZENMUX_API_KEY is not set"
    echo "  Set it with: export FINAGENT_ZENMUX_API_KEY=your-key"
    exit 1
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

# ==================================== 5. Setup Systemd Service (if running as root) ====================================
echo ""
echo "[5/5] Checking systemd service..."

if [ "$EUID" -eq 0 ]; then
    # Running as root - setup systemd service
    SERVICE_FILE="finagent.service"
    if [ -f "$SCRIPT_DIR/$SERVICE_FILE" ]; then
        cp "$SCRIPT_DIR/$SERVICE_FILE" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable finagent 2>/dev/null || true
        echo "  ✅ Systemd service configured"
        echo ""
        echo "  To set API keys for the service:"
        echo "    sudo systemctl import-environment ZENMUX_API_KEY"
        echo "    sudo systemctl import-environment AGNES_API_KEY"
        echo "    sudo systemctl import-environment NVIDIA_API_KEY"
    fi
else
    echo "  ⏭️  Skipping systemd setup (not running as root)"
fi

# ==================================== Stop Existing Server & Start New ====================================
echo ""
echo "Stopping existing server..."

# Stop existing server if running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "  ⚠️  Port 8000 is already in use. Stopping existing process..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "  ✅ Existing process stopped"
fi

# ==================================== Start Server ====================================
echo ""
echo "=================================== Starting Local Server ==================================="
echo "  🌐 Access URL: http://localhost:8000"
echo "  📊 API Docs: http://localhost:8000/docs"
echo "  Press Ctrl+C to stop"
echo ""

python finagent_api.py
