#!/usr/bin/env python3
"""
Test HubSpot connection and diagnose authentication issues
"""

import sys
import requests
import json
from hubspot_integration import HubSpotClient
from hubspot_config import HubSpotConfigManager
from database import OpportunityDB
from config_db import MONGODB_CONFIG

def test_direct_api_call(token):
    """Test direct API call to HubSpot"""
    print("\n1. Testing direct API call...")
    
    # Test with pipelines endpoint (simple GET request)
    url = "https://api.hubapi.com/crm/v3/pipelines/deals"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Direct API call successful!")
            data = response.json()
            print(f"   Found {len(data.get('results', []))} pipelines")
            return True
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 401:
                print("\n   📝 401 Unauthorized - Token is invalid or expired")
                print("   Please ensure:")
                print("   1. Your token starts with 'pat-'")
                print("   2. The token was copied correctly (no extra spaces)")
                print("   3. The Private App is active in HubSpot")
            elif response.status_code == 403:
                print("\n   📝 403 Forbidden - Missing required scopes")
                print("   Please ensure your Private App has these scopes:")
                print("   - crm.objects.deals.read")
                print("   - crm.objects.deals.write")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_token_format(token):
    """Check if token has correct format"""
    print("\n2. Checking token format...")
    
    if not token:
        print("   ❌ Token is empty")
        return False
    
    if token.startswith("pat-"):
        print("   ✅ Token format looks correct (starts with 'pat-')")
        return True
    elif len(token) == 40 and not token.startswith("pat-"):
        print("   ⚠️  This looks like a legacy API key (40 characters)")
        print("   HubSpot API keys are deprecated. Please use a Private App Access Token.")
        return False
    else:
        print(f"   ❌ Token format doesn't look right")
        print(f"   Token starts with: {token[:10]}...")
        print("   Expected format: pat-na1-xxxxx...")
        return False

def test_client_class(token):
    """Test using the HubSpotClient class"""
    print("\n3. Testing HubSpotClient class...")
    
    try:
        client = HubSpotClient(access_token=token)
        pipelines = client.get_pipelines()
        print(f"   ✅ Client class works! Found {len(pipelines)} pipelines")
        
        if pipelines:
            print("   Available pipelines:")
            for pipeline in pipelines:
                print(f"   - {pipeline.get('label')} (ID: {pipeline.get('id')})")
        
        return True
    except Exception as e:
        print(f"   ❌ Client class failed: {e}")
        return False

def test_with_config_manager():
    """Test using saved configuration"""
    print("\n4. Testing with saved configuration...")
    
    try:
        # Connect to MongoDB
        db = OpportunityDB(
            connection_string=MONGODB_CONFIG["connection_string"],
            db_name=MONGODB_CONFIG["database_name"]
        )
        
        config_manager = HubSpotConfigManager(db)
        config = config_manager.get_config()
        
        if not config:
            print("   ℹ️  No saved configuration found")
            return False
        
        if config.get('access_token'):
            print("   ✅ Found saved access token")
            result = config_manager.test_connection()
            if result['success']:
                print(f"   ✅ Connection test passed! Found {result.get('pipelines_found', 0)} pipelines")
                return True
            else:
                print(f"   ❌ Connection test failed: {result.get('error')}")
                return False
        elif config.get('api_key'):
            print("   ⚠️  Found legacy API key in configuration")
            print("   Please update to use a Private App Access Token")
            return False
        else:
            print("   ❌ No authentication credentials in saved configuration")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("HubSpot Connection Test")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Token provided as command line argument
        token = sys.argv[1]
        print(f"\nTesting with provided token...")
        
        # Run tests
        format_ok = test_token_format(token)
        if format_ok:
            api_ok = test_direct_api_call(token)
            if api_ok:
                client_ok = test_client_class(token)
    else:
        print("\nNo token provided. Testing saved configuration...")
        test_with_config_manager()
        
        print("\n" + "=" * 60)
        print("To test with a specific token, run:")
        print("python test_hubspot_connection.py YOUR_ACCESS_TOKEN")
    
    print("\n" + "=" * 60)
    print("Troubleshooting Guide:")
    print("=" * 60)
    print("""
1. Getting a Private App Access Token:
   - Go to HubSpot Settings → Integrations → Private Apps
   - Create a new app or use existing
   - Grant scopes: crm.objects.deals.read, crm.objects.deals.write
   - Copy the Access Token (starts with 'pat-')

2. Common Issues:
   - Wrong token type: Make sure you're using a Private App token, not API key
   - Missing scopes: Check that your app has deal read/write permissions
   - Token copied incorrectly: Ensure no extra spaces or characters
   - Region mismatch: Token region (na1, eu1) must match your HubSpot account

3. If you're using an API Key:
   - API Keys are deprecated as of November 2022
   - You must create a Private App and use its Access Token instead

4. Need more help?
   - Check HubSpot's Private Apps documentation
   - Verify your HubSpot account has API access
   - Ensure your subscription level includes API access
    """)

if __name__ == "__main__":
    main()