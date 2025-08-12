# RPI Camera Web Interface Scraper

![Build Status](https://github.com/MauroDruwel/RPI-Cam-Web-Interface-Scraper/workflows/Build%20and%20Test/badge.svg)
![Docker Image](https://github.com/MauroDruwel/RPI-Cam-Web-Interface-Scraper/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)

A containerized Python application that automatically downloads videos from an RPI camera web interface, concatenates daily footage, and uploads to YouTube. **Designed to run in Docker with automatic scheduling.**

## Features

- **🤖 Automatic Scheduling**: Built-in scheduler runs every 15 minutes (configurable)
- **📹 Video Scraping**: Downloads new videos from RPI camera web interface  
- **🧹 Server Cleanup**: Automatically deletes videos from server after download
- **📅 Daily Processing**: Concatenates all videos from a day at configurable time
- **📺 YouTube Upload**: Automatically uploads daily compilations to YouTube
- **⚙️ Fully Configurable**: All settings via environment variables
- **🐳 Docker Native**: Designed to run in containers
- **🔄 Retry Logic**: Robust error handling with configurable retry attempts

## Quick Start

1. **Clone and setup:**
```bash
git clone https://github.com/MauroDruwel/RPI-Cam-Web-Interface-Scraper.git
cd RPI-Cam-Web-Interface-Scraper
```

2. **Configure environment variables in `docker-compose.yml`:**
```yaml
# Edit the environment section in docker-compose.yml
environment:
  - RPICAM_BASE_URL=https://your-camera-server.com/path/
  # Adjust scheduling if needed
  - RPICAM_SCRAPE_INTERVAL_MINUTES=15
  - RPICAM_DAILY_PROCESS_TIME=23:59
```

3. **Setup YouTube API credentials:**
```bash
mkdir secrets
# Copy your client_secrets.json to the secrets/ directory
```

4. **Run with Docker:**
```bash
docker-compose up -d
```

That's it! The container will automatically:
- Scrape videos every 15 minutes
- Process and upload daily videos at 23:59
- Handle retries and errors gracefully

## Configuration

### Required Variables
- `RPICAM_BASE_URL`: Base URL of your RPI camera web interface

### Scheduling Configuration  
- `RPICAM_ENABLE_SCHEDULER`: Enable automatic scheduling (default: true)
- `RPICAM_SCRAPE_INTERVAL_MINUTES`: Minutes between scraping runs (default: 15)
- `RPICAM_DAILY_PROCESS_TIME`: Time for daily processing in HH:MM format (default: 23:59)

### Processing Configuration
- `RPICAM_DATA_DIR`: Directory to store videos (default: /data/videos)
- `RPICAM_MAX_RETRIES`: Maximum retry attempts (default: 5)
- `RPICAM_REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `RPICAM_DOWNLOAD_TIMEOUT`: Download timeout in seconds (default: 60)

### YouTube Configuration
- `YOUTUBE_CLIENT_SECRETS`: Path to YouTube client secrets file (default: client_secrets.json)
- `YOUTUBE_TOKEN_PATH`: Path to save YouTube auth token (default: token.pickle)
- `YOUTUBE_UPLOAD_TITLE_PREFIX`: Prefix for video titles (default: RPiCam)
- `YOUTUBE_UPLOAD_DESCRIPTION`: Description for uploaded videos
- `YOUTUBE_UPLOAD_TAGS`: Comma-separated tags for videos
- `YOUTUBE_UPLOAD_CATEGORY`: YouTube category ID (default: 22)
- `YOUTUBE_PRIVACY_STATUS`: Privacy status (default: unlisted)

## Usage

### Default (Automatic Scheduling)
```bash
# Start with automatic scheduling
docker-compose up -d

# Check logs
docker-compose logs -f rpicam-scraper
```

### Manual Operations
```bash
# One-time scrape
docker-compose run rpicam-scraper python src/main.py --mode scrape

# One-time daily processing
docker-compose run rpicam-scraper python src/main.py --mode daily

# Process specific date
docker-compose run rpicam-scraper python src/main.py --mode daily --date 2025-08-11

# Disable scheduler and run scrape only
docker-compose run -e RPICAM_ENABLE_SCHEDULER=false rpicam-scraper python src/main.py --mode scrape
```

### Container Management
```bash
# Stop the service
docker-compose down

# View logs
docker-compose logs rpicam-scraper

# Restart service
docker-compose restart rpicam-scraper

# Update and rebuild
git pull
docker-compose build
docker-compose up -d
```

## YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create OAuth 2.0 Client ID credentials for desktop application  
5. Download the JSON file and save as `secrets/client_secrets.json`

## Project Structure

```
├── src/
│   ├── main.py                 # Main entry point
│   └── rpicam_scraper/         # Main package
│       ├── config.py           # Configuration management
│       ├── scheduler.py        # Automatic scheduling
│       ├── video_scraper.py    # Video scraping and downloading
│       ├── video_processor.py  # Video concatenation and processing
│       └── youtube_uploader.py # YouTube authentication and upload
├── tests/                      # Test suite (basic Docker tests)
├── .github/workflows/          # GitHub Actions for CI/CD
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Service definition
└── requirements.txt            # Python dependencies
```

## Requirements

- Docker and Docker Compose
- YouTube API credentials
- Internet connection  
- RPI camera web interface

## Monitoring

The scheduler provides detailed logging:

```bash
# Follow logs in real-time
docker-compose logs -f rpicam-scraper

# Check last 50 lines
docker-compose logs --tail=50 rpicam-scraper
```

Log messages include:
- Scheduler start/stop events
- Scraping operations with timestamps
- Daily processing results  
- Error messages with retry attempts
- YouTube upload progress

## Troubleshooting

### Common Issues

1. **No videos found**: Check `RPICAM_BASE_URL` is correct and accessible
2. **YouTube upload fails**: Verify `client_secrets.json` is in `secrets/` directory
3. **Permission errors**: Ensure `./data` directory is writable
4. **FFmpeg errors**: Container includes ffmpeg, but check video file integrity

### Debug Commands

```bash
# Test configuration
docker-compose run rpicam-scraper python -c "
from rpicam_scraper.config import config
config.validate()
print('Config OK')
"

# Test connection to camera
docker-compose run rpicam-scraper python -c "
import requests
from rpicam_scraper.config import config
r = requests.get(config.preview_url, timeout=10)
print(f'Camera response: {r.status_code}')
"

# Run in debug mode
docker-compose run rpicam-scraper python src/main.py --mode scrape
```

## Contributing

1. Fork the repository
2. Make your changes
3. Test with `docker build -t test .`
4. Submit a pull request

## License

See LICENSE file for details.
