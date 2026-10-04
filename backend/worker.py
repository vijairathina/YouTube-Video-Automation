import os
import time
import threading
from datetime import datetime
from backend.database import db_session
from backend.models import UploadLog, UploaderConfig, AuditLog
from backend.services.smb_service import FileScannerService
from backend.services.youtube_service import YouTubeService

class UploaderWorker:
    def __init__(self):
        self._running = False
        self._thread = None
        self._force_retry = False
        self.scanner = FileScannerService()
        self.uploader = YouTubeService()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("🎬 YT Manager background uploader worker active.")

    def trigger_retry(self):
        self._force_retry = True

    def _loop(self):
        while self._running:
            try:
                session = db_session()
                cfg = session.query(UploaderConfig).first()
                if not cfg:
                    cfg = UploaderConfig()
                    session.add(cfg)
                    session.commit()

                if not cfg.upload_enabled:
                    cfg.status = "Paused by user"
                    session.commit()
                    session.close()
                    time.sleep(15)
                    continue

                folder = cfg.folder_path
                is_smb = cfg.is_smb
                
                cfg.status = f"Scanning {folder}..."
                cfg.last_scan_at = datetime.utcnow()
                session.commit()

                files = self.scanner.scan_folder(
                    folder_path=folder,
                    is_smb=is_smb,
                    smb_server=cfg.smb_share,
                    smb_user=cfg.smb_username,
                    smb_pass=cfg.smb_password
                )

                if not files:
                    cfg.status = "Waiting for files"
                    session.commit()
                    session.close()
                    time.sleep(30)
                    continue

                for file_path in files:
                    if not self._running:
                        break

                    filename = os.path.basename(file_path)
                    title = os.path.splitext(filename)[0]

                    # Check if already uploaded successfully
                    already_uploaded = session.query(UploadLog).filter_by(filename=filename, status="Success").first()
                    if already_uploaded:
                        continue

                    cfg.status = f"Uploading: {filename}"
                    session.commit()

                    try:
                        local_path = self.scanner.get_local_path(file_path, is_smb)
                        video_id = self.uploader.upload_video(local_path, title=title)

                        log = UploadLog(
                            filename=filename,
                            title=title,
                            video_id=video_id,
                            status="Success",
                            file_path=file_path,
                            uploaded_at=datetime.utcnow()
                        )
                        session.add(log)
                        cfg.status = f"Uploaded {filename}"
                        session.commit()
                        print(f"✅ [YT Worker] Uploaded: {filename} (ID: {video_id})")

                        # Wait upload interval between videos
                        interval_secs = max(cfg.upload_interval_mins * 60, 60)
                        for _ in range(int(interval_secs / 5)):
                            if not self._running or self._force_retry:
                                self._force_retry = False
                                break
                            time.sleep(5)

                    except Exception as upload_err:
                        err_msg = str(upload_err)
                        print(f"❌ [YT Worker] Upload error for {filename}: {err_msg}")
                        
                        log = UploadLog(
                            filename=filename,
                            title=title,
                            video_id="N/A",
                            status="Failed",
                            error_details=err_msg,
                            file_path=file_path,
                            uploaded_at=datetime.utcnow()
                        )
                        session.add(log)

                        if "uploadLimitExceeded" in err_msg:
                            cfg.status = "Quota reached - Waiting 1 hour"
                            session.commit()
                            time.sleep(3600)
                        else:
                            cfg.status = f"Error: {err_msg[:40]}"
                            session.commit()
                            time.sleep(30)

                session.close()
            except Exception as e:
                print(f"⚠️ [YT Worker] Supervisory loop error: {e}")
                time.sleep(20)

            # Polling rest between scanning passes
            time.sleep(20)
