"""Tests for the configuration module."""

import os
import pytest
from unittest.mock import patch

from rpicam_scraper.config import Config


class TestConfig:
    """Test cases for the Config class."""
    
    def test_config_initialization(self):
        """Test config initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.BASE_URL == ""
            assert config.YOUTUBE_CLIENT_SECRETS == "client_secrets.json"
            assert config.YOUTUBE_TOKEN_PATH == "token.pickle"
            assert config.DATA_DIR == "/data/videos"
            assert config.MAX_RETRIES == 5
            assert config.REQUEST_TIMEOUT == 30
    
    def test_config_with_environment_variables(self):
        """Test config with environment variables set."""
        env_vars = {
            "RPICAM_BASE_URL": "https://test.example.com/",
            "YOUTUBE_CLIENT_SECRETS": "test_secret.json",
            "RPICAM_DATA_DIR": "/test/data",
            "RPICAM_MAX_RETRIES": "10"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.BASE_URL == "https://test.example.com/"
            assert config.YOUTUBE_CLIENT_SECRETS == "test_secret.json"
            assert config.DATA_DIR == "/test/data"
            assert config.MAX_RETRIES == 10
    
    def test_preview_url_property(self):
        """Test the preview_url property."""
        env_vars = {"RPICAM_BASE_URL": "https://test.example.com/path"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.preview_url == "https://test.example.com/path/preview.php"
    
    def test_preview_url_with_trailing_slash(self):
        """Test preview_url property with trailing slash in base URL."""
        env_vars = {"RPICAM_BASE_URL": "https://test.example.com/path/"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.preview_url == "https://test.example.com/path/preview.php"
    
    def test_preview_url_without_base_url(self):
        """Test preview_url property raises error when base URL is missing."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            with pytest.raises(ValueError, match="RPICAM_BASE_URL environment variable is required"):
                _ = config.preview_url
    
    def test_youtube_tags_list_property(self):
        """Test the youtube_tags_list property."""
        env_vars = {"YOUTUBE_UPLOAD_TAGS": "tag1,tag2, tag3 ,tag4"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.youtube_tags_list == ["tag1", "tag2", "tag3", "tag4"]
    
    def test_youtube_tags_list_empty(self):
        """Test youtube_tags_list with empty tags."""
        env_vars = {"YOUTUBE_UPLOAD_TAGS": ""}
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.youtube_tags_list == []
    
    def test_validate_success(self):
        """Test successful validation."""
        env_vars = {"RPICAM_BASE_URL": "https://test.example.com/"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            config.validate()  # Should not raise
    
    def test_validate_missing_base_url(self):
        """Test validation fails when base URL is missing."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            with pytest.raises(ValueError, match="Missing required environment variables: RPICAM_BASE_URL"):
                config.validate()
    
    def test_integer_conversion(self):
        """Test integer environment variable conversion."""
        env_vars = {
            "RPICAM_MAX_RETRIES": "3",
            "RPICAM_REQUEST_TIMEOUT": "45",
            "RPICAM_DOWNLOAD_TIMEOUT": "120",
            "RPICAM_DOWNLOAD_CHUNK_SIZE": "16384"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()
            assert config.MAX_RETRIES == 3
            assert config.REQUEST_TIMEOUT == 45
            assert config.DOWNLOAD_TIMEOUT == 120
            assert config.DOWNLOAD_CHUNK_SIZE == 16384
