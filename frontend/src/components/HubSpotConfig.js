import React, { useState, useEffect } from 'react';
import { hubspotService } from '../services/api';

function HubSpotConfig() {
  const [config, setConfig] = useState({
    api_key: '',
    access_token: '',
    pipeline_id: 'default',
    default_stage_id: 'appointmentscheduled',
    sync_enabled: true,
    sync_interval_minutes: 30,
    webhook_enabled: false,
    webhook_url: '',
    auto_sync_new_opportunities: false,
    sync_direction: 'bidirectional'
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [showConfig, setShowConfig] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await hubspotService.getConfig();
      if (response.data) {
        setConfig({
          ...config,
          ...response.data,
          api_key: response.data.api_key === '***' ? '' : response.data.api_key,
          access_token: response.data.access_token === '***' ? '' : response.data.access_token
        });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to load configuration' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig({
      ...config,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setMessage(null);
      
      if (!config.api_key && !config.access_token) {
        setMessage({ type: 'error', text: 'Please provide either API Key or Access Token' });
        return;
      }
      
      const response = await hubspotService.saveConfig(config);
      
      if (response.success) {
        setMessage({ type: 'success', text: 'Configuration saved successfully!' });
        if (response.connection_test) {
          setTestResult(response.connection_test);
        }
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to save configuration' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    try {
      setLoading(true);
      setTestResult(null);
      
      const response = await hubspotService.testConnection();
      
      if (response.success) {
        setTestResult(response.data);
        setMessage({ type: 'success', text: 'Connection test successful!' });
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Connection test failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hubspot-config">
      <div className="config-header">
        <h2>HubSpot Configuration</h2>
        <button 
          className="toggle-btn"
          onClick={() => setShowConfig(!showConfig)}
        >
          {showConfig ? 'Hide' : 'Show'} Configuration
        </button>
      </div>

      {showConfig && (
        <div className="config-form">
          <div className="form-section">
            <h3>Authentication</h3>
            <p className="help-text">
              <strong>Important:</strong> HubSpot API Keys are deprecated. Use a Private App Access Token instead.
            </p>
            <p className="help-text">
              To get your Access Token:
              <br />1. Go to HubSpot Settings → Integrations → Private Apps
              <br />2. Create a new Private App or use existing one
              <br />3. Grant CRM scopes: crm.objects.deals.read, crm.objects.deals.write
              <br />4. Copy the Access Token from your app
            </p>
            
            <div className="form-group">
              <label>Private App Access Token (Required)</label>
              <input
                type="password"
                name="access_token"
                value={config.access_token}
                onChange={handleChange}
                placeholder="Enter your Private App Access Token"
              />
              <small>Starts with: pat-na1-...</small>
            </div>
            
            <div className="form-group">
              <label>API Key (Deprecated - Not Recommended)</label>
              <input
                type="password"
                name="api_key"
                value={config.api_key}
                onChange={handleChange}
                placeholder="Legacy API Key (if still using)"
                disabled={config.access_token ? true : false}
              />
              <small>Note: HubSpot API Keys are deprecated as of Nov 2022</small>
            </div>
          </div>

          <div className="form-section">
            <h3>Deal Settings</h3>
            
            <div className="form-group">
              <label>Pipeline ID</label>
              <input
                type="text"
                name="pipeline_id"
                value={config.pipeline_id}
                onChange={handleChange}
                placeholder="default"
              />
            </div>
            
            <div className="form-group">
              <label>Default Stage ID</label>
              <input
                type="text"
                name="default_stage_id"
                value={config.default_stage_id}
                onChange={handleChange}
                placeholder="appointmentscheduled"
              />
            </div>
          </div>

          <div className="form-section">
            <h3>Sync Settings</h3>
            
            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  name="sync_enabled"
                  checked={config.sync_enabled}
                  onChange={handleChange}
                />
                Enable Synchronization
              </label>
            </div>
            
            <div className="form-group">
              <label>Sync Interval (minutes)</label>
              <input
                type="number"
                name="sync_interval_minutes"
                value={config.sync_interval_minutes}
                onChange={handleChange}
                min="5"
                max="1440"
              />
            </div>
            
            <div className="form-group">
              <label>Sync Direction</label>
              <select
                name="sync_direction"
                value={config.sync_direction}
                onChange={handleChange}
              >
                <option value="one-way-to-hubspot">One-way to HubSpot</option>
                <option value="one-way-from-hubspot">One-way from HubSpot</option>
                <option value="bidirectional">Bidirectional</option>
              </select>
            </div>
            
            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  name="auto_sync_new_opportunities"
                  checked={config.auto_sync_new_opportunities}
                  onChange={handleChange}
                />
                Auto-sync New Opportunities
              </label>
            </div>
          </div>

          <div className="form-section">
            <h3>Webhook Settings (Optional)</h3>
            
            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  name="webhook_enabled"
                  checked={config.webhook_enabled}
                  onChange={handleChange}
                />
                Enable Webhooks
              </label>
            </div>
            
            {config.webhook_enabled && (
              <div className="form-group">
                <label>Webhook URL</label>
                <input
                  type="url"
                  name="webhook_url"
                  value={config.webhook_url}
                  onChange={handleChange}
                  placeholder="https://your-domain.com/webhook"
                />
              </div>
            )}
          </div>

          <div className="form-actions">
            <button 
              className="btn btn-primary"
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Configuration'}
            </button>
            
            <button 
              className="btn btn-secondary"
              onClick={handleTest}
              disabled={loading || (!config.api_key && !config.access_token)}
            >
              Test Connection
            </button>
          </div>

          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}

          {testResult && (
            <div className="test-result">
              <h4>Connection Test Result:</h4>
              <pre>{JSON.stringify(testResult, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default HubSpotConfig;