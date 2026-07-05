#!/bin/bash
set -e

# Detect mode from config or argument
RUN_MODE="${1:-production}"

echo "=================================== FinAgent Backend ($RUN_MODE) ==================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ==================================== 1. Check/Install Virtual Environment ====================================
echo ""
echo "[1/5] Checking virtual environment..."

VENV_DIR="finagent"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "  Virtual environment not found. Creating..."
    python3 -m venv "$VENV_DIR" || {
        apt-get update -qq && apt-get install -y -qq python3 python3-venv
        python3 -m venv "$VENV_DIR"
    }
    echo "  ✅ Virtual environment created"
else
    echo "  ✅ Virtual environment found"
fi

# Activate virtual environment
source "$VENV_ACTIVATE"

# ==================================== 2. Install/Update Dependencies ====================================
echo ""
echo "[2/5] Installing dependencies..."

pip install -r requirements.txt -q
echo "  ✅ Dependencies installed"

# ==================================== 3. Check/Install Docker & Qdrant ====================================
echo ""
echo "[3/5] Checking Docker and Qdrant..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "  Docker not found. Installing..."
    apt-get update -qq
    apt-get install -y -qq docker.io
    systemctl enable docker
    systemctl start docker
    echo "  ✅ Docker installed"
fi

# Check if Qdrant is already running
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "  ✅ Qdrant is already running"
else
    echo "  Starting Qdrant..."
    docker pull qdrant/qdrant:1.16.0 -q 2>/dev/null || true
    docker stop qdrant-finagent 2>/dev/null || true
    docker rm qdrant-finagent 2>/dev/null || true
    docker run -d --name qdrant-finagent -p 6333:6333 -p 6334:6334 qdrant/qdrant:1.16.0
    sleep 2
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo "  ✅ Qdrant started successfully"
    else
        echo "  ⚠️  Qdrant failed to start. Memory features will be limited."
    fi
fi

# ==================================== 4. Check Environment Variables ====================================
echo ""
echo "[4/5] Checking environment variables..."

# Load from .env file if exists
if [ -f "$SCRIPT_DIR/config/.env" ]; then
    set -a
    source "$SCRIPT_DIR/config/.env"
    set +a
fi

if [ -n "$ZENMUX_API_KEY" ]; then
    echo "  ✅ ZENMUX_API_KEY is set"
else
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
        echo ""
        echo "  Or create /etc/finagent/env:"
        echo "    sudo mkdir -p /etc/finagent"
        echo "    sudo tee /etc/finagent/env << 'EOF'"
        echo "    ZENMUX_API_KEY=your-key"
        echo "    AGNES_API_KEY=your-key"
        echo "    NVIDIA_API_KEY=your-key"
        echo "    EOF"
    fi
else
    echo "  ⏭️  Skipping systemd setup (not running as root)"
    echo "  Note: Run with sudo to configure systemd service"
fi

# ==================================== Start Server ====================================
echo ""
echo "=================================== Starting Production Server ==================================="
echo "  API: http://localhost:8000"
echo "  Logs: journalctl -u finagent -f (if running as service)"
echo ""

# Trap signals to keep terminal alive
trap 'echo ""; echo "Server stopped."; exit 0' INT TERM

# Check if we should run as systemd service or directly
if [ "$EUID" -eq 0 ] && systemctl is-active --quiet finagent 2>/dev/null; then
    echo "  Starting as systemd service..."
    echo "  Use 'sudo systemctl status finagent' to check status"
    echo "  Use 'sudo journalctl -u finagent -f' to view logs"
    echo ""
    systemctl start finagent
    echo "  Service started. Running in background."
    echo "  Press Ctrl+C to exit this terminal (service will keep running)."
    wait
else
    echo "  Starting directly... (Press Ctrl+C to stop)"
    echo ""
    gunicorn -w 2 -k uvicorn.workers.UvicornWorker finagent_api:app --bind 0.0.0.0:8000 --timeout 480 --log-level info
fi
