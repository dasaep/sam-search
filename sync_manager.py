"""
Opportunity Sync Manager with Throttling and Incremental Updates
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import json
import yaml

import client
from client.rest import ApiException
from database import OpportunityDB

log = logging.getLogger("sync_manager")
logging.basicConfig(level=logging.INFO)


class SyncManager:
    def __init__(self, db: OpportunityDB, sam_api_key: str):
        self.db = db
        self.sam_api_key = sam_api_key
        self.config = self._load_config()
        self.sync_state = self._load_sync_state()
        
    def _load_config(self) -> dict:
        """Load configuration from config.yaml"""
        with open("config.yaml", "r") as file:
            return yaml.load(file, Loader=yaml.FullLoader)
    
    def _load_sync_state(self) -> dict:
        """Load sync state from database or file"""
        try:
            # Try to get from database
            state_doc = self.db.db.sync_state.find_one({"_id": "main"})
            if state_doc:
                return state_doc
        except:
            pass
        
        # Default state
        return {
            "_id": "main",
            "last_sync_date": None,
            "last_opportunity_id": None,
            "total_synced": 0,
            "last_sync_timestamp": None
        }
    
    def _save_sync_state(self):
        """Save sync state to database"""
        self.sync_state["last_sync_timestamp"] = datetime.now(timezone.utc)
        self.db.db.sync_state.replace_one(
            {"_id": "main"},
            self.sync_state,
            upsert=True
        )
    
    def search_opportunities(
        self,
        from_date: str,
        to_date: str,
        naics: str,
        limit: int = 90,
        offset: int = 0
    ) -> List[Dict]:
        """Search opportunities with pagination support"""
        
        api_config = client.Configuration()
        api_config.host = self.config["sam_url"]
        api_client = client.ApiClient(api_config)
        api_instance = client.SamApi(api_client)
        
        try:
            # Add offset parameter for pagination
            api_response = api_instance.search(
                api_key=self.sam_api_key,
                posted_from=from_date,
                posted_to=to_date,
                limit=limit,
                naics=naics,
                offset=offset
            )
            
            return api_response.to_dict()["value"]
            
        except ApiException as e:
            log.exception(f"Exception when calling SamApi->search: {e}")
            return []
    
    def incremental_sync(self, max_opportunities: int = 90) -> Dict[str, Any]:
        """
        Perform incremental sync with throttling
        - Fetches only new opportunities since last sync
        - Limits to max_opportunities per run
        - Updates sync state
        """
        
        log.info("Starting incremental sync...")
        
        # Determine date range
        if self.sync_state["last_sync_date"]:
            from_date = datetime.fromisoformat(self.sync_state["last_sync_date"])
            # Add 1 day to avoid duplicates
            from_date = from_date + timedelta(days=1)
        else:
            # First sync - go back 30 days
            from_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        to_date = datetime.now(timezone.utc)
        
        from_date_str = from_date.strftime("%m/%d/%Y")
        to_date_str = to_date.strftime("%m/%d/%Y")
        
        log.info(f"Fetching opportunities from {from_date_str} to {to_date_str}")
        
        all_new_opportunities = []
        opportunities_per_naics = max_opportunities // len(self.config["naics"])
        
        for naics in self.config["naics"]:
            log.info(f"Fetching NAICS {naics['code']}: {naics['desc']}")
            
            opportunities = self.search_opportunities(
                from_date_str,
                to_date_str,
                naics["code"],
                limit=opportunities_per_naics
            )
            
            for opp in opportunities:
                # Check if we already have this opportunity
                existing = self.db.opportunities.find_one({"url": opp.get("url")})
                if not existing:
                    opp["naics_desc"] = naics["desc"]
                    opp["fetched_at"] = datetime.now(timezone.utc)
                    all_new_opportunities.append(opp)
            
            # Throttle between NAICS searches (2 seconds)
            time.sleep(2)
        
        # Store new opportunities
        if all_new_opportunities:
            count = self.db.bulk_upsert_opportunities(all_new_opportunities)
            log.info(f"Stored {count} new opportunities")
            
            # Update sync state
            self.sync_state["last_sync_date"] = to_date.isoformat()
            self.sync_state["total_synced"] += count
            self._save_sync_state()
        else:
            log.info("No new opportunities found")
        
        return {
            "new_opportunities": len(all_new_opportunities),
            "from_date": from_date_str,
            "to_date": to_date_str,
            "total_synced": self.sync_state["total_synced"]
        }
    
    def full_sync(self, days_back: int = 7, batch_size: int = 90) -> Dict[str, Any]:
        """
        Perform full sync with batching
        """
        log.info(f"Starting full sync for last {days_back} days")
        
        from_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        to_date = datetime.now(timezone.utc)
        
        from_date_str = from_date.strftime("%m/%d/%Y")
        to_date_str = to_date.strftime("%m/%d/%Y")
        
        total_synced = 0
        
        for naics in self.config["naics"]:
            offset = 0
            naics_total = 0
            
            while True:
                log.info(f"Fetching NAICS {naics['code']}, offset {offset}")
                
                opportunities = self.search_opportunities(
                    from_date_str,
                    to_date_str,
                    naics["code"],
                    limit=batch_size,
                    offset=offset
                )
                
                if not opportunities:
                    break
                
                # Process and store
                for opp in opportunities:
                    opp["naics_desc"] = naics["desc"]
                    opp["fetched_at"] = datetime.now(timezone.utc)
                
                count = self.db.bulk_upsert_opportunities(opportunities)
                naics_total += count
                offset += batch_size
                
                # Throttle (3 seconds between batches)
                time.sleep(3)
                
                # Stop if we've hit our limit for this run
                if naics_total >= batch_size * 3:
                    log.info(f"Reached batch limit for NAICS {naics['code']}")
                    break
            
            total_synced += naics_total
        
        # Update sync state
        self.sync_state["last_sync_date"] = to_date.isoformat()
        self.sync_state["total_synced"] = total_synced
        self._save_sync_state()
        
        return {
            "total_synced": total_synced,
            "from_date": from_date_str,
            "to_date": to_date_str
        }