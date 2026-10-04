import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_DIR = BASE_DIR / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "yt-manager-secret-key-trent-2026")
    PORT = int(os.getenv("PORT", 5002))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # SQLite Database Configuration
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "yt_manager.db"))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google / YouTube OAuth
    CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", str(BASE_DIR / "client_secrets.json"))
    TOKEN_FILE = os.getenv("TOKEN_FILE", str(DATA_DIR / "token.json"))
    YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    DEFAULT_CATEGORY = "22" # People & Blogs
    DEFAULT_PRIVACY = "private"
