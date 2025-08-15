"""
Simple Flask app for testing without MongoDB
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/')
def index():
    """Test endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Flask server is working!',
        'note': 'This is a test server without MongoDB connection'
    })

@app.route('/api/test')
def test():
    """Test API endpoint"""
    return jsonify({
        'success': True,
        'data': 'API is responding correctly'
    })

if __name__ == '__main__':
    logging.info("Starting simple test server on port 5001...")
    app.run(debug=True, port=5001, host='127.0.0.1')