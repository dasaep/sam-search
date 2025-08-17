#!/usr/bin/env python3
"""
Debug HubSpot authentication issue
"""

import sys
import requests
import json
from database import OpportunityDB
from config_db import MONGODB_CONFIG
from hubspot_config import HubSpotConfigManager

def check_saved_token():
    """Check what token is saved in the database"""
    print("Checking saved configuration...")
    
    try:
        # Connect to MongoDB
        db = OpportunityDB(
            connection_string=MONGODB_CONFIG["connection_string"],
            db_name=MONGODB_CONFIG["database_name"]
        )
        
        config_manager = HubSpotConfigManager(db)
        config = config_manager.get_config()
        
        if not config:
            print("❌ No configuration found in database")
            return None
            
        print("\n📋 Saved Configuration:")
        print(f"  Has API Key: {'Yes' if config.get('api_key') else 'No'}")
        print(f"  Has Access Token: {'Yes' if config.get('access_token') else 'No'}")
        
        if config.get('access_token'):
            token = config.get('access_token')
            print(f"\n🔍 Token Analysis:")
            print(f"  Length: {len(token)} characters")
            print(f"  Starts with: {token[:10]}..." if len(token) > 10 else f"  Token: {token}")
            
            # Check token format
            if token.startswith('pat-'):
                print(f"  ✅ Format: Looks like a Private App Token")
            elif token.startswith('CK') or token.startswith('CS'):
                print(f"  ❌ Format: This looks like a Client Key/Secret (wrong type)")
                print(f"     You need a Private App Access Token, not OAuth2 app credentials")
            elif len(token) == 40:
                print(f"  ❌ Format: This looks like a legacy API key (deprecated)")
            else:
                print(f"  ⚠️  Format: Unrecognized token format")
            
            return token
        elif config.get('api_key'):
            print(f"\n⚠️  Only API Key found (deprecated)")
            print(f"  API Key starts with: {config.get('api_key')[:10]}...")
            return None
        else:
            print("❌ No authentication credentials found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return None

def test_token_directly(token):
    """Test the token with a direct API call"""
    print(f"\n🧪 Testing token directly with HubSpot API...")
    
    # Test 1: Simple GET request
    print("\nTest 1: GET /crm/v3/pipelines/deals")
    url = "https://api.hubapi.com/crm/v3/pipelines/deals"
    
    # Try with Bearer token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"  Headers: Authorization: Bearer {token[:15]}...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ Success! API call worked")
            return True
        else:
            print(f"  ❌ Failed with status {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            
            # Try to parse error
            try:
                error_data = response.json()
                if error_data.get('category') == 'INVALID_AUTHENTICATION':
                    print("\n  📝 Authentication Error Details:")
                    print(f"     {error_data.get('message', 'No message')}")
                    
                    if 'OAuth 2.0' in error_data.get('message', ''):
                        print("\n  ⚠️  The API is expecting OAuth 2.0 authentication")
                        print("     Make sure you're using a Private App Access Token")
                        print("     NOT an OAuth2 app's Client ID or Client Secret")
            except:
                pass
                
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_as_api_key(token):
    """Test if the token works as an API key (deprecated method)"""
    print(f"\n🧪 Testing as API key (deprecated)...")
    
    url = "https://api.hubapi.com/crm/v3/pipelines/deals"
    params = {"hapikey": token}
    
    print(f"  URL: {url}?hapikey={token[:10]}...")
    
    try:
        response = requests.get(url, params=params)
        print(f"  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ Works as API key (but this is deprecated)")
            return True
        else:
            print(f"  ❌ Doesn't work as API key either")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 HubSpot Authentication Debugger")
    print("=" * 60)
    
    # Check saved token
    token = check_saved_token()
    
    if token:
        # Test the token
        success = test_token_directly(token)
        
        if not success and not token.startswith('pat-'):
            # Try as API key if it doesn't look like a PAT
            test_as_api_key(token)
    
    print("\n" + "=" * 60)
    print("📚 Solution Guide")
    print("=" * 60)
    
    if token and not token.startswith('pat-'):
        print("""
⚠️  Your token doesn't appear to be a Private App Access Token.

You seem to be using either:
1. An OAuth2 app's Client ID/Secret (wrong type)
2. A legacy API key (deprecated)

To fix this:
1. Go to HubSpot Settings → Integrations → Private Apps
2. Create a NEW Private App (not an OAuth app)
3. Grant these scopes:
   - crm.objects.deals.read
   - crm.objects.deals.write
4. Copy the Access Token (starts with 'pat-')
5. Use that token in the configuration

Important: Private Apps and OAuth Apps are different!
- OAuth Apps: For building public integrations
- Private Apps: For internal/private use (what you need)
""")
    else:
        print("""
To get the correct token:

1. Log in to HubSpot
2. Settings (gear icon) → Integrations → Private Apps
3. Click "Create a private app"
4. Name it (e.g., "SAM.gov Integration")
5. Go to Scopes tab
6. Select:
   ✅ crm.objects.deals.read
   ✅ crm.objects.deals.write
7. Create app
8. Copy the Access Token (starts with 'pat-na1-' or 'pat-eu1-')
9. Paste it in the application config

Common mistakes:
❌ Using Client ID/Secret from an OAuth app
❌ Using an API key (deprecated)
❌ Missing required scopes
❌ Extra spaces when copying token
✅ Use Private App Access Token
""")

if __name__ == "__main__":
    main()