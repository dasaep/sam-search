"""
Flask API backend with local MongoDB option
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import os
import logging
import sys

app = Flask(__name__)
CORS(app)

log = logging.getLogger("app")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Try to import and initialize database
db = None
matcher = None

try:
    from database_local import OpportunityDB
    from capability_matcher import CapabilityMatcher
    
    log.info("Starting SAM.gov Opportunity Analysis API (Local MongoDB Mode)")
    
    # Try local MongoDB first
    log.info("Attempting to connect to local MongoDB...")
    db = OpportunityDB(connection_string="mongodb://localhost:27017/", db_name="sam_opportunities")
    matcher = CapabilityMatcher(db)
    log.info("Successfully connected to local MongoDB")
    
except Exception as e:
    log.warning(f"Could not connect to MongoDB: {e}")
    log.info("Running in demo mode without database")

@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'message': 'SAM.gov Opportunity Analysis API',
        'status': 'running',
        'database': 'connected' if db else 'not connected (demo mode)',
        'endpoints': {
            'opportunities': '/api/opportunities',
            'capabilities': '/api/capabilities', 
            'statistics': '/api/statistics',
            'high_matches': '/api/matches/high'
        },
        'frontend': 'Run separately on port 3000 with: cd frontend && npm start'
    })

@app.route('/api/statistics')
def get_statistics():
    """Get system statistics"""
    if not db:
        return jsonify({
            'success': True,
            'data': {
                'total_opportunities': 0,
                'total_capabilities': 0,
                'active_capabilities': 0,
                'total_matches': 0,
                'high_matches': 0,
                'recent_opportunities': 0,
                'mode': 'demo - no database connected'
            }
        })
    
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

@app.route('/api/opportunities')
def get_opportunities():
    """Get opportunities with optional filters"""
    if not db:
        # Return demo data
        return jsonify({
            'success': True,
            'data': [
                {
                    '_id': 'demo1',
                    'title': 'Demo Opportunity - Software Development Services',
                    'agency': 'DEMO AGENCY',
                    'posted_date': '2024-01-01',
                    'due_date': '2024-02-01',
                    'type': 'Sources Sought',
                    'naics': '541511',
                    'url': 'https://sam.gov/demo'
                }
            ],
            'count': 1,
            'mode': 'demo'
        })
    
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

@app.route('/api/capabilities')
def get_capabilities():
    """Get all capabilities"""
    if not db:
        return jsonify({
            'success': True,
            'data': [],
            'mode': 'demo'
        })
    
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

if __name__ == '__main__':
    log.info("Starting Flask server on port 5001...")
    log.info("Access the API at: http://localhost:5001")
    log.info("Access the frontend at: http://localhost:3000 (run separately)")
    app.run(debug=True, port=5001, host='127.0.0.1')