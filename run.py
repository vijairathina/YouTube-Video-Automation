#!/usr/bin/env python3
"""YT Manager - Standalone Runner"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.database import init_db
from backend.worker import UploaderWorker
from backend.app import app, worker

if __name__ == "__main__":
    init_db()
    worker.start()
    print(f"""
    ==================================================
    ✨ YT Manager (Standalone Project)
    📍 URL: http://localhost:{Config.PORT}
    💾 Database: {Config.DATABASE_PATH}
    ==================================================
    """)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
