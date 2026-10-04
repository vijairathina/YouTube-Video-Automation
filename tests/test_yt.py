import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["DATABASE_PATH"] = ":memory:"

from backend.database import Base, engine, db_session
from backend.models import UploadLog, UploaderConfig
from backend.services.smb_service import FileScannerService

class TestYTManager(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.session = db_session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=engine)

    def test_upload_log_creation(self):
        log = UploadLog(
            filename="sample_video.mp4",
            title="Sample Video",
            video_id="dQw4w9WgXcQ",
            status="Success"
        )
        self.session.add(log)
        self.session.commit()

        retrieved = self.session.query(UploadLog).filter_by(filename="sample_video.mp4").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.status, "Success")
        self.assertEqual(retrieved.video_id, "dQw4w9WgXcQ")

    def test_uploader_config(self):
        cfg = UploaderConfig(
            folder_path="/test/videos",
            upload_interval_mins=30,
            upload_enabled=True
        )
        self.session.add(cfg)
        self.session.commit()

        retrieved = self.session.query(UploaderConfig).first()
        self.assertEqual(retrieved.upload_interval_mins, 30)
        self.assertTrue(retrieved.upload_enabled)

    def test_file_scanner_filter(self):
        scanner = FileScannerService()
        # Scan current test directory (no video files should be returned)
        files = scanner.scan_folder(str(Path(__file__).parent))
        self.assertEqual(len(files), 0)

if __name__ == "__main__":
    unittest.main()
