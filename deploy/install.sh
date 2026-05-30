#!/usr/bin/env bash
# Bootstrap script for the DigitalOcean droplet.
# Run as root on a fresh Ubuntu 24.04 droplet.
# Usage:  bash install.sh
set -euo pipefail

REPO_URL="https://github.com/lolatoirxonova-creator/gradproject.git"
APP_DIR="/opt/gradproject"
DOMAIN="${DOMAIN:-_}"  # Optional: set DOMAIN env var if you have a domain pointed at this droplet

echo "==> 1/8 apt update & install system packages"
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y python3.12 python3.12-venv python3-pip git unzip nginx ufw rsync

echo "==> 2/8 clone repo to ${APP_DIR}"
if [ ! -d "${APP_DIR}/.git" ]; then
  git clone "${REPO_URL}" "${APP_DIR}"
fi
cd "${APP_DIR}"
git pull || true

echo "==> 3/8 python venv + requirements"
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt

echo "==> 4/8 prepare data + models directories"
mkdir -p data models outputs

echo "==> 5/8 kaggle credentials check"
if [ -f /root/.kaggle/access_token ] || [ -f /root/.kaggle/kaggle.json ]; then
  chmod 600 /root/.kaggle/* 2>/dev/null || true
  echo "   kaggle creds present"
else
  echo "   !! No kaggle credentials found at /root/.kaggle/"
  echo "   Upload your access_token or kaggle.json to /root/.kaggle/ then re-run this script"
  exit 1
fi

echo "==> 6/8 download H&M dataset (~3.5 GB total)"
cd "${APP_DIR}"
for f in articles.csv customers.csv transactions_train.csv; do
  if [ ! -f "data/${f}" ]; then
    echo "   downloading ${f}"
    .venv/bin/kaggle competitions download -c h-and-m-personalized-fashion-recommendations -f "${f}" -p data/
    if [ -f "data/${f}.zip" ]; then
      unzip -o "data/${f}.zip" -d data/ && rm "data/${f}.zip"
    fi
  else
    echo "   ${f} already present, skip"
  fi
done

echo "==> 7/8 systemd service + nginx reverse proxy"
cat > /etc/systemd/system/streamlit.service <<'UNIT'
[Unit]
Description=H&M Recommendation Streamlit app
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/gradproject
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/gradproject/.venv/bin/streamlit run app/main.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/nginx/sites-available/streamlit <<EOF
server {
  listen 80 default_server;
  server_name ${DOMAIN};

  client_max_body_size 100M;

  gzip on;
  gzip_vary on;
  gzip_proxied any;
  gzip_min_length 1024;
  gzip_comp_level 5;
  gzip_types
    application/javascript
    application/json
    application/xml
    application/wasm
    text/css
    text/plain
    text/xml
    image/svg+xml;

  location / {
    proxy_pass http://127.0.0.1:8501;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
  }
}
EOF

ln -sf /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/streamlit
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> 8/8 enable firewall + start streamlit service"
ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw --force enable

# Don't start streamlit yet if models are missing — print instructions instead
if [ ! -f models/cf_als_model.pkl ] || [ ! -f models/ncf_neumf.pt ]; then
  echo ""
  echo "   !! Model files missing. From your local laptop run:"
  echo "      rsync -avz models/ root@\$(curl -s ifconfig.me)/opt/gradproject/models/"
  echo "   then on the droplet:  systemctl enable --now streamlit"
  exit 0
fi

systemctl daemon-reload
systemctl enable --now streamlit

echo ""
echo "✓ Deployment complete. Streamlit is running on:"
echo "   http://$(curl -s ifconfig.me)/"
echo ""
echo "Service controls:"
echo "   systemctl status streamlit"
echo "   journalctl -u streamlit -f"
echo "   systemctl restart streamlit"
