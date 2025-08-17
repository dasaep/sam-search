# HubSpot Authentication Guide

## Quick Start

You're getting a 401 Unauthorized error because you need a **Private App Access Token**, not a Client Key or API Key.

## Step-by-Step Instructions

### 1. Create a Private App in HubSpot

1. **Log in to HubSpot**
2. **Navigate to Settings**
   - Click the gear icon in the top navigation

3. **Go to Integrations → Private Apps**
   - In the left sidebar: Integrations → Private Apps

4. **Create a New Private App**
   - Click "Create a private app" button
   - Give it a name: "SAM.gov Integration" (or any name you prefer)
   - Add a description (optional)

### 2. Configure Scopes (Permissions)

1. **Click on the "Scopes" tab**

2. **Find and select these CRM scopes:**
   - Search for "deals" in the search box
   - Check these permissions:
     - ✅ `crm.objects.deals.read` - Read deals
     - ✅ `crm.objects.deals.write` - Write deals
   
3. **Optional but recommended:**
   - ✅ `crm.schemas.deals.read` - Read deal properties

### 3. Create the App and Get Your Token

1. **Click "Create app"** (or "Save" if editing existing app)
2. **Review and agree** to the terms
3. **Click "Continue creating"**
4. **Copy the Access Token**
   - The token will be displayed once
   - It starts with `pat-na1-` (or `pat-eu1-` for EU accounts)
   - **IMPORTANT:** Copy it now - you won't be able to see it again!

### 4. Use the Token in the Application

1. **Go to the HubSpot Configuration page** (`/hubspot-config`)
2. **Paste the token** in the "Private App Access Token" field
3. **Click "Test Connection"**
4. If successful, **click "Save Configuration"**

## Token Format

Your token should look like this:
```
pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Where:
- `pat` = Private App Token
- `na1` = North America region (could be `eu1` for Europe)
- The x's are alphanumeric characters

## Common Issues and Solutions

### Issue: 401 Unauthorized Error

**Causes:**
1. Using wrong type of credential (API Key, Client Key, Client Secret)
2. Token copied incorrectly (extra spaces, missing characters)
3. Token expired or revoked

**Solution:**
- Make sure you're using the Access Token from a Private App
- Re-copy the token carefully
- If needed, regenerate the token in HubSpot

### Issue: 403 Forbidden Error

**Cause:** Missing required permissions

**Solution:**
- Go back to your Private App in HubSpot
- Check that you've granted the `crm.objects.deals.read` and `crm.objects.deals.write` scopes
- Save the app again

### Issue: Token doesn't start with 'pat-'

**Cause:** You're using the wrong credential

**What you might be using instead:**
- **API Key**: 40-character string (deprecated)
- **Client ID**: Starts with a number
- **Client Secret**: Random string (this is for OAuth apps, not Private Apps)

**Solution:** Follow the steps above to create a Private App and get the Access Token

## Testing Your Connection

### Using the Test Script
```bash
python test_hubspot_connection.py YOUR_ACCESS_TOKEN
```

### Using the UI
1. Navigate to `/hubspot-config`
2. Enter your token
3. Click "Test Connection"

## Important Notes

1. **API Keys are Deprecated**: HubSpot deprecated API Keys in November 2022. You must use Private App Access Tokens.

2. **Keep Your Token Secure**: 
   - Never commit it to version control
   - Don't share it publicly
   - It has full access to the scopes you granted

3. **Token Regeneration**: 
   - You can regenerate your token at any time in HubSpot
   - Old tokens are immediately invalidated when you regenerate

4. **Rate Limits**: 
   - HubSpot has API rate limits
   - Private Apps have higher limits than API keys
   - Monitor your usage in HubSpot's dashboard

## Need More Help?

1. **HubSpot Documentation**: [Private Apps Guide](https://developers.hubspot.com/docs/api/private-apps)
2. **Check Application Logs**: Look for detailed error messages
3. **Run the Test Script**: `python test_hubspot_connection.py`
4. **Verify HubSpot Account**: Ensure your HubSpot account has API access (not all free accounts do)

## Visual Guide

```
HubSpot Settings
    └── Integrations
        └── Private Apps
            └── Create a private app
                ├── Basic Info Tab
                │   ├── Name: "SAM.gov Integration"
                │   └── Description: (optional)
                └── Scopes Tab
                    ├── ✅ crm.objects.deals.read
                    ├── ✅ crm.objects.deals.write
                    └── Create app → Copy Access Token
```

## Example Configuration in the App

After getting your token, in the application:

1. **Navigate to**: `/hubspot-config`
2. **Enter**:
   - Private App Access Token: `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - Leave API Key field empty
3. **Click**: "Test Connection"
4. **Expected Result**: "Connection successful"
5. **Click**: "Save Configuration"

You're now ready to sync opportunities to HubSpot!