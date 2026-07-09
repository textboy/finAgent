#!/bin/bash

# HTTPS Setup with Let's Encrypt for FinAgent
# Run on production server as root

DOMAIN="${1:-5ngc.s.time4vps.cloud}"
EMAIL="${2:-}"

echo "=================================== HTTPS Setup ($DOMAIN) ==================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo ./setup-https.sh $DOMAIN [email]"
    exit 1
fi

# Install nginx if not present
if ! command -v nginx &> /dev/null; then
    echo ""
    echo "[1/4] Installing nginx..."
    apt-get update -qq
    apt-get install -y -qq nginx
    echo "  ✅ Nginx installed"
else
    echo "  ✅ Nginx already installed"
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo ""
    echo "[2/4] Installing certbot..."
    apt-get install -y -qq certbot python3-certbot-nginx
    echo "  ✅ Certbot installed"
else
    echo "  ✅ Certbot already installed"
fi

# Configure nginx reverse proxy
echo ""
echo "[3/4] Configuring nginx..."

# Create directory if it doesn't exist
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

# Check if finagent config already exists
if [ -f /etc/nginx/sites-available/finagent ]; then
    echo "  ✅ Existing nginx config found, will add SSL with certbot"
else
    # Create new HTTP-only config (certbot will add SSL)
    cat > /etc/nginx/sites-available/finagent << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
EOF
    echo "  ✅ New nginx config created"
fi

# Enable site
ln -sf /etc/nginx/sites-available/finagent /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Temporarily use HTTP-only config for certbot
if grep -q "listen 443 ssl" /etc/nginx/sites-available/finagent; then
    echo "  Temporarily switching to HTTP-only for certificate setup..."
    cp /etc/nginx/sites-available/finagent /etc/nginx/sites-available/finagent.bak
    # Create HTTP-only version for certbot
    cat > /etc/nginx/sites-available/finagent << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
EOF
fi

# Test nginx config
echo "  Testing nginx config..."
if ! nginx -t 2>&1; then
    echo "  ❌ Nginx config test failed"
    # Restore backup if exists
    [ -f /etc/nginx/sites-available/finagent.bak ] && mv /etc/nginx/sites-available/finagent.bak /etc/nginx/sites-available/finagent
    exit 1
fi

systemctl reload nginx
echo "  ✅ Nginx configured"

# Get SSL certificate using standalone mode (more reliable)
echo ""
echo "[4/4] Obtaining SSL certificate..."

# Stop nginx temporarily for standalone mode
systemctl stop nginx 2>/dev/null || true

if [ -n "$EMAIL" ]; then
    certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"
else
    certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email
fi

CERTBOT_EXIT=$?

# Restart nginx
systemctl start nginx 2>/dev/null || true

if [ $CERTBOT_EXIT -eq 0 ]; then
    echo "  ✅ SSL certificate obtained"
    rm -f /etc/nginx/sites-available/finagent.bak

    # Configure nginx with SSL
    cat > /etc/nginx/sites-available/finagent << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
EOF
    systemctl reload nginx
    echo "  ✅ Nginx configured with SSL"
else
    echo "  ⚠️  SSL certificate failed. Try: certbot certonly --standalone -d $DOMAIN"
    [ -f /etc/nginx/sites-available/finagent.bak ] && mv /etc/nginx/sites-available/finagent.bak /etc/nginx/sites-available/finagent
    systemctl reload nginx
fi

# Setup auto-renewal
echo ""
echo "Setting up auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer
echo "  ✅ Auto-renewal configured"

# Update gunicorn to bind to localhost (nginx handles external traffic)
echo ""
echo "⚠️  Important: Update start_server.sh to bind gunicorn to 127.0.0.1:8000"
echo "   (nginx will proxy external traffic to gunicorn)"
echo ""
echo "=================================== Setup Complete ==================================="
echo ""
echo "  🌐 HTTPS URL: https://$DOMAIN"
echo "  📊 API Docs: https://$DOMAIN/docs"
echo ""
echo "  Test SSL: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo "  Renew cert: certbot renew --dry-run"
