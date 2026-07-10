#!/bin/bash

# Setup systemd environment file for FinAgent
# Run this to export API keys from your shell to systemd

echo "=== Setting up systemd environment ==="

# Create directory
sudo mkdir -p /etc/finagent

# Generate env file from current user's environment
cat > /tmp/finagent-env << EOF
# FinAgent Environment Variables
# Generated from $(whoami)'s environment on $(date)
# Re-run: sudo ./setup-service-env.sh

FINAGENT_ZENMUX_API_KEY=${FINAGENT_ZENMUX_API_KEY:-}
ZENMUX_API_KEY=${ZENMUX_API_KEY:-}
AGNES_API_KEY=${AGNES_API_KEY:-}
NVIDIA_API_KEY=${NVIDIA_API_KEY:-}
EOF

# Copy to system location
sudo cp /tmp/finagent-env /etc/finagent/env
sudo chmod 600 /etc/finagent/env
sudo chown root:root /etc/finagent/env

rm /tmp/finagent-env

echo ""
echo "✅ Environment file created: /etc/finagent/env"
echo ""
echo "API keys found:"
[ -n "$FINAGENT_ZENMUX_API_KEY" ] && echo "  ✅ FINAGENT_ZENMUX_API_KEY" || echo "  ⚠️  FINAGENT_ZENMUX_API_KEY not set"
[ -n "$ZENMUX_API_KEY" ] && echo "  ✅ ZENMUX_API_KEY" || echo "  ⚠️  ZENMUX_API_KEY not set"
[ -n "$AGNES_API_KEY" ] && echo "  ✅ AGNES_API_KEY" || echo "  ⚠️  AGNES_API_KEY not set"
[ -n "$NVIDIA_API_KEY" ] && echo "  ✅ NVIDIA_API_KEY" || echo "  ⚠️  NVIDIA_API_KEY not set (optional)"
echo ""
echo "Next steps:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl restart finagent"
