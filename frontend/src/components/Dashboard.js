import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { statisticsService, matchService } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [highMatches, setHighMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsResponse, matchesResponse] = await Promise.all([
        statisticsService.getStatistics(),
        matchService.getHighMatches(80, 5)
      ]);
      
      setStats(statsResponse.data);
      setHighMatches(matchesResponse.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!stats) return <div className="empty-state">No data available</div>;

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      
      <div className="dashboard-grid">
        <div className="stat-card">
          <h3>Total Opportunities</h3>
          <div className="value">{stats.total_opportunities}</div>
        </div>
        
        <div className="stat-card">
          <h3>Active Capabilities</h3>
          <div className="value">{stats.active_capabilities}</div>
        </div>
        
        <div className="stat-card">
          <h3>High Matches</h3>
          <div className="value">{stats.high_matches}</div>
        </div>
        
        <div className="stat-card">
          <h3>Today's Opportunities</h3>
          <div className="value">{stats.recent_opportunities}</div>
        </div>
      </div>

      <div className="detail-section">
        <h3>Recent High Matches</h3>
        {highMatches.length > 0 ? (
          <div className="opportunity-list">
            {highMatches.map((match) => (
              <div key={match._id} className="opportunity-card">
                <div className="opportunity-header">
                  <Link 
                    to={`/opportunities/${match.opportunity_id}`} 
                    className="opportunity-title"
                  >
                    {match.opportunity?.title}
                  </Link>
                  <span className="match-badge match-high">
                    {match.match_percentage.toFixed(0)}% Match
                  </span>
                </div>
                <div className="opportunity-meta">
                  <span>Agency: {match.opportunity?.agency}</span>
                  <span>Capability: {match.capability?.name}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No high matches found yet</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;