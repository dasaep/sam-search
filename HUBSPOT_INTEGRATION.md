# HubSpot Integration Guide

This document describes the HubSpot integration features added to the SAM.gov Opportunity Analyzer application.

## Overview

The HubSpot integration allows you to:
- Sync SAM.gov opportunities to HubSpot as Deals
- Configure HubSpot connection settings through a UI
- Select multiple opportunities for bulk sync
- Track sync status for each opportunity
- Receive updates from HubSpot via webhooks
- View comprehensive sync statistics

## Features

### 1. HubSpot Configuration Screen
- Navigate to `/hubspot-config` to access the configuration interface
- Enter your HubSpot API credentials (API Key or OAuth Access Token)
- Configure sync settings:
  - Pipeline and default stage for new deals
  - Sync interval and direction
  - Auto-sync options for new opportunities
  - Webhook configuration (optional)

### 2. Bulk Opportunity Selection and Sync
- The enhanced opportunity list (`/opportunities`) includes:
  - Checkboxes for selecting multiple opportunities
  - "Select All" functionality
  - Bulk sync button to send selected opportunities to HubSpot
  - Individual sync status badges for each opportunity

### 3. Sync Status Display
Each opportunity shows its HubSpot sync status:
- **Not Synced** (gray): Never synced to HubSpot
- **Synced to HubSpot** (green): Successfully synced
- **Sync Error** (red): Failed to sync (hover for error details)

### 4. Bidirectional Synchronization
- **Push to HubSpot**: Send opportunities as deals
- **Pull from HubSpot**: Retrieve deal updates and status changes
- **Webhook Support**: Real-time updates when deals change in HubSpot

### 5. HubSpot Dashboard
Navigate to `/hubspot` to view:
- Total synced opportunities
- Success/failure rates
- Last sync timestamp
- Sync performance charts
- Recent sync activity log

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install
```

### 2. Configure HubSpot Access

#### Using Private App Access Token (Required)
1. Log in to your HubSpot account
2. Go to Settings → Integrations → Private Apps
3. Click "Create a private app" (or use an existing one)
4. Give your app a name (e.g., "SAM.gov Integration")
5. Go to the "Scopes" tab and select these CRM scopes:
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - (Optional) `crm.schemas.deals.read` for custom properties
6. Click "Create app" or "Save"
7. Copy the Access Token (it starts with `pat-na1-` or similar)
8. Enter this token in the configuration screen

**Important Notes:**
- HubSpot API Keys are deprecated as of November 2022
- Private App Access Tokens are the recommended authentication method
- The token should start with `pat-` followed by your region code
- Keep your token secure - it provides full access to your selected scopes

### 3. Create Custom Properties in HubSpot
The integration uses custom deal properties. Create these in HubSpot:
- `sam_opportunity_id` (text)
- `sam_notice_id` (text)
- `sam_agency` (text)
- `sam_naics` (text)
- `sam_set_aside` (text)
- `sam_url` (URL)
- `sam_posted_date` (date)

### 4. Configure Webhooks (Optional)
For real-time updates from HubSpot:
1. Set your webhook URL in the configuration
2. In HubSpot, configure webhooks for deal events
3. Point them to: `https://your-domain.com/api/hubspot/webhook`

## API Endpoints

### Configuration
- `GET /api/hubspot/config` - Get current configuration
- `POST /api/hubspot/config` - Save configuration
- `POST /api/hubspot/test` - Test HubSpot connection

### Synchronization
- `POST /api/hubspot/sync` - Sync opportunities to HubSpot
  - Body: `{ "opportunity_ids": ["id1", "id2", ...] }`
- `POST /api/hubspot/sync-from` - Pull updates from HubSpot
- `GET /api/hubspot/statistics` - Get sync statistics

### Opportunities with Sync Status
- `GET /api/opportunities/with-sync` - Get opportunities with HubSpot sync status

### Webhook
- `POST /api/hubspot/webhook` - Receive HubSpot webhook events

## Database Schema

### New Collections

#### hubspot_config
Stores HubSpot configuration settings (encrypted credentials)

#### hubspot_sync
Tracks sync status for each opportunity:
```javascript
{
  opportunity_id: "...",
  hubspot_deal_id: "...",
  sync_status: "created|updated|error|deleted",
  last_sync: Date,
  sync_error: "...",
  webhook_data: {...}
}
```

## Security Considerations

1. **Credential Storage**: API keys and tokens are encrypted using Fernet encryption
2. **Webhook Validation**: Supports HMAC signature validation for webhooks
3. **Access Control**: Configuration requires authentication (implement as needed)
4. **Rate Limiting**: HubSpot API has rate limits - the sync manager handles this

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify API credentials are correct
   - Check network connectivity
   - Ensure IP is whitelisted (if using private app)

2. **Sync Errors**
   - Check HubSpot API limits
   - Verify custom properties exist in HubSpot
   - Review error messages in sync status

3. **Webhook Not Working**
   - Verify webhook URL is publicly accessible
   - Check webhook signature validation
   - Review webhook logs

### Logs
Check application logs for detailed error messages:
```bash
tail -f app.log  # Backend logs
```

## Best Practices

1. **Initial Sync**: Start with a small batch to test the integration
2. **Regular Sync**: Set up scheduled sync (cron job or scheduler)
3. **Monitor Stats**: Regularly check the dashboard for sync health
4. **Handle Duplicates**: The system uses opportunity URL as unique identifier
5. **Error Recovery**: Failed syncs can be retried individually or in bulk

## Future Enhancements

Potential improvements to consider:
- Advanced field mapping UI
- Sync scheduling within the app
- Deal stage automation rules
- Contact and company association
- Custom workflow triggers
- Detailed audit logs
- Export sync reports

## Support

For issues or questions about the HubSpot integration:
1. Check the logs for error details
2. Verify configuration settings
3. Test connection using the test button
4. Review HubSpot API documentation