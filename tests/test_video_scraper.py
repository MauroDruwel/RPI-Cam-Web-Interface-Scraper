"""Tests for the video scraper module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from rpicam_scraper.video_scraper import VideoScraper


class TestVideoScraper:
    """Test cases for the VideoScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = VideoScraper()
    
    def test_parse_video_metadata_valid(self):
        """Test parsing valid video metadata."""
        html = """
        <fieldset class="fileicon">
            <legend>Video Info</legend>
            <a href="media/video001.mp4">001</a>
            <button name="delete1" value="thumb001">Delete</button>
            <span>26 MB 19s 2025-08-12 19:52:10</span>
        </fieldset>
        """
        soup = BeautifulSoup(html, 'html.parser')
        fieldset = soup.find('fieldset')
        
        result = self.scraper.parse_video_metadata(fieldset)
        
        assert result is not None
        assert result['video'] == 'media/video001.mp4'
        assert result['thumbnail'] == 'thumb001'
        assert result['title'] == '2025-08-12 19:52:10'
        assert result['size'] == '26 MB'
        assert result['duration'] == '19s'
        assert result['date'] == '2025-08-12'
        assert result['time'] == '19:52:10'
    
    def test_parse_video_metadata_invalid_href(self):
        """Test parsing with invalid href."""
        html = """
        <fieldset class="fileicon">
            <a href="invalid/file.txt">001</a>
        </fieldset>
        """
        soup = BeautifulSoup(html, 'html.parser')
        fieldset = soup.find('fieldset')
        
        result = self.scraper.parse_video_metadata(fieldset)
        
        assert result is None
    
    def test_parse_video_metadata_no_href(self):
        """Test parsing with no href."""
        html = """
        <fieldset class="fileicon">
            <span>No video link</span>
        </fieldset>
        """
        soup = BeautifulSoup(html, 'html.parser')
        fieldset = soup.find('fieldset')
        
        result = self.scraper.parse_video_metadata(fieldset)
        
        assert result is None
    
    def test_parse_video_metadata_missing_datetime(self):
        """Test parsing with missing date/time information."""
        html = """
        <fieldset class="fileicon">
            <a href="media/video001.mp4">001</a>
            <button name="delete1" value="thumb001">Delete</button>
            <span>26 MB 19s</span>
        </fieldset>
        """
        soup = BeautifulSoup(html, 'html.parser')
        fieldset = soup.find('fieldset')
        
        result = self.scraper.parse_video_metadata(fieldset)
        
        assert result is not None
        assert result['title'] == 'Unknown DateTime'
        assert result['date'] == ''
        assert result['time'] == ''
    
    @patch('rpicam_scraper.video_scraper.config')
    @patch('requests.Session.get')
    def test_fetch_video_list_success(self, mock_get, mock_config):
        """Test successful video list fetching."""
        mock_config.preview_url = "http://test.com/preview.php"
        mock_config.REQUEST_TIMEOUT = 30
        mock_config.MAX_RETRIES = 5
        
        html_content = """
        <html>
            <body>
                <fieldset class="fileicon">
                    <a href="media/video001.mp4">001</a>
                    <button name="delete1" value="thumb001">Delete</button>
                    <span>26 MB 19s 2025-08-12 19:52:10</span>
                </fieldset>
                <fieldset class="fileicon">
                    <a href="media/video002.mp4">002</a>
                    <button name="delete1" value="thumb002">Delete</button>
                    <span>30 MB 22s 2025-08-12 20:15:30</span>
                </fieldset>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        videos = self.scraper.fetch_video_list()
        
        assert len(videos) == 2
        assert videos[0]['video'] == 'media/video001.mp4'
        assert videos[1]['video'] == 'media/video002.mp4'
        mock_get.assert_called_once_with("http://test.com/preview.php", timeout=30)
    
    @patch('rpicam_scraper.video_scraper.config')
    @patch('requests.Session.get')
    def test_fetch_video_list_http_error(self, mock_get, mock_config):
        """Test video list fetching with HTTP error."""
        mock_config.preview_url = "http://test.com/preview.php"
        mock_config.REQUEST_TIMEOUT = 30
        mock_config.MAX_RETRIES = 2
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        videos = self.scraper.fetch_video_list()
        
        assert videos == []
        assert mock_get.call_count == 2  # Should retry
    
    @patch('rpicam_scraper.video_scraper.config')
    @patch('requests.Session.get')
    @patch('builtins.open', create=True)
    def test_download_video_success(self, mock_open, mock_get, mock_config):
        """Test successful video download."""
        mock_config.BASE_URL = "http://test.com/"
        mock_config.DOWNLOAD_TIMEOUT = 60
        mock_config.DOWNLOAD_CHUNK_SIZE = 8192
        mock_config.MAX_RETRIES = 5
        
        video_meta = {
            'video': 'media/video001.mp4',
            'thumbnail': 'thumb001'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_get.return_value = mock_response
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = self.scraper.download_video(video_meta, "/test/dir")
        
        assert result is True
        mock_get.assert_called_once_with(
            "http://test.com/media/video001.mp4",
            stream=True,
            timeout=60
        )
        mock_file.write.assert_any_call(b'chunk1')
        mock_file.write.assert_any_call(b'chunk2')
    
    @patch('rpicam_scraper.video_scraper.config')
    @patch('requests.Session.post')
    def test_delete_video_from_server_success(self, mock_post, mock_config):
        """Test successful video deletion from server."""
        mock_config.preview_url = "http://test.com/preview.php"
        mock_config.REQUEST_TIMEOUT = 30
        mock_config.MAX_RETRIES = 5
        
        video_meta = {'thumbnail': 'thumb001'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.scraper.delete_video_from_server(video_meta)
        
        assert result is True
        mock_post.assert_called_once_with(
            "http://test.com/preview.php",
            data={'delete1': 'thumb001'},
            timeout=30
        )
    
    def test_delete_video_from_server_no_thumbnail(self):
        """Test video deletion with no thumbnail."""
        video_meta = {}
        
        result = self.scraper.delete_video_from_server(video_meta)
        
        assert result is False
