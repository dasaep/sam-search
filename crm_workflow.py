"""
CRM Workflow System for Opportunity Management
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

log = logging.getLogger("crm_workflow")


class OpportunityStage(Enum):
    """CRM stages for opportunity tracking"""
    DISCOVERED = "discovered"
    REVIEWING = "reviewing"
    QUALIFIED = "qualified"
    PROPOSAL_PREP = "proposal_prep"
    SUBMITTED = "submitted"
    AWARDED = "awarded"
    LOST = "lost"
    DECLINED = "declined"


class CRMWorkflow:
    def __init__(self, db):
        self.db = db
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure CRM collections exist"""
        # Create indexes for CRM collections
        self.db.db.opportunity_tracking.create_index([("opportunity_id", 1)])
        self.db.db.opportunity_tracking.create_index([("stage", 1)])
        self.db.db.opportunity_tracking.create_index([("assigned_to", 1)])
        
        self.db.db.opportunity_documents.create_index([("opportunity_id", 1)])
        self.db.db.opportunity_documents.create_index([("document_type", 1)])
        
        self.db.db.opportunity_activities.create_index([("opportunity_id", 1)])
        self.db.db.opportunity_activities.create_index([("activity_date", -1)])
    
    def create_opportunity_tracking(self, opportunity_id: str, initial_data: Dict = None) -> str:
        """Create CRM tracking record for an opportunity"""
        
        tracking = {
            "opportunity_id": opportunity_id,
            "stage": OpportunityStage.DISCOVERED.value,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "assigned_to": initial_data.get("assigned_to") if initial_data else None,
            "priority": initial_data.get("priority", "medium") if initial_data else "medium",
            "estimated_value": initial_data.get("estimated_value") if initial_data else None,
            "win_probability": initial_data.get("win_probability", 0) if initial_data else 0,
            "notes": initial_data.get("notes", []) if initial_data else [],
            "tags": initial_data.get("tags", []) if initial_data else [],
            "custom_fields": initial_data.get("custom_fields", {}) if initial_data else {},
            "stage_history": [
                {
                    "stage": OpportunityStage.DISCOVERED.value,
                    "entered_at": datetime.now(timezone.utc),
                    "entered_by": initial_data.get("entered_by") if initial_data else "system"
                }
            ]
        }
        
        result = self.db.db.opportunity_tracking.insert_one(tracking)
        
        # Log activity
        self.log_activity(
            opportunity_id,
            "tracking_created",
            "Opportunity tracking created",
            {"initial_stage": OpportunityStage.DISCOVERED.value}
        )
        
        return str(result.inserted_id)
    
    def update_stage(
        self,
        opportunity_id: str,
        new_stage: str,
        user: str = "system",
        notes: str = None
    ) -> bool:
        """Update opportunity stage"""
        
        # Validate stage
        if new_stage not in [s.value for s in OpportunityStage]:
            raise ValueError(f"Invalid stage: {new_stage}")
        
        # Get current tracking
        tracking = self.db.db.opportunity_tracking.find_one({"opportunity_id": opportunity_id})
        
        if not tracking:
            # Create new tracking if doesn't exist
            self.create_opportunity_tracking(opportunity_id)
            tracking = self.db.db.opportunity_tracking.find_one({"opportunity_id": opportunity_id})
        
        old_stage = tracking.get("stage")
        
        # Update stage
        update = {
            "$set": {
                "stage": new_stage,
                "updated_at": datetime.now(timezone.utc)
            },
            "$push": {
                "stage_history": {
                    "stage": new_stage,
                    "entered_at": datetime.now(timezone.utc),
                    "entered_by": user,
                    "notes": notes
                }
            }
        }
        
        if notes:
            update["$push"]["notes"] = {
                "text": notes,
                "created_at": datetime.now(timezone.utc),
                "created_by": user
            }
        
        result = self.db.db.opportunity_tracking.update_one(
            {"opportunity_id": opportunity_id},
            update
        )
        
        # Log activity
        self.log_activity(
            opportunity_id,
            "stage_changed",
            f"Stage changed from {old_stage} to {new_stage}",
            {"old_stage": old_stage, "new_stage": new_stage, "user": user}
        )
        
        return result.modified_count > 0
    
    def add_document(
        self,
        opportunity_id: str,
        document_name: str,
        document_type: str,
        document_url: str,
        metadata: Dict = None
    ) -> str:
        """Add document to opportunity"""
        
        document = {
            "opportunity_id": opportunity_id,
            "document_name": document_name,
            "document_type": document_type,
            "document_url": document_url,
            "uploaded_at": datetime.now(timezone.utc),
            "metadata": metadata or {},
            "extracted_text": None,  # For future OCR/text extraction
            "analysis": None  # For future AI analysis
        }
        
        result = self.db.db.opportunity_documents.insert_one(document)
        
        # Log activity
        self.log_activity(
            opportunity_id,
            "document_added",
            f"Document added: {document_name}",
            {"document_type": document_type, "document_id": str(result.inserted_id)}
        )
        
        return str(result.inserted_id)
    
    def get_documents(self, opportunity_id: str) -> List[Dict]:
        """Get all documents for an opportunity"""
        
        documents = []
        for doc in self.db.db.opportunity_documents.find({"opportunity_id": opportunity_id}):
            doc["_id"] = str(doc["_id"])
            documents.append(doc)
        
        return documents
    
    def log_activity(
        self,
        opportunity_id: str,
        activity_type: str,
        description: str,
        metadata: Dict = None
    ):
        """Log an activity for an opportunity"""
        
        activity = {
            "opportunity_id": opportunity_id,
            "activity_type": activity_type,
            "description": description,
            "activity_date": datetime.now(timezone.utc),
            "metadata": metadata or {}
        }
        
        self.db.db.opportunity_activities.insert_one(activity)
    
    def get_activities(
        self,
        opportunity_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get activity history for an opportunity"""
        
        activities = []
        cursor = self.db.db.opportunity_activities.find(
            {"opportunity_id": opportunity_id}
        ).sort("activity_date", -1).limit(limit)
        
        for activity in cursor:
            activity["_id"] = str(activity["_id"])
            activities.append(activity)
        
        return activities
    
    def get_tracking(self, opportunity_id: str) -> Optional[Dict]:
        """Get CRM tracking data for an opportunity"""
        
        tracking = self.db.db.opportunity_tracking.find_one({"opportunity_id": opportunity_id})
        if tracking:
            tracking["_id"] = str(tracking["_id"])
        
        return tracking
    
    def get_opportunities_by_stage(self, stage: str) -> List[Dict]:
        """Get all opportunities in a specific stage"""
        
        opportunities = []
        
        # Get tracking records
        for tracking in self.db.db.opportunity_tracking.find({"stage": stage}):
            # Get opportunity details
            opp = self.db.get_opportunity_by_id(tracking["opportunity_id"])
            if opp:
                opp["crm_tracking"] = tracking
                opp["crm_tracking"]["_id"] = str(tracking["_id"])
                opportunities.append(opp)
        
        return opportunities
    
    def update_opportunity_fields(
        self,
        opportunity_id: str,
        fields: Dict[str, Any]
    ) -> bool:
        """Update CRM fields for an opportunity"""
        
        allowed_fields = [
            "assigned_to", "priority", "estimated_value",
            "win_probability", "tags", "custom_fields"
        ]
        
        update_fields = {
            k: v for k, v in fields.items() if k in allowed_fields
        }
        
        if not update_fields:
            return False
        
        update_fields["updated_at"] = datetime.now(timezone.utc)
        
        result = self.db.db.opportunity_tracking.update_one(
            {"opportunity_id": opportunity_id},
            {"$set": update_fields}
        )
        
        # Log activity
        self.log_activity(
            opportunity_id,
            "fields_updated",
            "CRM fields updated",
            {"updated_fields": list(update_fields.keys())}
        )
        
        return result.modified_count > 0
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary of opportunities by stage"""
        
        pipeline = []
        
        for stage in OpportunityStage:
            count = self.db.db.opportunity_tracking.count_documents({"stage": stage.value})
            
            # Calculate total value
            total_value = 0
            for tracking in self.db.db.opportunity_tracking.find({"stage": stage.value}):
                if tracking.get("estimated_value"):
                    total_value += tracking["estimated_value"]
            
            pipeline.append({
                "stage": stage.value,
                "count": count,
                "total_value": total_value
            })
        
        return {
            "pipeline": pipeline,
            "total_opportunities": self.db.db.opportunity_tracking.count_documents({}),
            "updated_at": datetime.now(timezone.utc)
        }