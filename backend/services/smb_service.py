import os
import sys
import tempfile
from pathlib import Path

VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi', '.mkv')

try:
    from smbclient import register_session, listdir as smb_listdir, open_file as smb_open_file
    HAS_SMB = True
except ImportError:
    HAS_SMB = False

class FileScannerService:
    def __init__(self, smb_cache_dir=None):
        self.smb_cache_dir = smb_cache_dir or tempfile.mkdtemp(prefix="yt_smb_cache_")

    def connect_smb(self, server: str, username: str = None, password: str = None):
        if not HAS_SMB:
            raise RuntimeError("smbclient package not available.")
        if username or password:
            register_session(server, username=username, password=password)
        else:
            register_session(server)
        return True

    def scan_folder(self, folder_path: str, is_smb: bool = False, smb_server: str = None, smb_user: str = None, smb_pass: str = None):
        """Scans local path or SMB UNC path and returns list of video files."""
        if not folder_path:
            return []

        # Auto-detect SMB UNC path
        if folder_path.startswith("\\\\") or folder_path.startswith("//") or is_smb:
            if not HAS_SMB:
                print("⚠️ [FileScanner] SMB requested but smbclient is not installed.")
                return []
            try:
                if smb_server:
                    self.connect_smb(smb_server, smb_user, smb_pass)
                entries = smb_listdir(folder_path)
                return [
                    os.path.join(folder_path, f)
                    for f in entries
                    if f.lower().endswith(VIDEO_EXTENSIONS)
                ]
            except Exception as e:
                print(f"❌ [FileScanner] SMB Scan error: {e}")
                return []

        # Local directory
        if not os.path.isdir(folder_path):
            return []

        try:
            return [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith(VIDEO_EXTENSIONS)
            ]
        except Exception as e:
            print(f"❌ [FileScanner] Local Scan error: {e}")
            return []

    def get_local_path(self, file_path: str, is_smb: bool = False):
        """If on SMB, downloads to local temp cache, else returns path directly."""
        if not is_smb and not (file_path.startswith("\\\\") or file_path.startswith("//")):
            return file_path

        filename = os.path.basename(file_path)
        cache_file = os.path.join(self.smb_cache_dir, filename)
        if not os.path.exists(cache_file):
            with smb_open_file(file_path, "rb") as src:
                with open(cache_file, "wb") as dst:
                    dst.write(src.read())
        return cache_file
