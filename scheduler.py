"""
Scheduler for automated opportunity syncing
"""

import schedule
import time
import logging
from datetime import datetime
import threading
import os
import sys

from database import OpportunityDB
from sync_manager import SyncManager
from config_db import MONGODB_CONFIG

log = logging.getLogger("scheduler")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OpportunityScheduler:
    def __init__(self, sam_api_key: str):
        self.sam_api_key = sam_api_key
        self.db = None
        self.sync_manager = None
        self.running = False
        self.thread = None
        
    def initialize(self):
        """Initialize database and sync manager"""
        try:
            log.info("Initializing scheduler...")
            self.db = OpportunityDB(
                connection_string=MONGODB_CONFIG["connection_string"],
                db_name=MONGODB_CONFIG["database_name"]
            )
            self.sync_manager = SyncManager(self.db, self.sam_api_key)
            log.info("Scheduler initialized successfully")
            return True
        except Exception as e:
            log.error(f"Failed to initialize scheduler: {e}")
            return False
    
    def sync_job(self):
        """Job to run incremental sync"""
        try:
            log.info("Starting scheduled sync job...")
            result = self.sync_manager.incremental_sync(max_opportunities=90)
            log.info(f"Sync job completed: {result}")
            
            # Store job result
            self.db.db.sync_jobs.insert_one({
                "executed_at": datetime.utcnow(),
                "status": "success",
                "result": result
            })
            
        except Exception as e:
            log.error(f"Sync job failed: {e}")
            
            # Store failure
            self.db.db.sync_jobs.insert_one({
                "executed_at": datetime.utcnow(),
                "status": "failed",
                "error": str(e)
            })
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self, interval_minutes: int = 15):
        """Start the scheduler"""
        if not self.initialize():
            log.error("Failed to start scheduler - initialization failed")
            return False
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.sync_job)
        
        # Run once immediately
        log.info("Running initial sync...")
        self.sync_job()
        
        # Start scheduler thread
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        
        log.info(f"Scheduler started - will sync every {interval_minutes} minutes")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        log.info("Stopping scheduler...")
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        schedule.clear()
        if self.db:
            self.db.close()
        log.info("Scheduler stopped")
    
    def get_job_history(self, limit: int = 10):
        """Get recent job history"""
        if not self.db:
            return []
        
        jobs = []
        cursor = self.db.db.sync_jobs.find().sort("executed_at", -1).limit(limit)
        
        for job in cursor:
            job["_id"] = str(job["_id"])
            jobs.append(job)
        
        return jobs


def main():
    """Main function to run scheduler as standalone service"""
    
    sam_api_key = os.getenv("SAM_API_KEY")
    if not sam_api_key:
        log.error("SAM_API_KEY environment variable not set")
        sys.exit(1)
    
    interval = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))
    
    scheduler = OpportunityScheduler(sam_api_key)
    
    try:
        if scheduler.start(interval_minutes=interval):
            log.info("Scheduler service running. Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            while True:
                time.sleep(60)
        else:
            log.error("Failed to start scheduler service")
            sys.exit(1)
            
    except KeyboardInterrupt:
        log.info("Received interrupt signal")
        scheduler.stop()
        log.info("Scheduler service stopped")


if __name__ == "__main__":
    main()