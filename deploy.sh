#!/bin/bash
set -e

echo "=== NexCrawl VPS Deployment ==="

# 1. Install system dependencies
echo "[1/6] Installing system packages..."
apt update -y
apt install -y python3-pip python3-venv python3-dev build-essential libxml2-dev libxslt1-dev

# 2. Create app directory
echo "[2/6] Setting up application directory..."
mkdir -p /opt/nexcrawl
cp -r /tmp/nexcrawl-deploy/* /opt/nexcrawl/
cd /opt/nexcrawl

# 3. Create virtual environment and install
echo "[3/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Create systemd service
echo "[4/6] Creating systemd service..."
cat > /etc/systemd/system/nexcrawl.service << 'EOF'
[Unit]
Description=NexCrawl API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nexcrawl
Environment=PATH=/opt/nexcrawl/venv/bin:/usr/bin:/bin
ExecStart=/opt/nexcrawl/venv/bin/uvicorn nexcrawl.api:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nexcrawl
systemctl restart nexcrawl

# 5. Configure Nginx reverse proxy
echo "[5/6] Configuring Nginx..."
cat > /etc/nginx/sites-available/nexcrawl << 'EOF'
server {
    listen 80;
    server_name _;

    location /v1/ {
        proxy_pass http://127.0.0.1:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable site and remove default if it conflicts
ln -sf /etc/nginx/sites-available/nexcrawl /etc/nginx/sites-enabled/nexcrawl
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

# 6. Verify
echo "[6/6] Verifying..."
sleep 2
systemctl status nexcrawl --no-pager
curl -s http://127.0.0.1:8000/health

echo ""
echo "=== Deployment Complete ==="
echo "API is live at: http://31.97.102.237/health"
echo "API docs at: http://31.97.102.237/docs"
