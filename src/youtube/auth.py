import os
import json
import logging
from pathlib import Path
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)

SCOPES = settings.YOUTUBE_SCOPES

class YouTubeAuthManager:
    @staticmethod
    def get_authenticated_service():
        """
        Loads OAuth2 credentials and returns built YouTube API service instance.
        """
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        token_file = Path(settings.YOUTUBE_TOKEN_FILE)
        secret_file = Path(settings.YOUTUBE_CLIENT_SECRET_FILE)

        # 1. Check if token data is provided in environment variable (GitHub Secrets)
        token_env = os.getenv("YOUTUBE_TOKEN_DATA")
        if token_env:
            try:
                token_info = json.loads(token_env)
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except Exception as e:
                logger.error(f"Error parsing YOUTUBE_TOKEN_DATA env secret: {e}")

        # 2. Check local token.json file
        if not creds and token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            except Exception as e:
                logger.error(f"Error loading token from {token_file}: {e}")

        # 3. Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh YouTube OAuth token: {e}")
                creds = None

        if not creds:
            logger.warning("No valid YouTube OAuth credentials found.")
            return None

        return build("youtube", "v3", credentials=creds)
