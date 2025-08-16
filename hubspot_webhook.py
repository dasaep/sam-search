"""
HubSpot webhook handler for receiving real-time updates
"""

import logging
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

log = logging.getLogger("hubspot_webhook")


class HubSpotWebhookHandler:
    """Handle incoming webhooks from HubSpot"""
    
    def __init__(self, db, client_secret: str = None):
        """
        Initialize webhook handler
        
        Args:
            db: Database instance
            client_secret: HubSpot client secret for webhook validation
        """
        self.db = db
        self.client_secret = client_secret
    
    def validate_webhook(self, request_body: str, signature: str) -> bool:
        """
        Validate webhook signature from HubSpot
        
        Args:
            request_body: Raw request body
            signature: X-HubSpot-Signature header value
        
        Returns:
            True if signature is valid
        """
        if not self.client_secret:
            log.warning("No client secret configured, skipping webhook validation")
            return True
        
        # HubSpot uses SHA256 HMAC
        expected_signature = hmac.new(
            self.client_secret.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook payload from HubSpot
        
        Args:
            payload: Webhook payload from HubSpot
        
        Returns:
            Processing result
        """
        try:
            # Extract event type and data
            events = payload.get('events', [payload])
            
            results = {
                'processed': 0,
                'errors': 0,
                'details': []
            }
            
            for event in events:
                try:
                    result = self._process_event(event)
                    results['processed'] += 1
                    results['details'].append(result)
                except Exception as e:
                    log.error(f"Failed to process event: {e}")
                    results['errors'] += 1
                    results['details'].append({
                        'error': str(e),
                        'event': event
                    })
            
            return results
            
        except Exception as e:
            log.error(f"Failed to process webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single webhook event
        
        Args:
            event: Single event from webhook payload
        
        Returns:
            Processing result for this event
        """
        event_type = event.get('eventType', '')
        object_type = event.get('objectType', '')
        
        # Handle deal events
        if object_type == 'DEAL':
            return self._process_deal_event(event)
        
        # Handle contact events (if needed for deal associations)
        elif object_type == 'CONTACT':
            return self._process_contact_event(event)
        
        # Handle company events (if needed for deal associations)
        elif object_type == 'COMPANY':
            return self._process_company_event(event)
        
        else:
            log.info(f"Ignoring event type: {object_type}.{event_type}")
            return {
                'ignored': True,
                'reason': f'Unsupported object type: {object_type}'
            }
    
    def _process_deal_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process deal-related webhook events
        
        Args:
            event: Deal event from webhook
        
        Returns:
            Processing result
        """
        event_type = event.get('eventType', '')
        deal_id = str(event.get('objectId'))
        
        if not deal_id:
            raise ValueError("No deal ID in event")
        
        # Get the opportunity associated with this deal
        sync_record = self.db.hubspot_sync.find_one({
            'hubspot_deal_id': deal_id
        })
        
        if not sync_record:
            log.warning(f"No local opportunity found for HubSpot deal {deal_id}")
            return {
                'warning': 'Deal not found in local database',
                'deal_id': deal_id
            }
        
        opportunity_id = sync_record['opportunity_id']
        
        # Process based on event type
        if event_type in ['deal.creation', 'deal.propertyChange']:
            # Update local sync status
            properties = event.get('properties', {})
            
            update_data = {
                'opportunity_id': opportunity_id,
                'hubspot_deal_id': deal_id,
                'last_webhook_event': event_type,
                'last_webhook_time': datetime.now(timezone.utc),
                'webhook_data': {
                    'stage': properties.get('dealstage'),
                    'amount': properties.get('amount'),
                    'close_date': properties.get('closedate'),
                    'pipeline': properties.get('pipeline'),
                    'probability': properties.get('hs_deal_stage_probability'),
                    'is_closed': properties.get('hs_is_closed'),
                    'is_closed_won': properties.get('hs_is_closed_won')
                }
            }
            
            self.db.update_hubspot_sync_status(update_data)
            
            # Update opportunity status if deal is closed
            if properties.get('hs_is_closed_won') == 'true':
                self._mark_opportunity_won(opportunity_id)
            elif properties.get('hs_is_closed') == 'true':
                self._mark_opportunity_lost(opportunity_id)
            
            return {
                'success': True,
                'action': 'updated',
                'opportunity_id': opportunity_id,
                'deal_id': deal_id,
                'event_type': event_type
            }
        
        elif event_type == 'deal.deletion':
            # Mark sync record as deleted
            update_data = {
                'opportunity_id': opportunity_id,
                'hubspot_deal_id': deal_id,
                'sync_status': 'deleted',
                'last_webhook_event': event_type,
                'last_webhook_time': datetime.now(timezone.utc),
                'deleted_at': datetime.now(timezone.utc)
            }
            
            self.db.update_hubspot_sync_status(update_data)
            
            return {
                'success': True,
                'action': 'deleted',
                'opportunity_id': opportunity_id,
                'deal_id': deal_id
            }
        
        else:
            return {
                'ignored': True,
                'reason': f'Unhandled deal event type: {event_type}'
            }
    
    def _process_contact_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process contact-related webhook events
        
        Args:
            event: Contact event from webhook
        
        Returns:
            Processing result
        """
        # Implement if you need to track contact associations with deals
        return {
            'ignored': True,
            'reason': 'Contact events not implemented'
        }
    
    def _process_company_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process company-related webhook events
        
        Args:
            event: Company event from webhook
        
        Returns:
            Processing result
        """
        # Implement if you need to track company associations with deals
        return {
            'ignored': True,
            'reason': 'Company events not implemented'
        }
    
    def _mark_opportunity_won(self, opportunity_id: str):
        """Mark an opportunity as won in the local database"""
        try:
            from bson import ObjectId
            self.db.opportunities.update_one(
                {'_id': ObjectId(opportunity_id)},
                {
                    '$set': {
                        'status': 'won',
                        'won_date': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            log.info(f"Marked opportunity {opportunity_id} as won")
        except Exception as e:
            log.error(f"Failed to mark opportunity as won: {e}")
    
    def _mark_opportunity_lost(self, opportunity_id: str):
        """Mark an opportunity as lost in the local database"""
        try:
            from bson import ObjectId
            self.db.opportunities.update_one(
                {'_id': ObjectId(opportunity_id)},
                {
                    '$set': {
                        'status': 'lost',
                        'lost_date': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            log.info(f"Marked opportunity {opportunity_id} as lost")
        except Exception as e:
            log.error(f"Failed to mark opportunity as lost: {e}")


def register_webhook_endpoint(app, db, config_manager):
    """
    Register webhook endpoint with Flask app
    
    Args:
        app: Flask application instance
        db: Database instance
        config_manager: HubSpot configuration manager
    """
    from flask import request, jsonify
    
    @app.route('/api/hubspot/webhook', methods=['POST'])
    def handle_hubspot_webhook():
        """Handle incoming HubSpot webhooks"""
        try:
            # Get configuration
            config = config_manager.get_config()
            if not config or not config.get('webhook_enabled'):
                return jsonify({
                    'success': False,
                    'error': 'Webhooks not enabled'
                }), 403
            
            # Initialize handler
            handler = HubSpotWebhookHandler(
                db,
                client_secret=config.get('client_secret')
            )
            
            # Validate webhook signature if configured
            signature = request.headers.get('X-HubSpot-Signature', '')
            if config.get('client_secret'):
                if not handler.validate_webhook(request.data.decode(), signature):
                    log.warning("Invalid webhook signature")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid signature'
                    }), 401
            
            # Process webhook
            payload = request.json
            result = handler.process_webhook(payload)
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            log.error(f"Webhook handling error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500