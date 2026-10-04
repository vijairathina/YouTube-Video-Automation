import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import desc, func

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.database import init_db, db_session, backup_database
from backend.models import UploadLog, UploaderConfig, YouTubeAccount, AuditLog
from backend.services.smb_service import FileScannerService
from backend.services.youtube_service import YouTubeService
from backend.worker import UploaderWorker

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.secret_key = Config.SECRET_KEY

worker = UploaderWorker()
scanner = FileScannerService()
youtube_service = YouTubeService()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# =========================================================================
# STATIC FRONTEND ROUTES
# =========================================================================

@app.route("/")
def serve_index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")

@app.route("/<path:path>")
def serve_static(path):
    if (FRONTEND_DIR / path).exists():
        return send_from_directory(str(FRONTEND_DIR), path)
    return send_from_directory(str(FRONTEND_DIR), "index.html")

# =========================================================================
# HEALTH CHECK
# =========================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    db_ok = False
    try:
        from sqlalchemy import text
        db_session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    auth_ok = youtube_service.is_authenticated()

    return jsonify({
        "service": "YT Manager",
        "status": "Online" if db_ok else "Degraded",
        "database": "Online" if db_ok else "Offline",
        "youtube_auth": "Connected" if auth_ok else "Not Authenticated",
        "version": "2.0.0"
    })

# =========================================================================
# DASHBOARD STATS
# =========================================================================

@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    total_uploads = db_session.query(func.count(UploadLog.id)).scalar()
    success_count = db_session.query(func.count(UploadLog.id)).filter(UploadLog.status == "Success").scalar()
    failed_count = db_session.query(func.count(UploadLog.id)).filter(UploadLog.status == "Failed").scalar()

    cfg = db_session.query(UploaderConfig).first()
    account = db_session.query(YouTubeAccount).first()

    return jsonify({
        "total_uploads": total_uploads or 0,
        "success_count": success_count or 0,
        "failed_count": failed_count or 0,
        "worker_status": cfg.status if cfg else "Idle",
        "upload_enabled": cfg.upload_enabled if cfg else True,
        "current_folder": cfg.folder_path if cfg else ".",
        "is_smb": cfg.is_smb if cfg else False,
        "channel_name": account.channel_name if account else "YouTube Uploader",
        "is_authenticated": youtube_service.is_authenticated()
    })

# =========================================================================
# UPLOAD LOGS & FILE SCANNING
# =========================================================================

@app.route("/api/uploads", methods=["GET"])
def get_uploads():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 25))
    status = request.args.get("status")
    search = request.args.get("search")

    query = db_session.query(UploadLog)
    if status:
        query = query.filter(UploadLog.status == status)
    if search:
        query = query.filter(UploadLog.filename.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(desc(UploadLog.uploaded_at)).offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "items": [item.to_dict() for item in items]
    })

@app.route("/api/files/pending", methods=["GET"])
def pending_files():
    cfg = db_session.query(UploaderConfig).first()
    if not cfg or not cfg.folder_path:
        return jsonify({"files": []})

    files = scanner.scan_folder(
        folder_path=cfg.folder_path,
        is_smb=cfg.is_smb,
        smb_server=cfg.smb_share,
        smb_user=cfg.smb_username,
        smb_pass=cfg.smb_password
    )

    # Check status against upload_logs
    result = []
    for f in files:
        fname = os.path.basename(f)
        log = db_session.query(UploadLog).filter_by(filename=fname).first()
        result.append({
            "filename": fname,
            "path": f,
            "status": log.status if log else "Pending",
            "video_id": log.video_id if log else None
        })

    return jsonify({"files": result})

# =========================================================================
# CONFIGURATION & RETRY TRIGGER
# =========================================================================

@app.route("/api/uploader/settings", methods=["GET", "POST"])
def uploader_settings():
    cfg = db_session.query(UploaderConfig).first()
    if not cfg:
        cfg = UploaderConfig()
        db_session.add(cfg)
        db_session.commit()

    if request.method == "POST":
        data = request.get_json() or {}
        if "folder_path" in data:
            cfg.folder_path = data["folder_path"].strip()
        if "is_smb" in data:
            cfg.is_smb = bool(data["is_smb"])
        if "smb_share" in data:
            cfg.smb_share = data["smb_share"].strip()
        if "smb_username" in data:
            cfg.smb_username = data["smb_username"].strip()
        if "smb_password" in data and data["smb_password"]:
            cfg.smb_password = data["smb_password"].strip()
        if "upload_interval_mins" in data:
            cfg.upload_interval_mins = int(data["upload_interval_mins"])
        if "retry_interval_hours" in data:
            cfg.retry_interval_hours = int(data["retry_interval_hours"])
        if "upload_enabled" in data:
            cfg.upload_enabled = bool(data["upload_enabled"])

        db_session.commit()
        return jsonify({"success": True, "config": cfg.to_dict()})

    return jsonify({"success": True, "config": cfg.to_dict()})

@app.route("/api/uploader/retry", methods=["POST"])
def trigger_retry():
    worker.trigger_retry()
    cfg = db_session.query(UploaderConfig).first()
    if cfg:
        cfg.status = "Manual retry pushed by user"
        db_session.commit()
    return jsonify({"success": True, "message": "Manual retry loop triggered"})

# =========================================================================
# DATABASE BACKUP
# =========================================================================

@app.route("/api/database/backup", methods=["POST"])
def trigger_backup():
    try:
        path = backup_database()
        return jsonify({"success": True, "backup_file": path})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    worker.start()
    print(f"🎬 YT Manager starting on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
