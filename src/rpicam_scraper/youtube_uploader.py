"""
YouTube uploader module for handling authentication and video uploads.
"""

import os
import pickle
import time
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

from .config import config


class YouTubeUploader:
    """Handles YouTube authentication and video uploads."""
    
    def __init__(self):
        self.youtube_service = None
    
    def get_authenticated_service(self):
        """Authenticate and return a YouTube API service object."""
        creds = None
        
        # Load credentials if they exist
        if os.path.exists(config.YOUTUBE_TOKEN_PATH):
            with open(config.YOUTUBE_TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
        
        # If no valid credentials, log in and save
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.YOUTUBE_CLIENT_SECRETS, 
                    config.YOUTUBE_SCOPES
                )
                creds = flow.run_console()
            
            # Save credentials for next run
            with open(config.YOUTUBE_TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)
        
        self.youtube_service = build("youtube", "v3", credentials=creds)
        return self.youtube_service
    
    def upload_video(self, file_path: str, title: str, description: Optional[str] = None) -> bool:
        """
        Upload a video to YouTube.
        
        Args:
            file_path: Path to the video file to upload
            title: Title for the video
            description: Optional description for the video
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not self.youtube_service:
            self.get_authenticated_service()
        
        body = {
            "snippet": {
                "title": title,
                "description": description or config.YOUTUBE_UPLOAD_DESCRIPTION,
                "tags": config.youtube_tags_list,
                "categoryId": config.YOUTUBE_UPLOAD_CATEGORY
            },
            "status": {
                "privacyStatus": config.YOUTUBE_PRIVACY_STATUS
            }
        }
        
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        
        for attempt in range(config.MAX_RETRIES):
            try:
                request = self.youtube_service.videos().insert(
                    part=",".join(body.keys()),
                    body=body,
                    media_body=media
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        print(f"Upload progress: {int(status.progress() * 100)}%")
                
                print(f"Upload complete: https://youtu.be/{response['id']}")
                return True
                
            except Exception as e:
                print(f"YouTube upload error (attempt {attempt+1}): {e}")
                
                # Check for rate limit error
                if hasattr(e, 'resp') and e.resp and e.resp.status == 403:
                    print("YouTube rate limit hit. Waiting 1 hour before retrying...")
                    time.sleep(3600)
                else:
                    wait = 2 ** attempt
                    print(f"Retrying upload in {wait} seconds...")
                    time.sleep(wait)
        
        print("Upload failed after retries.")
        return False
