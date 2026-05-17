# Deployment — DigitalOcean droplet (Ubuntu 24.04)

Target: `root@165.227.144.159` → `http://165.227.144.159`

## Step-by-step (run in Termius, one block at a time)

### 1. Upload your Kaggle credentials to the droplet

**On your laptop**, in a regular terminal (not Termius):

```bash
scp ~/.kaggle/access_token root@165.227.144.159:/tmp/access_token
```

**Then on the droplet** (in Termius):

```bash
mkdir -p ~/.kaggle && mv /tmp/access_token ~/.kaggle/access_token && chmod 600 ~/.kaggle/access_token
```

### 2. Run the bootstrap script on the droplet

```bash
curl -sL https://raw.githubusercontent.com/lolatoirxonova-creator/gradproject/main/deploy/install.sh -o /tmp/install.sh
bash /tmp/install.sh
```

This will:
- Install Python, nginx, ufw
- Clone the repo to `/opt/gradproject`
- Create the venv and install all Python deps
- Download the H&M dataset (~3.5 GB) directly via Kaggle CLI
- Configure systemd + nginx reverse proxy on port 80
- The script will stop and tell you to upload models when it gets to that step.

### 3. Upload the trained models from your laptop

**On your laptop**:

```bash
cd /Users/mirzohidabdurazzoqov/Documents/PDP/gradproject
rsync -avz --progress models/ root@165.227.144.159:/opt/gradproject/models/
```

This is ~440 MB. On a typical home connection it takes 10–25 minutes.

### 4. Start the Streamlit service

**On the droplet**:

```bash
systemctl enable --now streamlit
systemctl status streamlit
```

You should see `Active: active (running)`.

### 5. Test the public URL

Open in any browser:  **http://165.227.144.159**

The first request takes ~30 seconds to load (data + models warm-up). Subsequent requests are fast.

## Useful commands

```bash
# Live tail of the streamlit logs
journalctl -u streamlit -f

# Restart after code/model changes
systemctl restart streamlit

# Update code from GitHub
cd /opt/gradproject && git pull && systemctl restart streamlit
```

## Troubleshooting

**Service won't start** → `journalctl -u streamlit -n 50`

**502 Bad Gateway in browser** → streamlit isn't running on 8501. Check `systemctl status streamlit`.

**Memory pressure** → DO droplet only has 2 GB RAM. `htop` to monitor. If swapping, reduce the `sample_n` in `app/main.py` from 1_000_000 to 500_000.

**Want HTTPS?** Point a domain at 165.227.144.159, then on the droplet:
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```
