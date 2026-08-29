import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.settings import settings
from src.youtube.auth import YouTubeAuthManager

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self):
        self.privacy_status = settings.YOUTUBE_PRIVACY_STATUS  # Hardcoded "private"
        self.made_for_kids = settings.YOUTUBE_MADE_FOR_KIDS    # Hardcoded False

    def upload_short_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        Uploads video to YouTube with hardcoded Private guardrail and MadeForKids: False.
        Returns YouTube Video ID or None.
        """
        if self.privacy_status.lower() != "private":
            raise ValueError("HARDGUARDRAIL VIOLATION: Privacy status MUST be 'private'. Aborting upload!")

        tags = tags or ["Shorts", "Movies", "FilmRecommendations", "TMDB"]
        
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": "24"  # Entertainment category
            },
            "status": {
                "privacyStatus": self.privacy_status,
                "selfDeclaredMadeForKids": self.made_for_kids
            }
        }

        if dry_run:
            logger.info(f"[DRY-RUN] Simulated YouTube Upload SUCCESS.")
            logger.info(f"  Title: {title}")
            logger.info(f"  Privacy Status: {body['status']['privacyStatus']}")
            logger.info(f"  selfDeclaredMadeForKids: {body['status']['selfDeclaredMadeForKids']}")
            return "MOCK_DRY_RUN_VIDEO_ID_12345"

        youtube = YouTubeAuthManager.get_authenticated_service()
        if not youtube:
            logger.warning("YouTube authentication unavailable. Skipping upload.")
            return None

        try:
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
            
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            logger.info("Executing YouTube video upload...")
            response = request.execute()
            video_id = response.get("id")
            logger.info(f"YouTube Upload Successful! Video ID: {video_id} (Privacy: Private)")
            return video_id
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return None
