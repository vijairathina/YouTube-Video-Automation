# VTES Data Migration - YT Manager

## Overview
This document outlines the extraction of YouTube uploading configurations and historical logs from legacy VTES into YT Manager's standalone SQLite database.

## Source Files in VTES
- `uploads_log.csv`: 606 historical upload records.
- `app_state.json`: Folder path, SMB credentials, intervals, status.
- `token.json` & `client_secrets.json`: Authorized Google credentials.

## Execution
Run the migration script:
```bash
python scripts/migrate_from_vtes.py
```

## Verification
- Navigate to `http://localhost:5002`.
- Verify total uploads display matches the 606 records from VTES.
- Check that the active watcher directory matches the previous setting.
