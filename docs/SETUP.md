# Setup & Deployment Guide - YT Manager

## Local Development
1. Open terminal in `Projects/YTManager/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize SQLite database:
   ```bash
   python migrations/init_db.py
   ```
4. Place your Google API `client_secrets.json` into `Projects/YTManager/`.
5. Run the application:
   ```bash
   python run.py
   ```
6. Open `http://localhost:5002`.

## Production Deployment (Windows Service / Linux Systemd)
### Systemd Service (Linux)
Create `/etc/systemd/system/yt-manager.service`:
```ini
[Unit]
Description=YouTube Manager Background Service
After=network.target

[Service]
User=appuser
WorkingDirectory=/opt/YTManager
ExecStart=/opt/YTManager/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Start and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now yt-manager
```
