"""
Flask API backend for SAM.gov opportunity analysis system
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import os
import logging
from database import OpportunityDB
from capability_matcher import CapabilityMatcher
from config_db import MONGODB_CONFIG
from hubspot_integration import HubSpotClient, HubSpotSyncManager
from hubspot_config import HubSpotConfigManager
from hubspot_webhook import register_webhook_endpoint

app = Flask(__name__)
CORS(app)

log = logging.getLogger("app")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log.info("Starting SAM.gov Opportunity Analysis API")
log.info(f"Initializing database connection...")

try:
    # Connect to MongoDB Atlas
    db = OpportunityDB(
        connection_string=MONGODB_CONFIG["connection_string"],
        db_name=MONGODB_CONFIG["database_name"]
    )
    matcher = CapabilityMatcher(db)
    config_manager = HubSpotConfigManager(db)
    
    # Register webhook endpoint
    register_webhook_endpoint(app, db, config_manager)
    
    log.info("Database connection established successfully")
except Exception as e:
    log.error(f"Failed to initialize database: {e}")
    log.error("Please check your MongoDB Atlas connection and try again")
    exit(1)


@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """Get opportunities with optional filters"""
    try:
        filters = {}
        
        if request.args.get('naics'):
            filters['naics'] = request.args.get('naics')
        
        if request.args.get('agency'):
            filters['agency'] = {'$regex': request.args.get('agency'), '$options': 'i'}
        
        if request.args.get('set_aside'):
            filters['set_aside'] = request.args.get('set_aside')
        
        if request.args.get('days'):
            days = int(request.args.get('days'))
            filters['posted_date_parsed'] = {
                '$gte': datetime.now(timezone.utc) - timedelta(days=days)
            }
        
        limit = int(request.args.get('limit', 100))
        skip = int(request.args.get('skip', 0))
        
        opportunities = db.get_opportunities(filters, limit, skip)
        
        return jsonify({
            'success': True,
            'data': opportunities,
            'count': len(opportunities)
        })
    
    except Exception as e:
        log.error(f"Error getting opportunities: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunities/<opp_id>', methods=['GET'])
def get_opportunity(opp_id):
    """Get a single opportunity with its matches"""
    try:
        opportunity = db.get_opportunity_by_id(opp_id)
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': 'Opportunity not found'
            }), 404
        
        matches = db.get_matches_for_opportunity(opp_id)
        
        return jsonify({
            'success': True,
            'data': {
                'opportunity': opportunity,
                'matches': matches
            }
        })
    
    except Exception as e:
        log.error(f"Error getting opportunity: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunities/<opp_id>/analyze', methods=['POST'])
def analyze_opportunity(opp_id):
    """Analyze an opportunity against all active capabilities"""
    try:
        opportunity = db.get_opportunity_by_id(opp_id)
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': 'Opportunity not found'
            }), 404
        
        matches = matcher.analyze_opportunity(opportunity)
        
        return jsonify({
            'success': True,
            'data': matches
        })
    
    except Exception as e:
        log.error(f"Error analyzing opportunity: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/capabilities', methods=['GET'])
def get_capabilities():
    """Get all capabilities"""
    try:
        active_only = request.args.get('active', 'true').lower() == 'true'
        capabilities = db.get_capabilities(active_only)
        
        return jsonify({
            'success': True,
            'data': capabilities
        })
    
    except Exception as e:
        log.error(f"Error getting capabilities: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/capabilities', methods=['POST'])
def create_capability():
    """Create a new capability"""
    try:
        data = request.json
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Capability name is required'
            }), 400
        
        capability = {
            'name': data['name'],
            'description': data.get('description', ''),
            'keywords': data.get('keywords', []),
            'naics_codes': data.get('naics_codes', []),
            'preferred_agencies': data.get('preferred_agencies', []),
            'min_value': data.get('min_value'),
            'max_value': data.get('max_value'),
            'active': data.get('active', True)
        }
        
        cap_id = db.create_capability(capability)
        
        return jsonify({
            'success': True,
            'data': {'id': cap_id}
        })
    
    except Exception as e:
        log.error(f"Error creating capability: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/capabilities/<cap_id>', methods=['PUT'])
def update_capability(cap_id):
    """Update a capability"""
    try:
        data = request.json
        
        allowed_updates = ['name', 'description', 'keywords', 'naics_codes', 
                          'preferred_agencies', 'min_value', 'max_value', 'active']
        
        updates = {k: v for k, v in data.items() if k in allowed_updates}
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No valid updates provided'
            }), 400
        
        success = db.update_capability(cap_id, updates)
        
        return jsonify({
            'success': success
        })
    
    except Exception as e:
        log.error(f"Error updating capability: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/matches/high', methods=['GET'])
def get_high_matches():
    """Get opportunities with high capability matches"""
    try:
        threshold = float(request.args.get('threshold', 70))
        limit = int(request.args.get('limit', 50))
        
        matches = db.get_high_matches(threshold, limit)
        
        return jsonify({
            'success': True,
            'data': matches
        })
    
    except Exception as e:
        log.error(f"Error getting high matches: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        stats = db.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        log.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# HubSpot Integration Endpoints

@app.route('/api/hubspot/config', methods=['GET'])
def get_hubspot_config():
    """Get HubSpot configuration"""
    try:
        config = config_manager.get_config()
        
        if config:
            # Remove sensitive data from response
            if 'api_key' in config:
                config['api_key'] = '***' if config['api_key'] else ''
            if 'access_token' in config:
                config['access_token'] = '***' if config['access_token'] else ''
        
        return jsonify({
            'success': True,
            'data': config or {}
        })
    
    except Exception as e:
        log.error(f"Error getting HubSpot config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hubspot/config', methods=['POST'])
def save_hubspot_config():
    """Save HubSpot configuration"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('api_key') and not data.get('access_token'):
            return jsonify({
                'success': False,
                'error': 'Either API key or access token is required'
            }), 400
        
        # Save configuration
        success = config_manager.save_config(data)
        
        if success:
            # Test connection
            test_result = config_manager.test_connection()
            
            return jsonify({
                'success': True,
                'message': 'Configuration saved successfully',
                'connection_test': test_result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save configuration'
            }), 500
    
    except Exception as e:
        log.error(f"Error saving HubSpot config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hubspot/test', methods=['POST'])
def test_hubspot_connection():
    """Test HubSpot connection"""
    try:
        result = config_manager.test_connection()
        
        return jsonify({
            'success': result['success'],
            'data': result
        })
    
    except Exception as e:
        log.error(f"Error testing HubSpot connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hubspot/sync', methods=['POST'])
def sync_to_hubspot():
    """Sync opportunities to HubSpot"""
    try:
        data = request.json
        opportunity_ids = data.get('opportunity_ids', [])
        
        if not opportunity_ids:
            return jsonify({
                'success': False,
                'error': 'No opportunities selected for sync'
            }), 400
        
        # Get HubSpot configuration
        config = config_manager.get_config()
        if not config:
            return jsonify({
                'success': False,
                'error': 'HubSpot not configured'
            }), 400
        
        # Initialize HubSpot client and sync manager
        client = HubSpotClient(
            api_key=config.get('api_key'),
            access_token=config.get('access_token')
        )
        sync_manager = HubSpotSyncManager(client, db)
        
        # Sync opportunities
        results = sync_manager.sync_multiple_opportunities(opportunity_ids)
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        log.error(f"Error syncing to HubSpot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hubspot/sync-from', methods=['POST'])
def sync_from_hubspot():
    """Sync deal updates from HubSpot"""
    try:
        # Get HubSpot configuration
        config = config_manager.get_config()
        if not config:
            return jsonify({
                'success': False,
                'error': 'HubSpot not configured'
            }), 400
        
        # Initialize HubSpot client and sync manager
        client = HubSpotClient(
            api_key=config.get('api_key'),
            access_token=config.get('access_token')
        )
        sync_manager = HubSpotSyncManager(client, db)
        
        # Sync from HubSpot
        results = sync_manager.sync_from_hubspot()
        
        return jsonify({
            'success': results['success'],
            'data': results
        })
    
    except Exception as e:
        log.error(f"Error syncing from HubSpot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hubspot/statistics', methods=['GET'])
def get_hubspot_statistics():
    """Get HubSpot sync statistics"""
    try:
        stats = db.get_hubspot_sync_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        log.error(f"Error getting HubSpot statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunities/with-sync', methods=['GET'])
def get_opportunities_with_sync():
    """Get opportunities with HubSpot sync status"""
    try:
        filters = {}
        
        if request.args.get('naics'):
            filters['naics'] = request.args.get('naics')
        
        if request.args.get('agency'):
            filters['agency'] = {'$regex': request.args.get('agency'), '$options': 'i'}
        
        if request.args.get('set_aside'):
            filters['set_aside'] = request.args.get('set_aside')
        
        if request.args.get('days'):
            days = int(request.args.get('days'))
            filters['posted_date_parsed'] = {
                '$gte': datetime.now(timezone.utc) - timedelta(days=days)
            }
        
        limit = int(request.args.get('limit', 100))
        skip = int(request.args.get('skip', 0))
        
        opportunities = db.get_opportunities_with_sync_status(filters, limit, skip)
        
        return jsonify({
            'success': True,
            'data': opportunities,
            'count': len(opportunities)
        })
    
    except Exception as e:
        log.error(f"Error getting opportunities with sync: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'message': 'SAM.gov Opportunity Analysis API',
        'endpoints': {
            'opportunities': '/api/opportunities',
            'capabilities': '/api/capabilities',
            'statistics': '/api/statistics',
            'high_matches': '/api/matches/high',
            'hubspot_config': '/api/hubspot/config',
            'hubspot_sync': '/api/hubspot/sync',
            'hubspot_sync_from': '/api/hubspot/sync-from',
            'hubspot_statistics': '/api/hubspot/statistics'
        },
        'frontend': 'Run separately on port 3000 with: cd frontend && npm start'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')