"""
Video scraper module for fetching and downloading videos from RPI camera interface.
"""

import os
import re
import time
import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup, Tag

from .config import config


class VideoScraper:
    """Handles scraping and downloading videos from the RPI camera web interface."""
    
    def __init__(self):
        self.session = requests.Session()
    
    def parse_video_metadata(self, fieldset: Tag) -> Optional[Dict[str, str]]:
        """
        Parse video metadata from a fieldset element.
        
        Args:
            fieldset: BeautifulSoup Tag object representing a video fieldset
            
        Returns:
            dict: Video metadata or None if parsing fails
        """
        # Extract video link
        a_tag = fieldset.find("a", href=True)
        if not (a_tag and a_tag["href"].startswith("media/") and a_tag["href"].endswith(".mp4")):
            return None
        
        video_url = a_tag["href"]
        
        # Thumbnail from delete button
        delete_btn = fieldset.find("button", attrs={"name": "delete1"})
        thumbnail = delete_btn["value"] if delete_btn else None
        
        # Extract metadata from fieldset text
        details = fieldset.get_text(" ", strip=True)
        
        # Try to extract size, duration, date, time using regex
        size_match = re.search(r"(\d+ MB)", details)
        duration_match = re.search(r"(\d+s)", details)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", details)
        time_match = re.search(r"(\d{2}:\d{2}:\d{2})", details)
        
        size = size_match.group(1) if size_match else ""
        duration = duration_match.group(1) if duration_match else ""
        date = date_match.group(1) if date_match else ""
        time_str = time_match.group(1) if time_match else ""
        
        # Build title: date and time
        if date and time_str:
            title = f"{date} {time_str}"
        else:
            title = "Unknown DateTime"
        
        return {
            "video": video_url,
            "thumbnail": thumbnail,
            "title": title,
            "size": size,
            "duration": duration,
            "date": date,
            "time": time_str
        }
    
    def fetch_video_list(self) -> List[Dict[str, str]]:
        """
        Fetch the list of available videos from the camera interface.
        
        Returns:
            list: List of video metadata dictionaries
        """
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(config.preview_url, timeout=config.REQUEST_TIMEOUT)
                if response.status_code != 200:
                    raise Exception(f"Preview page HTTP {response.status_code}")
                
                soup = BeautifulSoup(response.text, "html.parser")
                break
                
            except Exception as e:
                print(f"Error fetching preview page (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        else:
            print("Failed to fetch preview page after retries.")
            return []
        
        videos = []
        for fieldset in soup.find_all("fieldset", class_="fileicon"):
            meta = self.parse_video_metadata(fieldset)
            if meta:
                videos.append(meta)
        
        return videos
    
    def download_video(self, video_meta: Dict[str, str], day_dir: str) -> bool:
        """
        Download a single video to the specified directory.
        
        Args:
            video_meta: Video metadata dictionary
            day_dir: Directory to save the video to
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        video_url = f"{config.BASE_URL.rstrip('/')}/{video_meta['video']}"
        filename = video_meta['video'].split('/')[-1]
        local_path = os.path.join(day_dir, filename)
        
        print(f"Downloading {filename} from {video_url}...")
        
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(
                    video_url, 
                    stream=True, 
                    timeout=config.DOWNLOAD_TIMEOUT
                )
                
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=config.DOWNLOAD_CHUNK_SIZE):
                            f.write(chunk)
                    
                    print(f"Downloaded {filename} to {local_path}")
                    return True
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"Download error for {filename} (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        
        print(f"Failed to download {filename} after retries.")
        return False
    
    def delete_video_from_server(self, video_meta: Dict[str, str]) -> bool:
        """
        Delete a video from the server using its thumbnail identifier.
        
        Args:
            video_meta: Video metadata dictionary
            
        Returns:
            bool: True if deletion request was successful, False otherwise
        """
        if not video_meta.get('thumbnail'):
            print("No thumbnail found for server delete request.")
            return False
        
        for attempt in range(config.MAX_RETRIES):
            try:
                delete_response = self.session.post(
                    config.preview_url,
                    data={'delete1': video_meta['thumbnail']},
                    timeout=config.REQUEST_TIMEOUT
                )
                
                if delete_response.status_code == 200:
                    print(f"Server delete request sent for {video_meta['thumbnail']}")
                    return True
                else:
                    raise Exception(f"HTTP {delete_response.status_code}")
                    
            except Exception as e:
                print(f"Delete error for {video_meta['thumbnail']} (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        
        print(f"Failed to delete {video_meta['thumbnail']} on server after retries.")
        return False
    
    def fetch_and_clean(self) -> None:
        """
        Main method: Download new videos and delete them from the server.
        Saves videos to a directory organized by date.
        """
        videos = self.fetch_video_list()
        if not videos:
            print("No videos found to download.")
            return
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        day_dir = os.path.join(config.DATA_DIR, today)
        os.makedirs(day_dir, exist_ok=True)
        
        for video_meta in videos:
            # Download the video
            if self.download_video(video_meta, day_dir):
                # If download successful, delete from server
                self.delete_video_from_server(video_meta)
