"""Tests for the video processor module."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call

from rpicam_scraper.video_processor import VideoProcessor


class TestVideoProcessor:
    """Test cases for the VideoProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('rpicam_scraper.video_processor.YouTubeUploader'):
            self.processor = VideoProcessor()
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_video_files_success(self, mock_listdir, mock_exists):
        """Test getting video files from directory."""
        mock_exists.return_value = True
        mock_listdir.return_value = ['video1.mp4', 'video2.mp4', 'other.txt', 'video3.mp4']
        
        result = self.processor.get_video_files('/test/dir')
        
        assert result == ['video1.mp4', 'video2.mp4', 'video3.mp4']
        mock_exists.assert_called_once_with('/test/dir')
        mock_listdir.assert_called_once_with('/test/dir')
    
    @patch('os.path.exists')
    def test_get_video_files_directory_not_exists(self, mock_exists):
        """Test getting video files when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = self.processor.get_video_files('/nonexistent/dir')
        
        assert result == []
        mock_exists.assert_called_once_with('/nonexistent/dir')
    
    @patch('builtins.open', create=True)
    @patch('os.path.abspath')
    @patch('os.path.join')
    def test_create_ffmpeg_file_list(self, mock_join, mock_abspath, mock_open):
        """Test creating ffmpeg file list."""
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_abspath.side_effect = lambda x: f'/abs{x}'
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        files = ['video1.mp4', 'video2.mp4']
        result = self.processor.create_ffmpeg_file_list('/test/dir', files)
        
        assert result == '/test/dir/files.txt'
        mock_file.write.assert_has_calls([
            call("file '/abs/test/dir/video1.mp4'\n"),
            call("file '/abs/test/dir/video2.mp4'\n")
        ])
    
    @patch('rpicam_scraper.video_processor.config')
    @patch('subprocess.run')
    @patch.object(VideoProcessor, 'create_ffmpeg_file_list')
    def test_concatenate_videos_success(self, mock_create_list, mock_run, mock_config):
        """Test successful video concatenation."""
        mock_config.MAX_RETRIES = 3
        mock_create_list.return_value = '/test/dir/files.txt'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        files = ['video1.mp4', 'video2.mp4']
        result = self.processor.concatenate_videos('/test/dir', files, '/test/output.mp4')
        
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '/test/output.mp4' in call_args
    
    @patch('rpicam_scraper.video_processor.config')
    @patch('subprocess.run')
    @patch.object(VideoProcessor, 'create_ffmpeg_file_list')
    def test_concatenate_videos_failure(self, mock_create_list, mock_run, mock_config):
        """Test failed video concatenation."""
        mock_config.MAX_RETRIES = 2
        mock_create_list.return_value = '/test/dir/files.txt'
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "FFmpeg error"
        mock_run.return_value = mock_result
        
        files = ['video1.mp4', 'video2.mp4']
        result = self.processor.concatenate_videos('/test/dir', files, '/test/output.mp4')
        
        assert result is False
        assert mock_run.call_count == 2  # Should retry
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_files_success(self, mock_remove, mock_exists):
        """Test successful file cleanup."""
        mock_exists.return_value = True
        
        files = ['file1.txt', 'file2.txt']
        self.processor.cleanup_files('/test/dir', files)
        
        mock_remove.assert_has_calls([
            call('/test/dir/file1.txt'),
            call('/test/dir/file2.txt')
        ])
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_files_with_error(self, mock_remove, mock_exists):
        """Test file cleanup with errors."""
        mock_exists.return_value = True
        mock_remove.side_effect = [None, OSError("Permission denied")]
        
        files = ['file1.txt', 'file2.txt']
        # Should not raise exception
        self.processor.cleanup_files('/test/dir', files)
        
        assert mock_remove.call_count == 2
    
    @patch('rpicam_scraper.video_processor.config')
    @patch('datetime.datetime')
    @patch('os.path.exists')
    @patch.object(VideoProcessor, 'get_video_files')
    def test_process_daily_videos_no_directory(self, mock_get_files, mock_exists, mock_datetime, mock_config):
        """Test processing when directory doesn't exist."""
        mock_datetime.now.return_value.strftime.return_value = "2025-08-12"
        mock_config.DATA_DIR = "/data"
        mock_exists.return_value = False
        
        result = self.processor.process_daily_videos()
        
        assert result is False
        mock_exists.assert_called_once_with('/data/2025-08-12')
    
    @patch('rpicam_scraper.video_processor.config')
    @patch('datetime.datetime')
    @patch('os.path.exists')
    @patch.object(VideoProcessor, 'get_video_files')
    def test_process_daily_videos_no_files(self, mock_get_files, mock_exists, mock_datetime, mock_config):
        """Test processing when no video files exist."""
        mock_datetime.now.return_value.strftime.return_value = "2025-08-12"
        mock_config.DATA_DIR = "/data"
        mock_exists.return_value = True
        mock_get_files.return_value = []
        
        result = self.processor.process_daily_videos()
        
        assert result is False
    
    @patch('rpicam_scraper.video_processor.config')
    @patch('os.path.exists')
    @patch.object(VideoProcessor, 'get_video_files')
    @patch.object(VideoProcessor, 'concatenate_videos')
    @patch.object(VideoProcessor, 'cleanup_files')
    @patch('os.rmdir')
    def test_process_daily_videos_success(self, mock_rmdir, mock_cleanup, mock_concat, mock_get_files, mock_exists, mock_config):
        """Test successful daily video processing."""
        mock_config.DATA_DIR = "/data"
        mock_config.YOUTUBE_UPLOAD_TITLE_PREFIX = "RPiCam"
        mock_exists.return_value = True
        mock_get_files.return_value = ['video1.mp4', 'video2.mp4']
        mock_concat.return_value = True
        
        # Mock YouTube uploader
        self.processor.youtube_uploader.upload_video.return_value = True
        
        result = self.processor.process_daily_videos("2025-08-12")
        
        assert result is True
        mock_concat.assert_called_once()
        self.processor.youtube_uploader.upload_video.assert_called_once_with(
            '/data/2025-08-12/2025-08-12_combined.mp4',
            'RPiCam 2025-08-12'
        )
