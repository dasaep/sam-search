"""
Test backend API endpoints
"""

import requests
import json
from config_db import MONGODB_CONFIG

def test_api():
    base_url = "http://localhost:5000"
    
    print("Testing Backend API")
    print("===================")
    print()
    
    # Test root endpoint
    try:
        print("1. Testing root endpoint (/)...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Root endpoint is working")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   ❌ Root endpoint returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error connecting to backend: {e}")
        print("   Make sure the backend is running with: python app.py")
        return
    
    print()
    
    # Test statistics endpoint
    try:
        print("2. Testing statistics endpoint (/api/statistics)...")
        response = requests.get(f"{base_url}/api/statistics", timeout=10)
        if response.status_code == 200:
            print("   ✅ Statistics endpoint is working")
            data = response.json()
            if data.get('success'):
                stats = data.get('data', {})
                print(f"   - Total opportunities: {stats.get('total_opportunities', 0)}")
                print(f"   - Total capabilities: {stats.get('total_capabilities', 0)}")
                print(f"   - Active capabilities: {stats.get('active_capabilities', 0)}")
                print(f"   - Total matches: {stats.get('total_matches', 0)}")
        else:
            print(f"   ❌ Statistics endpoint returned status: {response.status_code}")
    except requests.exceptions.Timeout:
        print("   ⚠️  Request timed out - MongoDB connection may be slow")
        print("   This could be due to network latency with MongoDB Atlas")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test opportunities endpoint
    try:
        print("3. Testing opportunities endpoint (/api/opportunities)...")
        response = requests.get(f"{base_url}/api/opportunities?limit=1", timeout=10)
        if response.status_code == 200:
            print("   ✅ Opportunities endpoint is working")
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                print(f"   - Found {count} opportunities")
        else:
            print(f"   ❌ Opportunities endpoint returned status: {response.status_code}")
    except requests.exceptions.Timeout:
        print("   ⚠️  Request timed out - MongoDB connection may be slow")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test capabilities endpoint
    try:
        print("4. Testing capabilities endpoint (/api/capabilities)...")
        response = requests.get(f"{base_url}/api/capabilities", timeout=10)
        if response.status_code == 200:
            print("   ✅ Capabilities endpoint is working")
            data = response.json()
            if data.get('success'):
                caps = data.get('data', [])
                print(f"   - Found {len(caps)} capabilities")
        else:
            print(f"   ❌ Capabilities endpoint returned status: {response.status_code}")
    except requests.exceptions.Timeout:
        print("   ⚠️  Request timed out - MongoDB connection may be slow")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("Test complete!")
    print()
    print("MongoDB Atlas Configuration:")
    print(f"- Database: {MONGODB_CONFIG['database_name']}")
    print("- Connection: mongodb+srv://Cluster08122:****@cluster08122.jkmqf6j.mongodb.net")

if __name__ == "__main__":
    test_api()