#!/usr/bin/env bash
# Update an existing droplet deployment with the latest local code.
# Run from the project root on your LAPTOP:  bash deploy/sync.sh
#
# Assumes:
#   - Initial install already ran (deploy/install.sh) → app dir exists at /opt/gradproject
#   - SSH access to root@165.227.144.159 from this laptop
#
# Override target via env var:  DROPLET=root@1.2.3.4 bash deploy/sync.sh
set -euo pipefail

DROPLET="${DROPLET:-root@165.227.144.159}"
APP_DIR="${APP_DIR:-/opt/gradproject}"

cd "$(dirname "$0")/.."  # repo root

echo "==> 1/6 sync app code (app/, src/, .streamlit/, requirements.txt)"
rsync -avz --delete \
    --exclude '__pycache__' \
    --exclude '.DS_Store' \
    --exclude '*.pyc' \
    app/  "${DROPLET}:${APP_DIR}/app/"
rsync -avz \
    --exclude '__pycache__' \
    src/  "${DROPLET}:${APP_DIR}/src/"
# .streamlit/config.toml carries the theme tokens (palette, fonts, radii) — the
# UI looks wrong without it. Theme changes also need a streamlit restart (step 6).
rsync -avz .streamlit/  "${DROPLET}:${APP_DIR}/.streamlit/"
rsync -avz requirements.txt CLAUDE.md  "${DROPLET}:${APP_DIR}/"

echo "==> 2/6 sync evaluation outputs + docs (for Evaluation page + sidebar PDF)"
rsync -avz outputs/  "${DROPLET}:${APP_DIR}/outputs/"
rsync -avz docs/project_explained.pdf docs/final_report.md docs/findings_*.md \
    "${DROPLET}:${APP_DIR}/docs/"

echo "==> 3/6 sync precomputed pickles + image cache"
rsync -avz models/trending.pkl models/article_prices.pkl \
    "${DROPLET}:${APP_DIR}/models/"
ssh "${DROPLET}" "mkdir -p ${APP_DIR}/data/image_cache"
rsync -avz data/image_cache/  "${DROPLET}:${APP_DIR}/data/image_cache/"

echo "==> 4/6 refresh Python deps (bcrypt + plotly added since v1)"
ssh "${DROPLET}" "cd ${APP_DIR} && .venv/bin/pip install -r requirements.txt --quiet"

echo "==> 5/6 update nginx config (gzip + WS-friendly timeout)"
ssh "${DROPLET}" "cat > /etc/nginx/sites-available/streamlit" <<'NGINX'
server {
  listen 80 default_server;
  server_name _;

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
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
  }
}
NGINX
ssh "${DROPLET}" "ln -sf /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/streamlit && rm -f /etc/nginx/sites-enabled/default && nginx -t && systemctl reload nginx"

echo "==> 6/6 run DB migrations, seed demo accounts, restart streamlit"
ssh "${DROPLET}" "cd ${APP_DIR} && \
    .venv/bin/python -c 'from app import db; db.init_db(); print(\"DB init OK\")' && \
    .venv/bin/python -m app.auth seed-demos && \
    systemctl restart streamlit && \
    sleep 3 && \
    systemctl is-active streamlit"

echo ""
echo "✓ Deployed."
echo "  URL:           http://165.227.144.159/  (port 80, nginx-fronted)"
echo "  Service:       ssh ${DROPLET} 'systemctl status streamlit --no-pager'"
echo "  Tail logs:     ssh ${DROPLET} 'journalctl -u streamlit -f'"
echo "  Demo accounts:"
echo "    demo_customer@example.com / Demo2026!     (customer, warm)"
echo "    demo_admin@example.com    / Admin2026!    (admin)"
echo "    demo_analyst@example.com  / Analyst2026!  (analyst)"
echo "    cold_user@example.com     / Cold2026!     (customer, cold-start)"
