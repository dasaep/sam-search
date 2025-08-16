"""
HubSpot integration module for syncing opportunities as deals
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

log = logging.getLogger("hubspot")


class HubSpotClient:
    """Client for interacting with HubSpot API"""
    
    BASE_URL = "https://api.hubapi.com"
    
    def __init__(self, api_key: str = None, access_token: str = None):
        """
        Initialize HubSpot client with either API key or OAuth access token
        
        Args:
            api_key: HubSpot API key (deprecated but still supported)
            access_token: OAuth2 access token (recommended)
        """
        self.api_key = api_key
        self.access_token = access_token
        
        if not api_key and not access_token:
            raise ValueError("Either API key or access token must be provided")
        
        self.headers = self._get_headers()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get appropriate headers based on authentication method"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            # API key is passed as query parameter, not in headers
            pass
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request to HubSpot API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        # Add API key to params if using API key authentication
        if self.api_key and not self.access_token:
            if params is None:
                params = {}
            params["hapikey"] = self.api_key
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            
            if response.text:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            log.error(f"HubSpot API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                log.error(f"Response: {e.response.text}")
            raise
    
    def create_deal(self, deal_data: Dict[str, Any]) -> Dict:
        """
        Create a new deal in HubSpot
        
        Args:
            deal_data: Dictionary containing deal properties
        
        Returns:
            Created deal object from HubSpot
        """
        endpoint = "/crm/v3/objects/deals"
        
        # Format data for HubSpot API
        formatted_data = {
            "properties": deal_data
        }
        
        result = self._make_request("POST", endpoint, data=formatted_data)
        log.info(f"Created HubSpot deal: {result.get('id')}")
        return result
    
    def update_deal(self, deal_id: str, deal_data: Dict[str, Any]) -> Dict:
        """
        Update an existing deal in HubSpot
        
        Args:
            deal_id: HubSpot deal ID
            deal_data: Dictionary containing deal properties to update
        
        Returns:
            Updated deal object from HubSpot
        """
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        
        formatted_data = {
            "properties": deal_data
        }
        
        result = self._make_request("PATCH", endpoint, data=formatted_data)
        log.info(f"Updated HubSpot deal: {deal_id}")
        return result
    
    def get_deal(self, deal_id: str) -> Dict:
        """
        Get a deal by ID from HubSpot
        
        Args:
            deal_id: HubSpot deal ID
        
        Returns:
            Deal object from HubSpot
        """
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        return self._make_request("GET", endpoint)
    
    def get_deals(self, limit: int = 100, after: str = None, properties: List[str] = None) -> Dict:
        """
        Get multiple deals from HubSpot
        
        Args:
            limit: Number of deals to retrieve (max 100)
            after: Pagination cursor
            properties: List of properties to include
        
        Returns:
            Dictionary containing deals and pagination info
        """
        endpoint = "/crm/v3/objects/deals"
        
        params = {
            "limit": min(limit, 100)
        }
        
        if after:
            params["after"] = after
        
        if properties:
            params["properties"] = ",".join(properties)
        
        return self._make_request("GET", endpoint, params=params)
    
    def search_deals(self, filters: List[Dict], properties: List[str] = None, limit: int = 100) -> Dict:
        """
        Search for deals using filters
        
        Args:
            filters: List of filter conditions
            properties: List of properties to include
            limit: Number of results to return
        
        Returns:
            Search results containing matching deals
        """
        endpoint = "/crm/v3/objects/deals/search"
        
        data = {
            "filterGroups": [{"filters": filters}],
            "limit": min(limit, 100)
        }
        
        if properties:
            data["properties"] = properties
        
        return self._make_request("POST", endpoint, data=data)
    
    def delete_deal(self, deal_id: str) -> None:
        """
        Delete a deal from HubSpot
        
        Args:
            deal_id: HubSpot deal ID
        """
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        self._make_request("DELETE", endpoint)
        log.info(f"Deleted HubSpot deal: {deal_id}")
    
    def get_pipelines(self) -> List[Dict]:
        """
        Get all deal pipelines from HubSpot
        
        Returns:
            List of pipeline objects
        """
        endpoint = "/crm/v3/pipelines/deals"
        result = self._make_request("GET", endpoint)
        return result.get("results", [])
    
    def get_deal_stages(self, pipeline_id: str = None) -> List[Dict]:
        """
        Get deal stages for a specific pipeline or all pipelines
        
        Args:
            pipeline_id: Optional pipeline ID to filter stages
        
        Returns:
            List of deal stage objects
        """
        pipelines = self.get_pipelines()
        stages = []
        
        for pipeline in pipelines:
            if pipeline_id and pipeline["id"] != pipeline_id:
                continue
            
            for stage in pipeline.get("stages", []):
                stage["pipeline_id"] = pipeline["id"]
                stage["pipeline_name"] = pipeline["label"]
                stages.append(stage)
        
        return stages


class HubSpotSyncManager:
    """Manager for syncing opportunities with HubSpot deals"""
    
    def __init__(self, hubspot_client: HubSpotClient, db):
        """
        Initialize sync manager
        
        Args:
            hubspot_client: HubSpot API client
            db: Database instance
        """
        self.client = hubspot_client
        self.db = db
    
    def opportunity_to_deal(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an opportunity to HubSpot deal format
        
        Args:
            opportunity: Opportunity data from database
        
        Returns:
            Dictionary formatted for HubSpot deal creation
        """
        # Map opportunity fields to HubSpot deal properties
        deal_data = {
            "dealname": opportunity.get("title", "Untitled Opportunity"),
            "amount": opportunity.get("amount", 0),
            "closedate": self._format_date(opportunity.get("due_date")),
            "pipeline": "default",  # Can be configured
            "dealstage": "appointmentscheduled",  # Initial stage
            "description": opportunity.get("description", ""),
            
            # Custom properties (these need to be created in HubSpot first)
            "sam_opportunity_id": str(opportunity.get("_id", "")),
            "sam_notice_id": opportunity.get("notice_id", ""),
            "sam_agency": opportunity.get("agency", ""),
            "sam_naics": opportunity.get("naics", ""),
            "sam_set_aside": opportunity.get("set_aside", ""),
            "sam_url": opportunity.get("url", ""),
            "sam_posted_date": self._format_date(opportunity.get("posted_date")),
        }
        
        # Remove None values
        deal_data = {k: v for k, v in deal_data.items() if v is not None}
        
        return deal_data
    
    def _format_date(self, date_value) -> Optional[str]:
        """
        Format date for HubSpot (Unix timestamp in milliseconds)
        
        Args:
            date_value: Date string or datetime object
        
        Returns:
            Unix timestamp in milliseconds as string
        """
        if not date_value:
            return None
        
        try:
            if isinstance(date_value, str):
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            elif isinstance(date_value, datetime):
                dt = date_value
            else:
                return None
            
            # Convert to Unix timestamp in milliseconds
            timestamp = int(dt.timestamp() * 1000)
            return str(timestamp)
        except Exception as e:
            log.error(f"Error formatting date {date_value}: {e}")
            return None
    
    def sync_opportunity_to_hubspot(self, opportunity_id: str) -> Dict[str, Any]:
        """
        Sync a single opportunity to HubSpot as a deal
        
        Args:
            opportunity_id: Database ID of the opportunity
        
        Returns:
            Sync result with HubSpot deal ID and status
        """
        try:
            # Get opportunity from database
            opportunity = self.db.get_opportunity_by_id(opportunity_id)
            if not opportunity:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Check if already synced
            existing_sync = self.db.get_hubspot_sync_status(opportunity_id)
            
            deal_data = self.opportunity_to_deal(opportunity)
            
            if existing_sync and existing_sync.get("hubspot_deal_id"):
                # Update existing deal
                deal_id = existing_sync["hubspot_deal_id"]
                result = self.client.update_deal(deal_id, deal_data)
                sync_status = "updated"
            else:
                # Create new deal
                result = self.client.create_deal(deal_data)
                deal_id = result["id"]
                sync_status = "created"
            
            # Update sync status in database
            sync_record = {
                "opportunity_id": opportunity_id,
                "hubspot_deal_id": deal_id,
                "sync_status": sync_status,
                "last_sync": datetime.now(timezone.utc),
                "sync_error": None
            }
            self.db.update_hubspot_sync_status(sync_record)
            
            return {
                "success": True,
                "hubspot_deal_id": deal_id,
                "status": sync_status
            }
            
        except Exception as e:
            log.error(f"Failed to sync opportunity {opportunity_id}: {e}")
            
            # Update sync status with error
            sync_record = {
                "opportunity_id": opportunity_id,
                "sync_status": "error",
                "last_sync": datetime.now(timezone.utc),
                "sync_error": str(e)
            }
            self.db.update_hubspot_sync_status(sync_record)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def sync_multiple_opportunities(self, opportunity_ids: List[str]) -> Dict[str, Any]:
        """
        Sync multiple opportunities to HubSpot
        
        Args:
            opportunity_ids: List of opportunity IDs to sync
        
        Returns:
            Summary of sync results
        """
        results = {
            "total": len(opportunity_ids),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for opp_id in opportunity_ids:
            result = self.sync_opportunity_to_hubspot(opp_id)
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "opportunity_id": opp_id,
                **result
            })
        
        return results
    
    def sync_from_hubspot(self, since_date: datetime = None) -> Dict[str, Any]:
        """
        Sync deal updates from HubSpot back to local database
        
        Args:
            since_date: Only sync deals modified after this date
        
        Returns:
            Summary of sync results
        """
        try:
            # Get all synced opportunities
            synced_opps = self.db.get_synced_opportunities()
            
            if not synced_opps:
                return {
                    "success": True,
                    "message": "No opportunities to sync from HubSpot",
                    "updated": 0
                }
            
            updated_count = 0
            
            for sync_record in synced_opps:
                if not sync_record.get("hubspot_deal_id"):
                    continue
                
                try:
                    # Get deal from HubSpot
                    deal = self.client.get_deal(sync_record["hubspot_deal_id"])
                    
                    # Update local database with HubSpot data
                    update_data = {
                        "hubspot_stage": deal["properties"].get("dealstage"),
                        "hubspot_amount": deal["properties"].get("amount"),
                        "hubspot_close_date": deal["properties"].get("closedate"),
                        "hubspot_last_modified": deal["properties"].get("hs_lastmodifieddate"),
                        "hubspot_is_deleted": deal["properties"].get("hs_is_deleted", False)
                    }
                    
                    # Update sync status
                    sync_record.update({
                        "last_sync_from_hubspot": datetime.now(timezone.utc),
                        "hubspot_data": update_data
                    })
                    
                    self.db.update_hubspot_sync_status(sync_record)
                    updated_count += 1
                    
                except Exception as e:
                    log.error(f"Failed to sync deal {sync_record['hubspot_deal_id']}: {e}")
            
            return {
                "success": True,
                "updated": updated_count,
                "total_checked": len(synced_opps)
            }
            
        except Exception as e:
            log.error(f"Failed to sync from HubSpot: {e}")
            return {
                "success": False,
                "error": str(e)
            }