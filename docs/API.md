# API Reference - YT Manager

Base URL: `http://localhost:5002/api`

### Health & Stats
- `GET /health` -> `{ "service": "YT Manager", "status": "Online", "database": "Online", "youtube_auth": "Connected" }`
- `GET /dashboard/stats` -> Returns total uploads, success count, failed count, worker status, current folder, and channel name.

### Uploads & Files
- `GET /uploads?page=1&limit=25&status=Success&search=test` -> Paginated upload history.
- `GET /files/pending` -> Lists detected video files in the configured directory and their upload status.

### Settings & Controls
- `GET /uploader/settings` -> Current folder, SMB credentials, intervals, and enabled state.
- `POST /uploader/settings` -> Update settings payload.
- `POST /uploader/retry` -> Forces immediate background retry loop.

### Backup
- `POST /database/backup` -> Creates snapshot in `backups/`.
