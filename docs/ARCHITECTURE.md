# Architecture Documentation - YT Manager

## Overview
YT Manager handles headless and user-driven video uploading from both local storage and remote network drives to YouTube.

## Components
1. **Frontend Layer**: Pure HTML5, CSS3 Glassmorphism with Trent Sunset Coral/Amber palette, and Vanilla JS.
2. **REST API Layer (`backend/app.py`)**: Flask server serving status, logs, settings, and pending files.
3. **Background Worker (`backend/worker.py`)**: Runs continuously in a dedicated thread to scan directories, handle throttling, and execute chunked uploads.
4. **Scanner Service (`backend/services/smb_service.py`)**: Unified interface for scanning local folders and Windows/SMB UNC shares (`\\server\share`).
5. **YouTube Service (`backend/services/youtube_service.py`)**: Google OAuth2 credentials lifecycle and YouTube Data API v3 client.
6. **Database Layer (`data/yt_manager.db`)**: SQLite with WAL mode.
