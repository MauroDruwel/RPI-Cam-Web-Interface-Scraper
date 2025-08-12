"""
Scheduler module for automatic video scraping and processing.
"""

import datetime
import time
import threading
from typing import Optional

from .config import config
from .video_scraper import VideoScraper
from .video_processor import VideoProcessor


class RPiCamScheduler:
    """Scheduler for automatic video scraping and daily processing."""
    
    def __init__(self):
        self.scraper = VideoScraper()
        self.processor = VideoProcessor()
        self.running = False
        self.last_daily_process = None
        
    def should_run_daily_process(self) -> bool:
        """Check if it's time to run the daily process."""
        now = datetime.datetime.now()
        
        # Parse the configured time (HH:MM format)
        try:
            hour, minute = map(int, config.DAILY_PROCESS_TIME.split(':'))
        except (ValueError, AttributeError):
            hour, minute = 23, 59  # Default to 23:59
        
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If target time has passed today and we haven't run today
        today = now.date()
        if (now >= target_time and 
            (self.last_daily_process is None or self.last_daily_process != today)):
            return True
        
        return False
    
    def run_scraping(self) -> None:
        """Run video scraping."""
        try:
            print(f"[{datetime.datetime.now()}] Starting scheduled video scraping...")
            self.scraper.fetch_and_clean()
            print(f"[{datetime.datetime.now()}] Video scraping completed.")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Error during scraping: {e}")
    
    def run_daily_process(self) -> None:
        """Run daily video processing."""
        try:
            print(f"[{datetime.datetime.now()}] Starting scheduled daily processing...")
            success = self.processor.process_daily_videos()
            if success:
                print(f"[{datetime.datetime.now()}] Daily processing completed successfully.")
                self.last_daily_process = datetime.datetime.now().date()
            else:
                print(f"[{datetime.datetime.now()}] Daily processing failed.")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Error during daily processing: {e}")
    
    def run_scheduler(self) -> None:
        """Main scheduler loop."""
        print(f"[{datetime.datetime.now()}] Scheduler started.")
        print(f"  - Scraping interval: {config.SCRAPE_INTERVAL_MINUTES} minutes")
        print(f"  - Daily processing time: {config.DAILY_PROCESS_TIME}")
        
        last_scrape = datetime.datetime.min
        scrape_interval = datetime.timedelta(minutes=config.SCRAPE_INTERVAL_MINUTES)
        
        while self.running:
            now = datetime.datetime.now()
            
            # Check if it's time for scraping
            if now - last_scrape >= scrape_interval:
                self.run_scraping()
                last_scrape = now
            
            # Check if it's time for daily processing
            if self.should_run_daily_process():
                self.run_daily_process()
            
            # Sleep for 1 minute before checking again
            time.sleep(60)
        
        print(f"[{datetime.datetime.now()}] Scheduler stopped.")
    
    def start(self) -> None:
        """Start the scheduler in a separate thread."""
        if self.running:
            print("Scheduler is already running.")
            return
        
        self.running = True
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        return scheduler_thread
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
