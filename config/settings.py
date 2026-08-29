import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    # Base Directories
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    OUTPUT_DIR: Path = BASE_DIR / "output"

    # API Keys & Endpoints
    TMDB_API_KEY: str = Field(default_factory=lambda: os.getenv("TMDB_API_KEY", ""))
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p"

    PEXELS_API_KEY: str = Field(default_factory=lambda: os.getenv("PEXELS_API_KEY", ""))
    PIXABAY_API_KEY: str = Field(default_factory=lambda: os.getenv("PIXABAY_API_KEY", ""))
    
    # LLM Settings (Configurable model name)
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL_NAME: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"))

    # YouTube API & Security Guardrails
    YOUTUBE_CLIENT_SECRET_FILE: str = Field(default_factory=lambda: os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json"))
    YOUTUBE_TOKEN_FILE: str = Field(default_factory=lambda: os.getenv("YOUTUBE_TOKEN_FILE", "token.json"))
    YOUTUBE_PRIVACY_STATUS: str = "private"  # MUST NEVER BE ANYTHING OTHER THAN PRIVATE
    YOUTUBE_MADE_FOR_KIDS: bool = False       # YouTube Data API status.selfDeclaredMadeForKids field
    YOUTUBE_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]

    # Email Notifications
    SMTP_SERVER: str = Field(default_factory=lambda: os.getenv("SMTP_SERVER", ""))
    SMTP_PORT: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    SMTP_USERNAME: str = Field(default_factory=lambda: os.getenv("SMTP_USERNAME", ""))
    SMTP_PASSWORD: str = Field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    NOTIFICATION_EMAIL: str = Field(default_factory=lambda: os.getenv("NOTIFICATION_EMAIL", ""))

    # Selection & Cooldown Rules
    TITLE_COOLDOWN_DAYS: int = 30
    CONCEPT_COOLDOWN_DAYS: int = 5
    UNDERRATED_MIN_VOTE_COUNT: int = 100
    UNDERRATED_MIN_POPULARITY: float = 15.0

    # Video Render Settings
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    FPS: int = 30
    VOICE_NAME: str = "en-US-ChristopherNeural"

    def ensure_directories(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
