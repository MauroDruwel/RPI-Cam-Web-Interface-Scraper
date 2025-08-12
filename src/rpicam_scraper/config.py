"""
Configuration module for RPI Camera Web Interface Scraper.
All configuration values are loaded from environment variables.
"""

import os
from typing import List


class Config:
    """Configuration class that loads all settings from environment variables."""
    
    def __init__(self):
        """Initialize configuration by loading from environment variables."""
        # Camera server configuration
        self.BASE_URL: str = os.environ.get("RPICAM_BASE_URL", "")
        
        # YouTube API configuration
        self.YOUTUBE_CLIENT_SECRETS: str = os.environ.get("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
        self.YOUTUBE_TOKEN_PATH: str = os.environ.get("YOUTUBE_TOKEN_PATH", "token.pickle")
        self.YOUTUBE_UPLOAD_TITLE_PREFIX: str = os.environ.get("YOUTUBE_UPLOAD_TITLE_PREFIX", "RPiCam")
        self.YOUTUBE_UPLOAD_DESCRIPTION: str = os.environ.get("YOUTUBE_UPLOAD_DESCRIPTION", "Uploaded by RPI-Cam-Web-Interface-Scraper")
        self.YOUTUBE_UPLOAD_TAGS: str = os.environ.get("YOUTUBE_UPLOAD_TAGS", "RPiCam,AutoUpload")
        self.YOUTUBE_UPLOAD_CATEGORY: str = os.environ.get("YOUTUBE_UPLOAD_CATEGORY", "22")  # People & Blogs
        self.YOUTUBE_PRIVACY_STATUS: str = os.environ.get("YOUTUBE_PRIVACY_STATUS", "unlisted")
        
        # File storage configuration
        self.DATA_DIR: str = os.environ.get("RPICAM_DATA_DIR", "/data/videos")
        
        # Processing configuration
        self.MAX_RETRIES: int = int(os.environ.get("RPICAM_MAX_RETRIES", "5"))
        self.REQUEST_TIMEOUT: int = int(os.environ.get("RPICAM_REQUEST_TIMEOUT", "30"))
        self.DOWNLOAD_TIMEOUT: int = int(os.environ.get("RPICAM_DOWNLOAD_TIMEOUT", "60"))
        self.DOWNLOAD_CHUNK_SIZE: int = int(os.environ.get("RPICAM_DOWNLOAD_CHUNK_SIZE", "8192"))
        
        # Scheduling configuration
        self.ENABLE_SCHEDULER: bool = os.environ.get("RPICAM_ENABLE_SCHEDULER", "true").lower() == "true"
        self.SCRAPE_INTERVAL_MINUTES: int = int(os.environ.get("RPICAM_SCRAPE_INTERVAL_MINUTES", "15"))
        self.DAILY_PROCESS_TIME: str = os.environ.get("RPICAM_DAILY_PROCESS_TIME", "23:59")  # HH:MM format
        
        # YouTube API scopes
        self.YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    
    @property
    def preview_url(self) -> str:
        """Get the full preview URL."""
        if not self.BASE_URL:
            raise ValueError("RPICAM_BASE_URL environment variable is required")
        return f"{self.BASE_URL.rstrip('/')}/preview.php"
    
    @property
    def youtube_tags_list(self) -> List[str]:
        """Get YouTube tags as a list."""
        return [tag.strip() for tag in self.YOUTUBE_UPLOAD_TAGS.split(",") if tag.strip()]
    
    def validate(self) -> None:
        """Validate that all required configuration is present."""
        required_vars = [
            ("RPICAM_BASE_URL", self.BASE_URL),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Global config instance
config = Config()
