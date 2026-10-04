import os
import json
from pathlib import Path
from backend.config import Config

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

class YouTubeService:
    def __init__(self, secrets_file=None, token_file=None):
        self.secrets_file = secrets_file or Config.CLIENT_SECRETS_FILE
        self.token_file = token_file or Config.TOKEN_FILE
        self.youtube = None

    def is_authenticated(self):
        if not HAS_GOOGLE:
            return False
        if not os.path.exists(self.token_file):
            return False
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, Config.YOUTUBE_SCOPES)
            return creds and creds.valid
        except Exception:
            return False

    def authenticate(self):
        """Authenticates with Google OAuth2 and builds YouTube API client."""
        if not HAS_GOOGLE:
            raise RuntimeError("google-api-python-client / google-auth not installed.")

        credentials = None
        if os.path.exists(self.token_file):
            try:
                credentials = Credentials.from_authorized_user_file(self.token_file, Config.YOUTUBE_SCOPES)
            except Exception:
                credentials = None

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                if not os.path.exists(self.secrets_file):
                    raise FileNotFoundError(f"client_secrets.json not found at {self.secrets_file}")
                flow = InstalledAppFlow.from_client_secrets_file(self.secrets_file, Config.YOUTUBE_SCOPES)
                credentials = flow.run_local_server(port=0)

            # Persist token
            Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, "w") as token:
                token.write(credentials.to_json())

        self.youtube = build("youtube", "v3", credentials=credentials)
        return True

    def upload_video(self, file_path, title, description="", category_id="22", privacy_status="private"):
        """Uploads video using resumable MediaFileUpload."""
        if not self.youtube:
            self.authenticate()

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = self.youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()

        return response.get("id")
