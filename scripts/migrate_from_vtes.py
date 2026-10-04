import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import csv
import json
import shutil
from pathlib import Path
from datetime import datetime

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
VTES_DIR = PROJECT_DIR.parent.parent

sys.path.insert(0, str(PROJECT_DIR))

from backend.database import init_db, db_session
from backend.models import UploadLog, UploaderConfig, YouTubeAccount, AuditLog

def migrate_vtes_yt_data():
    print(f"📦 Starting YT Manager migration from VTES directory: {VTES_DIR}")
    init_db()
    session = db_session()

    # 1. Migrate Uploader Settings from app_state.json
    app_state_file = VTES_DIR / "app_state.json"
    if app_state_file.exists():
        with open(app_state_file, "r", encoding="utf-8") as f:
            try:
                state_data = json.load(f)
            except Exception:
                state_data = {}

        cfg = session.query(UploaderConfig).first()
        if not cfg:
            cfg = UploaderConfig()
            session.add(cfg)

        cfg.folder_path = state_data.get("folder_path", ".")
        cfg.is_smb = bool(state_data.get("smb_share"))
        cfg.smb_share = state_data.get("smb_share", "")
        cfg.smb_username = state_data.get("smb_username", "")
        cfg.smb_password = state_data.get("smb_password", "")
        cfg.upload_interval_mins = int(state_data.get("upload_interval_mins", 45))
        cfg.retry_interval_hours = int(state_data.get("retry_interval_hours", 24))
        cfg.upload_enabled = bool(state_data.get("upload_enabled", True))
        cfg.status = state_data.get("status", "Migrated from VTES")
        print("✓ Migrated uploader folder & interval configurations")

    # 2. Copy client_secrets.json & token.json if present
    token_src = VTES_DIR / "token.json"
    token_dst = PROJECT_DIR / "data" / "token.json"
    if token_src.exists():
        token_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(token_src, token_dst)
        print("✓ Migrated authorized Google OAuth token.json")

    secrets_src = VTES_DIR / "client_secrets.json"
    secrets_dst = PROJECT_DIR / "client_secrets.json"
    if secrets_src.exists():
        shutil.copy2(secrets_src, secrets_dst)
        print("✓ Migrated Google OAuth client_secrets.json")

    # 3. Migrate historical uploads from uploads_log.csv
    csv_file = VTES_DIR / "uploads_log.csv"
    imported_count = 0
    duplicate_count = 0

    if csv_file.exists():
        with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = (row.get("Filename") or row.get("filename") or "").strip()
                if not fname:
                    continue

                existing = session.query(UploadLog).filter_by(filename=fname).first()
                if existing:
                    duplicate_count += 1
                    continue

                ts_str = row.get("Timestamp") or ""
                parsed_ts = None
                if ts_str:
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                        try:
                            parsed_ts = datetime.strptime(ts_str, fmt)
                            break
                        except Exception:
                            pass

                log_entry = UploadLog(
                    filename=fname,
                    title=row.get("Title") or Path(fname).stem,
                    video_id=row.get("Video ID") or row.get("video_id") or "N/A",
                    status=row.get("Status") or "Success",
                    error_details=row.get("Error Details") or "",
                    uploaded_at=parsed_ts or datetime.utcnow()
                )
                session.add(log_entry)
                imported_count += 1

    session.add(AuditLog(
        event_type="migration",
        message=f"Migrated from VTES uploads_log.csv: {imported_count} upload records",
        details_json=json.dumps({"imported": imported_count, "duplicates": duplicate_count})
    ))

    session.commit()
    session.close()
    print(f"🎉 YT Manager Migration Complete! Imported: {imported_count} logs ({duplicate_count} skipped).")

if __name__ == "__main__":
    migrate_vtes_yt_data()
