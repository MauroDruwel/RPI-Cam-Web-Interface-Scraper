"""Tests for the YouTube uploader module."""

import os
import pytest
from unittest.mock import Mock, patch, mock_open

from rpicam_scraper.youtube_uploader import YouTubeUploader


class TestYouTubeUploader:
    """Test cases for the YouTubeUploader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.uploader = YouTubeUploader()
    
    @patch('rpicam_scraper.youtube_uploader.config')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('rpicam_scraper.youtube_uploader.build')
    def test_get_authenticated_service_existing_token(self, mock_build, mock_pickle, mock_file, mock_exists, mock_config):
        """Test authentication with existing valid token."""
        mock_config.YOUTUBE_TOKEN_PATH = "token.pickle"
        mock_exists.return_value = True
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle.return_value = mock_creds
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        result = self.uploader.get_authenticated_service()
        
        assert result == mock_service
        assert self.uploader.youtube_service == mock_service
        mock_exists.assert_called_once_with("token.pickle")
        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
    
    @patch('rpicam_scraper.youtube_uploader.config')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('pickle.dump')
    @patch('rpicam_scraper.youtube_uploader.build')
    @patch('rpicam_scraper.youtube_uploader.Request')
    def test_get_authenticated_service_expired_token(self, mock_request, mock_build, mock_dump, mock_pickle, mock_file, mock_exists, mock_config):
        """Test authentication with expired token that can be refreshed."""
        mock_config.YOUTUBE_TOKEN_PATH = "token.pickle"
        mock_exists.return_value = True
        
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token"
        mock_pickle.return_value = mock_creds
        
        # After refresh, token becomes valid
        def refresh_side_effect(request):
            mock_creds.valid = True
        mock_creds.refresh.side_effect = refresh_side_effect
        
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        result = self.uploader.get_authenticated_service()
        
        assert result == mock_service
        mock_creds.refresh.assert_called_once()
        mock_dump.assert_called_once()
    
    @patch('rpicam_scraper.youtube_uploader.config')
    @patch('os.path.exists')
    def test_get_authenticated_service_no_token(self, mock_exists, mock_config):
        """Test authentication with no existing token."""
        mock_config.YOUTUBE_TOKEN_PATH = "token.pickle"
        mock_exists.return_value = False
        
        with patch('rpicam_scraper.youtube_uploader.InstalledAppFlow') as mock_flow:
            with patch('rpicam_scraper.youtube_uploader.build') as mock_build:
                with patch('builtins.open', mock_open()):
                    with patch('pickle.dump'):
                        mock_config.YOUTUBE_CLIENT_SECRETS = "client_secret.json"
                        mock_config.YOUTUBE_SCOPES = ["scope1"]
                        
                        mock_creds = Mock()
                        mock_flow_instance = Mock()
                        mock_flow_instance.run_local_server.return_value = mock_creds
                        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
                        
                        mock_service = Mock()
                        mock_build.return_value = mock_service
                        
                        result = self.uploader.get_authenticated_service()
                        
                        assert result == mock_service
                        mock_flow.from_client_secrets_file.assert_called_once_with(
                            "client_secret.json", ["scope1"]
                        )
    
    @patch('rpicam_scraper.youtube_uploader.config')
    @patch('rpicam_scraper.youtube_uploader.MediaFileUpload')
    def test_upload_video_success(self, mock_media_upload, mock_config):
        """Test successful video upload."""
        mock_config.YOUTUBE_UPLOAD_DESCRIPTION = "Test description"
        mock_config.youtube_tags_list = ["tag1", "tag2"]
        mock_config.YOUTUBE_UPLOAD_CATEGORY = "22"
        mock_config.YOUTUBE_PRIVACY_STATUS = "unlisted"
        mock_config.MAX_RETRIES = 3
        
        # Set up mock YouTube service
        mock_service = Mock()
        self.uploader.youtube_service = mock_service
        
        # Mock the upload process
        mock_request = Mock()
        mock_service.videos().insert.return_value = mock_request
        
        # Mock successful upload with progress
        mock_status = Mock()
        mock_status.progress.return_value = 0.5
        mock_response = {"id": "test_video_id"}
        
        mock_request.next_chunk.side_effect = [
            (mock_status, None),  # First call with progress
            (None, mock_response)  # Second call with response
        ]
        
        result = self.uploader.upload_video("/test/video.mp4", "Test Title", "Test Description")
        
        assert result is True
        mock_service.videos().insert.assert_called_once()
        call_args = mock_service.videos().insert.call_args
        assert call_args[1]['body']['snippet']['title'] == "Test Title"
        assert call_args[1]['body']['snippet']['description'] == "Test Description"
    
    @patch('rpicam_scraper.youtube_uploader.config')
    @patch('rpicam_scraper.youtube_uploader.MediaFileUpload')
    @patch('time.sleep')
    def test_upload_video_rate_limit(self, mock_sleep, mock_media_upload, mock_config):
        """Test video upload with rate limit error."""
        mock_config.MAX_RETRIES = 2
        
        # Set up mock YouTube service
        mock_service = Mock()
        self.uploader.youtube_service = mock_service
        
        # Mock rate limit error
        mock_request = Mock()
        mock_service.videos().insert.return_value = mock_request
        
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.resp = Mock()
        rate_limit_error.resp.status = 403
        
        mock_request.next_chunk.side_effect = rate_limit_error
        
        result = self.uploader.upload_video("/test/video.mp4", "Test Title")
        
        assert result is False
        # Should sleep for 1 hour on rate limit
        mock_sleep.assert_called_with(3600)
    
    @patch('rpicam_scraper.youtube_uploader.config')
    @patch('rpicam_scraper.youtube_uploader.MediaFileUpload')
    @patch('time.sleep')
    def test_upload_video_generic_error(self, mock_sleep, mock_media_upload, mock_config):
        """Test video upload with generic error and retries."""
        mock_config.MAX_RETRIES = 3
        
        # Set up mock YouTube service
        mock_service = Mock()
        self.uploader.youtube_service = mock_service
        
        # Mock generic error
        mock_request = Mock()
        mock_service.videos().insert.return_value = mock_request
        mock_request.next_chunk.side_effect = Exception("Generic error")
        
        result = self.uploader.upload_video("/test/video.mp4", "Test Title")
        
        assert result is False
        # Should have made multiple attempts
        assert mock_service.videos().insert.call_count == 3
        # Should have slept with exponential backoff
        assert mock_sleep.call_count == 3
