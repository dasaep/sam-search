import React, { useState, useEffect } from 'react';
import { hubspotService, statisticsService } from '../services/api';

function HubSpotDashboard() {
  const [hubspotStats, setHubspotStats] = useState(null);
  const [systemStats, setSystemStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    fetchStatistics();
    
    // Set up auto-refresh if enabled
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchStatistics, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      
      // Fetch both HubSpot and system statistics
      const [hubspotResponse, systemResponse] = await Promise.all([
        hubspotService.getStatistics(),
        statisticsService.getStatistics()
      ]);
      
      setHubspotStats(hubspotResponse.data);
      setSystemStats(systemResponse.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(1)}%`;
  };

  if (loading && !hubspotStats) return <div className="loading">Loading statistics...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="hubspot-dashboard">
      <div className="dashboard-header">
        <h2>HubSpot Integration Dashboard</h2>
        <div className="dashboard-controls">
          <button 
            className="btn btn-secondary"
            onClick={fetchStatistics}
            disabled={loading}
          >
            Refresh
          </button>
          
          <label className="auto-refresh">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>System Overview</h3>
          {systemStats && (
            <div className="stat-content">
              <div className="stat-item">
                <span className="stat-label">Total Opportunities:</span>
                <span className="stat-value">{systemStats.total_opportunities}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Active Capabilities:</span>
                <span className="stat-value">{systemStats.active_capabilities}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">High Matches:</span>
                <span className="stat-value">{systemStats.high_matches}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Recent Opportunities:</span>
                <span className="stat-value">{systemStats.recent_opportunities}</span>
              </div>
            </div>
          )}
        </div>

        <div className="stat-card">
          <h3>HubSpot Sync Status</h3>
          {hubspotStats && (
            <div className="stat-content">
              <div className="stat-item">
                <span className="stat-label">Total Synced:</span>
                <span className="stat-value">{hubspotStats.total_synced}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Successful:</span>
                <span className="stat-value success">{hubspotStats.successful}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Failed:</span>
                <span className="stat-value error">{hubspotStats.failed}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Success Rate:</span>
                <span className="stat-value">{formatPercentage(hubspotStats.sync_percentage)}</span>
              </div>
            </div>
          )}
        </div>

        <div className="stat-card">
          <h3>Sync Activity</h3>
          {hubspotStats && (
            <div className="stat-content">
              <div className="stat-item">
                <span className="stat-label">Last Sync:</span>
                <span className="stat-value">{formatDate(hubspotStats.last_sync)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Pending Sync:</span>
                <span className="stat-value">
                  {systemStats ? systemStats.total_opportunities - hubspotStats.total_synced : 0}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="stat-card">
          <h3>Sync Performance</h3>
          <div className="stat-content">
            <div className="sync-chart">
              {hubspotStats && (
                <>
                  <div className="chart-bar">
                    <div 
                      className="bar success"
                      style={{ width: `${hubspotStats.sync_percentage}%` }}
                    >
                      <span>Successful</span>
                    </div>
                  </div>
                  <div className="chart-bar">
                    <div 
                      className="bar error"
                      style={{ width: `${100 - hubspotStats.sync_percentage}%` }}
                    >
                      <span>Failed</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="recent-sync-activity">
        <h3>Recent Sync Activity</h3>
        <div className="activity-log">
          {/* This could be populated with recent sync events */}
          <div className="log-entry">
            <span className="log-time">{formatDate(hubspotStats?.last_sync)}</span>
            <span className="log-message">Last synchronization completed</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HubSpotDashboard;