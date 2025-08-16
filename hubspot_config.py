"""
HubSpot configuration management module
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timezone
from cryptography.fernet import Fernet
import base64

log = logging.getLogger("hubspot_config")


class HubSpotConfigManager:
    """Manage HubSpot configuration and credentials"""
    
    def __init__(self, db):
        """
        Initialize configuration manager
        
        Args:
            db: Database instance for storing configuration
        """
        self.db = db
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for securing API credentials"""
        key_file = ".hubspot_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value"""
        if not value:
            return ""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value"""
        if not encrypted_value:
            return ""
        try:
            decoded = base64.b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            log.error(f"Failed to decrypt value: {e}")
            return ""
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save HubSpot configuration to database
        
        Args:
            config: Configuration dictionary containing:
                - api_key or access_token (required)
                - pipeline_id (optional)
                - default_stage_id (optional)
                - sync_enabled (optional)
                - webhook_url (optional)
                - custom_field_mappings (optional)
        
        Returns:
            True if saved successfully
        """
        try:
            # Encrypt sensitive data
            if "api_key" in config:
                config["api_key_encrypted"] = self.encrypt_value(config.pop("api_key"))
            
            if "access_token" in config:
                config["access_token_encrypted"] = self.encrypt_value(config.pop("access_token"))
            
            # Add metadata
            config["updated_at"] = datetime.now(timezone.utc)
            config["config_version"] = "1.0"
            
            # Save to database
            self.db.save_hubspot_config(config)
            
            log.info("HubSpot configuration saved successfully")
            return True
            
        except Exception as e:
            log.error(f"Failed to save HubSpot configuration: {e}")
            return False
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get HubSpot configuration from database
        
        Returns:
            Configuration dictionary with decrypted values
        """
        try:
            config = self.db.get_hubspot_config()
            
            if not config:
                return None
            
            # Decrypt sensitive data
            if "api_key_encrypted" in config:
                config["api_key"] = self.decrypt_value(config.pop("api_key_encrypted"))
            
            if "access_token_encrypted" in config:
                config["access_token"] = self.decrypt_value(config.pop("access_token_encrypted"))
            
            return config
            
        except Exception as e:
            log.error(f"Failed to get HubSpot configuration: {e}")
            return None
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update specific configuration values
        
        Args:
            updates: Dictionary of configuration updates
        
        Returns:
            True if updated successfully
        """
        try:
            current_config = self.get_config() or {}
            current_config.update(updates)
            return self.save_config(current_config)
            
        except Exception as e:
            log.error(f"Failed to update HubSpot configuration: {e}")
            return False
    
    def delete_config(self) -> bool:
        """
        Delete HubSpot configuration from database
        
        Returns:
            True if deleted successfully
        """
        try:
            self.db.delete_hubspot_config()
            log.info("HubSpot configuration deleted")
            return True
            
        except Exception as e:
            log.error(f"Failed to delete HubSpot configuration: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate HubSpot configuration
        
        Args:
            config: Configuration to validate (uses stored config if not provided)
        
        Returns:
            Validation result with status and any errors
        """
        if config is None:
            config = self.get_config()
        
        if not config:
            return {
                "valid": False,
                "errors": ["No configuration found"]
            }
        
        errors = []
        
        # Check for required authentication
        if not config.get("api_key") and not config.get("access_token"):
            errors.append("Either API key or access token is required")
        
        # Validate webhook URL if provided
        if config.get("webhook_url"):
            if not config["webhook_url"].startswith(("http://", "https://")):
                errors.append("Invalid webhook URL format")
        
        # Validate custom field mappings if provided
        if config.get("custom_field_mappings"):
            if not isinstance(config["custom_field_mappings"], dict):
                errors.append("Custom field mappings must be a dictionary")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_field_mappings(self) -> Dict[str, str]:
        """
        Get field mappings between opportunity fields and HubSpot deal properties
        
        Returns:
            Dictionary mapping opportunity fields to HubSpot properties
        """
        config = self.get_config()
        
        # Default mappings
        default_mappings = {
            "title": "dealname",
            "amount": "amount",
            "due_date": "closedate",
            "description": "description",
            "agency": "sam_agency",
            "naics": "sam_naics",
            "set_aside": "sam_set_aside",
            "notice_id": "sam_notice_id",
            "url": "sam_url",
            "posted_date": "sam_posted_date"
        }
        
        if config and config.get("custom_field_mappings"):
            # Override with custom mappings
            default_mappings.update(config["custom_field_mappings"])
        
        return default_mappings
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test HubSpot connection with current configuration
        
        Returns:
            Test result with status and details
        """
        try:
            from hubspot_integration import HubSpotClient
            
            config = self.get_config()
            if not config:
                return {
                    "success": False,
                    "error": "No configuration found"
                }
            
            # Create client and test connection
            client = HubSpotClient(
                api_key=config.get("api_key"),
                access_token=config.get("access_token")
            )
            
            # Try to get pipelines as a test
            pipelines = client.get_pipelines()
            
            return {
                "success": True,
                "message": "Connection successful",
                "pipelines_found": len(pipelines)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Default configuration template
DEFAULT_HUBSPOT_CONFIG = {
    "api_key": "",
    "access_token": "",
    "pipeline_id": "default",
    "default_stage_id": "appointmentscheduled",
    "sync_enabled": True,
    "sync_interval_minutes": 30,
    "webhook_enabled": False,
    "webhook_url": "",
    "custom_field_mappings": {},
    "auto_sync_new_opportunities": False,
    "sync_direction": "bidirectional",  # one-way-to-hubspot, one-way-from-hubspot, bidirectional
    "create_custom_properties": True,
    "log_level": "INFO"
}