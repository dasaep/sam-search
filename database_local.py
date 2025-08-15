"""
Database module with local MongoDB fallback
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
import logging

log = logging.getLogger("database")


class OpportunityDB:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "sam_opportunities"):
        """Initialize with local MongoDB by default"""
        
        log.info(f"Connecting to MongoDB...")
        log.info(f"Database: {db_name}")
        
        try:
            # Simple connection without SRV
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=2000,  # 2 second timeout for local
                connectTimeoutMS=2000,
                socketTimeoutMS=2000,
                directConnection=True  # For local MongoDB
            )
            
            # Test the connection
            self.client.admin.command('ping')
            log.info("Successfully connected to MongoDB")
            
            self.db: Database = self.client[db_name]
            self.opportunities: Collection = self.db.opportunities
            self.capabilities: Collection = self.db.capabilities
            self.matches: Collection = self.db.matches
            
            log.info("Database initialization complete")
            
        except Exception as e:
            log.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _setup_indexes(self):
        """Create indexes for better query performance"""
        try:
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
        except Exception as e:
            log.warning(f"Could not create indexes: {e}")
    
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