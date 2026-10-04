import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, db_session
from backend.models import UploaderConfig, YouTubeAccount

def run_migrations():
    print("🚀 Initializing YT Manager SQLite schema...")
    init_db()
    session = db_session()

    cfg = session.query(UploaderConfig).first()
    if not cfg:
        cfg = UploaderConfig(
            folder_path=".",
            upload_interval_mins=45,
            retry_interval_hours=24,
            upload_enabled=True,
            status="Initialized"
        )
        session.add(cfg)
        print("✓ Created default uploader configuration")

    account = session.query(YouTubeAccount).first()
    if not account:
        account = YouTubeAccount(
            channel_id="",
            channel_name="YouTube Channel",
            is_active=True
        )
        session.add(account)
        print("✓ Seeded YouTube account model")

    session.commit()
    session.close()
    print("✅ YT Manager database initialized successfully!")

if __name__ == "__main__":
    run_migrations()
