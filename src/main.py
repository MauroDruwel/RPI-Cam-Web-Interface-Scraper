"""
Main entry point for the RPI Camera Web Interface Scraper.
"""

import argparse
import datetime
import signal
import sys
import time
from typing import Optional

from rpicam_scraper.config import config
from rpicam_scraper.video_scraper import VideoScraper
from rpicam_scraper.video_processor import VideoProcessor
from rpicam_scraper.scheduler import RPiCamScheduler


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="RPI Camera Web Interface Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with scheduler (default)
  python main.py --mode scrape      # One-time scrape
  python main.py --mode daily       # One-time daily processing
  python main.py --mode daily --date 2025-08-11  # Process specific date
  python main.py --mode scheduler   # Run scheduler explicitly
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["scrape", "daily", "scheduler"],
        default="scheduler" if config.ENABLE_SCHEDULER else "scrape",
        help="Operation mode: 'scrape' for one-time scrape, 'daily' for one-time processing, 'scheduler' for automatic scheduling"
    )
    
    parser.add_argument(
        "--date",
        type=str,
        help="Date to process in YYYY-MM-DD format (only used with --mode daily)"
    )
    
    return parser


def validate_date_format(date_str: str) -> bool:
    """Validate date string format."""
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)


def main():
    """Main function."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    try:
        # Validate configuration
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Validate date format if provided
    if args.date and not validate_date_format(args.date):
        print("Error: Date must be in YYYY-MM-DD format")
        sys.exit(1)
    
    try:
        if args.mode == "scrape":
            print("Starting video scraping and download...")
            scraper = VideoScraper()
            scraper.fetch_and_clean()
            print("Video scraping completed.")
            
        elif args.mode == "daily":
            print("Starting daily video processing...")
            if args.date:
                print(f"Processing videos for date: {args.date}")
            else:
                print("Processing today's videos")
                
            processor = VideoProcessor()
            success = processor.process_daily_videos(args.date)
            
            if success:
                print("Daily video processing completed successfully.")
            else:
                print("Daily video processing failed.")
                sys.exit(1)
        
        elif args.mode == "scheduler":
            print("Starting scheduler...")
            scheduler = RPiCamScheduler()
            scheduler.start()
            
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping scheduler...")
                scheduler.stop()
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
