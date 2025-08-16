"""
Database module for managing SAM.gov opportunities and capabilities
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
import logging

log = logging.getLogger("database")


class OpportunityDB:
    def __init__(self, connection_string: str = None, db_name: str = "sam_opportunities"):
        # Use MongoDB Atlas connection string if not provided
        if not connection_string:
            connection_string = "mongodb+srv://Cluster08122:dVBYQ0R4aHZx@cluster08122.jkmqf6j.mongodb.net/?retryWrites=true&w=majority"
        
        log.info(f"Connecting to MongoDB Atlas...")
        log.info(f"Database: {db_name}")
        
        try:
            # Add timeout and serverSelectionTimeoutMS
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test the connection
            self.client.admin.command('ping')
            log.info("Successfully connected to MongoDB Atlas")
            
            self.db: Database = self.client[db_name]
            self.opportunities: Collection = self.db.opportunities
            self.capabilities: Collection = self.db.capabilities
            self.matches: Collection = self.db.matches
            self.hubspot_sync: Collection = self.db.hubspot_sync
            self.hubspot_config: Collection = self.db.hubspot_config
            
            log.info("Setting up database indexes...")
            self._setup_indexes()
            log.info("Database initialization complete")
            
        except Exception as e:
            log.error(f"Failed to connect to MongoDB Atlas: {e}")
            log.error("Make sure your IP is whitelisted in MongoDB Atlas Network Access")
            raise
    
    def _setup_indexes(self):
        """Create indexes for better query performance"""
        self.opportunities.create_index([("posted_date", DESCENDING)])
        self.opportunities.create_index([("due_date", ASCENDING)])
        self.opportunities.create_index([("naics", ASCENDING)])
        self.opportunities.create_index([("agency", ASCENDING)])
        self.opportunities.create_index([("set_aside", ASCENDING)])
        self.opportunities.create_index([("url", ASCENDING)], unique=True)
        
        self.capabilities.create_index([("name", ASCENDING)], unique=True)
        self.capabilities.create_index([("active", ASCENDING)])
        
        self.matches.create_index([("opportunity_id", ASCENDING)])
        self.matches.create_index([("capability_id", ASCENDING)])
        self.matches.create_index([("match_percentage", DESCENDING)])
        self.matches.create_index([("created_at", DESCENDING)])
        
        self.hubspot_sync.create_index([("opportunity_id", ASCENDING)], unique=True)
        self.hubspot_sync.create_index([("hubspot_deal_id", ASCENDING)])
        self.hubspot_sync.create_index([("sync_status", ASCENDING)])
        self.hubspot_sync.create_index([("last_sync", DESCENDING)])
    
    def upsert_opportunity(self, opportunity: Dict[str, Any]) -> str:
        """Insert or update an opportunity"""
        opportunity["last_updated"] = datetime.now(timezone.utc)
        opportunity["created_at"] = opportunity.get("created_at", datetime.now(timezone.utc))
        
        result = self.opportunities.update_one(
            {"url": opportunity["url"]},
            {"$set": opportunity},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            doc = self.opportunities.find_one({"url": opportunity["url"]})
            return str(doc["_id"])
    
    def bulk_upsert_opportunities(self, opportunities: List[Dict[str, Any]]) -> int:
        """Bulk insert or update opportunities"""
        count = 0
        for opp in opportunities:
            self.upsert_opportunity(opp)
            count += 1
        return count
    
    def get_opportunities(self, filters: Optional[Dict] = None, limit: int = 100, skip: int = 0) -> List[Dict]:
        """Get opportunities with optional filters"""
        query = filters or {}
        
        cursor = self.opportunities.find(query).sort("posted_date", DESCENDING).skip(skip).limit(limit)
        
        opportunities = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            opportunities.append(doc)
        
        return opportunities
    
    def get_opportunity_by_id(self, opp_id: str) -> Optional[Dict]:
        """Get a single opportunity by ID"""
        from bson import ObjectId
        
        doc = self.opportunities.find_one({"_id": ObjectId(opp_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    def create_capability(self, capability: Dict[str, Any]) -> str:
        """Create a new capability"""
        capability["created_at"] = datetime.now(timezone.utc)
        capability["active"] = capability.get("active", True)
        
        result = self.capabilities.insert_one(capability)
        return str(result.inserted_id)
    
    def update_capability(self, cap_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing capability"""
        from bson import ObjectId
        
        updates["updated_at"] = datetime.now(timezone.utc)
        result = self.capabilities.update_one(
            {"_id": ObjectId(cap_id)},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    def get_capabilities(self, active_only: bool = True) -> List[Dict]:
        """Get all capabilities"""
        query = {"active": True} if active_only else {}
        
        capabilities = []
        for doc in self.capabilities.find(query):
            doc["_id"] = str(doc["_id"])
            capabilities.append(doc)
        
        return capabilities
    
    def get_capability_by_id(self, cap_id: str) -> Optional[Dict]:
        """Get a single capability by ID"""
        from bson import ObjectId
        
        doc = self.capabilities.find_one({"_id": ObjectId(cap_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    def save_match(self, opportunity_id: str, capability_id: str, match_percentage: float, match_details: Dict) -> str:
        """Save a match between an opportunity and capability"""
        match = {
            "opportunity_id": opportunity_id,
            "capability_id": capability_id,
            "match_percentage": match_percentage,
            "match_details": match_details,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = self.matches.insert_one(match)
        return str(result.inserted_id)
    
    def get_matches_for_opportunity(self, opportunity_id: str) -> List[Dict]:
        """Get all capability matches for an opportunity"""
        matches = []
        for doc in self.matches.find({"opportunity_id": opportunity_id}).sort("match_percentage", DESCENDING):
            doc["_id"] = str(doc["_id"])
            
            capability = self.get_capability_by_id(doc["capability_id"])
            if capability:
                doc["capability"] = capability
            
            matches.append(doc)
        
        return matches
    
    def get_high_matches(self, threshold: float = 70.0, limit: int = 50) -> List[Dict]:
        """Get opportunities with high capability matches"""
        pipeline = [
            {"$match": {"match_percentage": {"$gte": threshold}}},
            {"$sort": {"created_at": -1, "match_percentage": -1}},
            {"$limit": limit},
            {"$group": {
                "_id": "$opportunity_id",
                "best_match": {"$first": "$$ROOT"}
            }}
        ]
        
        results = []
        for doc in self.matches.aggregate(pipeline):
            match = doc["best_match"]
            match["_id"] = str(match["_id"])
            
            opportunity = self.get_opportunity_by_id(match["opportunity_id"])
            capability = self.get_capability_by_id(match["capability_id"])
            
            if opportunity and capability:
                match["opportunity"] = opportunity
                match["capability"] = capability
                results.append(match)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        return {
            "total_opportunities": self.opportunities.count_documents({}),
            "total_capabilities": self.capabilities.count_documents({}),
            "active_capabilities": self.capabilities.count_documents({"active": True}),
            "total_matches": self.matches.count_documents({}),
            "high_matches": self.matches.count_documents({"match_percentage": {"$gte": 70}}),
            "recent_opportunities": self.opportunities.count_documents({
                "posted_date": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)}
            })
        }
    
    def close(self):
        """Close database connection"""
        self.client.close()
    
    # HubSpot Integration Methods
    
    def get_hubspot_sync_status(self, opportunity_id: str) -> Optional[Dict]:
        """Get HubSpot sync status for an opportunity"""
        doc = self.hubspot_sync.find_one({"opportunity_id": opportunity_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    def update_hubspot_sync_status(self, sync_record: Dict[str, Any]) -> bool:
        """Update HubSpot sync status for an opportunity"""
        sync_record["updated_at"] = datetime.now(timezone.utc)
        
        result = self.hubspot_sync.update_one(
            {"opportunity_id": sync_record["opportunity_id"]},
            {"$set": sync_record},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    def get_synced_opportunities(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all opportunities that have been synced to HubSpot"""
        query = filters or {}
        
        synced = []
        for doc in self.hubspot_sync.find(query):
            doc["_id"] = str(doc["_id"])
            synced.append(doc)
        
        return synced
    
    def get_opportunities_with_sync_status(self, filters: Optional[Dict] = None, limit: int = 100, skip: int = 0) -> List[Dict]:
        """Get opportunities with their HubSpot sync status"""
        pipeline = [
            {"$match": filters or {}},
            {"$sort": {"posted_date": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "hubspot_sync",
                    "localField": "_id",
                    "foreignField": "opportunity_id",
                    "as": "hubspot_sync"
                }
            },
            {
                "$addFields": {
                    "hubspot_sync": {"$arrayElemAt": ["$hubspot_sync", 0]}
                }
            }
        ]
        
        opportunities = []
        for doc in self.opportunities.aggregate(pipeline):
            doc["_id"] = str(doc["_id"])
            if doc.get("hubspot_sync"):
                doc["hubspot_sync"]["_id"] = str(doc["hubspot_sync"]["_id"])
            opportunities.append(doc)
        
        return opportunities
    
    def bulk_update_sync_status(self, sync_records: List[Dict[str, Any]]) -> int:
        """Bulk update HubSpot sync status for multiple opportunities"""
        count = 0
        for record in sync_records:
            if self.update_hubspot_sync_status(record):
                count += 1
        return count
    
    def save_hubspot_config(self, config: Dict[str, Any]) -> bool:
        """Save HubSpot configuration"""
        config["_id"] = "hubspot_config"  # Single document for config
        config["updated_at"] = datetime.now(timezone.utc)
        
        result = self.hubspot_config.replace_one(
            {"_id": "hubspot_config"},
            config,
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    def get_hubspot_config(self) -> Optional[Dict]:
        """Get HubSpot configuration"""
        doc = self.hubspot_config.find_one({"_id": "hubspot_config"})
        if doc:
            del doc["_id"]
        return doc
    
    def delete_hubspot_config(self) -> bool:
        """Delete HubSpot configuration"""
        result = self.hubspot_config.delete_one({"_id": "hubspot_config"})
        return result.deleted_count > 0
    
    def get_hubspot_sync_statistics(self) -> Dict:
        """Get HubSpot sync statistics"""
        total_synced = self.hubspot_sync.count_documents({})
        successful = self.hubspot_sync.count_documents({"sync_status": {"$in": ["created", "updated"]}})
        failed = self.hubspot_sync.count_documents({"sync_status": "error"})
        
        # Get last sync time
        last_sync = self.hubspot_sync.find_one(
            {},
            sort=[("last_sync", -1)]
        )
        
        return {
            "total_synced": total_synced,
            "successful": successful,
            "failed": failed,
            "last_sync": last_sync["last_sync"] if last_sync else None,
            "sync_percentage": (successful / total_synced * 100) if total_synced > 0 else 0
        }