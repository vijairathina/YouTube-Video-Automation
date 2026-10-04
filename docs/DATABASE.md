# Database Documentation - YT Manager

## SQLite Database
- **Path**: `data/yt_manager.db`
- **Driver**: SQLite 3 with SQLAlchemy 2.0 ORM
- **Journal Mode**: WAL (Write-Ahead Logging)

## Tables
1. **`upload_logs`**: Historical upload records (filename, title, video_id, status, error_details, file_path, uploaded_at).
2. **`uploader_configs`**: Folder path, SMB credentials, upload interval (mins), retry interval (hours), upload_enabled, status.
3. **`youtube_accounts`**: Channel ID, channel name, OAuth token reference, and active status.
4. **`scheduled_videos`**: Queue of future planned video uploads.
5. **`audit_logs`**: Configuration changes, retry events, and service lifecycle logs.
