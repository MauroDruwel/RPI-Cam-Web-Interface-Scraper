"""
Video processor module for concatenating and processing videos.
"""

import os
import datetime
import subprocess
import time
from typing import List, Optional

from .config import config
from .youtube_uploader import YouTubeUploader


class VideoProcessor:
    """Handles video concatenation and processing operations."""
    
    def __init__(self):
        self.youtube_uploader = YouTubeUploader()
    
    def get_video_files(self, day_dir: str) -> List[str]:
        """
        Get all MP4 video files from a directory.
        
        Args:
            day_dir: Directory to search for video files
            
        Returns:
            list: Sorted list of MP4 filenames
        """
        if not os.path.exists(day_dir):
            return []
        
        return sorted([f for f in os.listdir(day_dir) if f.endswith('.mp4')])
    
    def create_ffmpeg_file_list(self, day_dir: str, files: List[str]) -> str:
        """
        Create a file list for ffmpeg concatenation.
        
        Args:
            day_dir: Directory containing the video files
            files: List of video filenames
            
        Returns:
            str: Path to the created file list
        """
        list_path = os.path.join(day_dir, 'files.txt')
        with open(list_path, 'w') as f:
            for file in files:
                # Use absolute paths for ffmpeg
                abs_path = os.path.abspath(os.path.join(day_dir, file))
                f.write(f"file '{abs_path}'\n")
        return list_path
    
    def concatenate_videos(self, day_dir: str, files: List[str], output_path: str) -> bool:
        """
        Concatenate multiple video files using ffmpeg.
        
        Args:
            day_dir: Directory containing the video files
            files: List of video filenames to concatenate
            output_path: Path for the output concatenated video
            
        Returns:
            bool: True if concatenation was successful, False otherwise
        """
        list_path = self.create_ffmpeg_file_list(day_dir, files)
        
        for attempt in range(config.MAX_RETRIES):
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_path,
                '-c', 'copy', output_path
            ]
            
            print(f"Running ffmpeg to concatenate {len(files)} files... (attempt {attempt+1})")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"Concatenated video saved to {output_path}")
                    return True
                else:
                    print(f"ffmpeg error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("ffmpeg operation timed out")
            except Exception as e:
                print(f"ffmpeg execution error: {e}")
            
            time.sleep(2 ** attempt)
        
        print("Failed to concatenate videos after retries.")
        return False
    
    def cleanup_files(self, day_dir: str, files_to_delete: List[str]) -> None:
        """
        Delete specified files from the directory.
        
        Args:
            day_dir: Directory containing the files
            files_to_delete: List of filenames to delete
        """
        for file in files_to_delete:
            try:
                file_path = os.path.join(day_dir, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted {file}")
            except Exception as e:
                print(f"Failed to delete {file}: {e}")
    
    def process_daily_videos(self, date_str: Optional[str] = None) -> bool:
        """
        Process all videos for a specific date: concatenate, upload to YouTube, and cleanup.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. If None, uses today's date.
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        if date_str is None:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        day_dir = os.path.join(config.DATA_DIR, date_str)
        
        if not os.path.exists(day_dir):
            print(f"No videos found for {date_str}")
            return False
        
        files = self.get_video_files(day_dir)
        
        if not files:
            print(f"No mp4 files to concatenate for {date_str}")
            return False
        
        print(f"Found {len(files)} video files for {date_str}")
        
        # Create output path for concatenated video
        output_filename = f"{date_str}_combined.mp4"
        output_path = os.path.join(day_dir, output_filename)
        
        # Concatenate videos
        if not self.concatenate_videos(day_dir, files, output_path):
            return False
        
        # Upload to YouTube
        title = f"{config.YOUTUBE_UPLOAD_TITLE_PREFIX} {date_str}"
        upload_success = self.youtube_uploader.upload_video(output_path, title)
        
        if upload_success:
            print("Upload successful, cleaning up local files...")
            # Delete all original files, the file list, and the concatenated video
            files_to_delete = files + ['files.txt', output_filename]
            self.cleanup_files(day_dir, files_to_delete)
            
            # Remove the directory if it's empty
            try:
                os.rmdir(day_dir)
                print(f"Removed empty directory {day_dir}")
            except OSError:
                print(f"Directory {day_dir} not empty, keeping it")
        else:
            print("Upload failed, keeping local files")
        
        return upload_success
