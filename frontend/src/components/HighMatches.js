import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { matchService } from '../services/api';

function HighMatches() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [threshold, setThreshold] = useState(70);

  useEffect(() => {
    fetchHighMatches();
  }, []);

  const fetchHighMatches = async () => {
    try {
      setLoading(true);
      const response = await matchService.getHighMatches(threshold, 100);
      setMatches(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleThresholdChange = (e) => {
    setThreshold(e.target.value);
  };

  const handleApplyThreshold = () => {
    fetchHighMatches();
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const getMatchBadgeClass = (percentage) => {
    if (percentage >= 80) return 'match-high';
    if (percentage >= 50) return 'match-medium';
    return 'match-low';
  };

  if (loading) return <div className="loading">Loading high matches...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="high-matches">
      <h2>High Match Opportunities</h2>
      
      <div className="filters">
        <div className="filter-group">
          <label>Match Threshold (%)</label>
          <input 
            type="number" 
            min="0" 
            max="100"
            value={threshold}
            onChange={handleThresholdChange}
          />
        </div>
        <button className="btn btn-primary" onClick={handleApplyThreshold}>
          Apply Threshold
        </button>
      </div>

      {matches.length > 0 ? (
        <div className="opportunity-list">
          {matches.map((match) => (
            <div key={match._id} className="opportunity-card">
              <div className="opportunity-header">
                <Link 
                  to={`/opportunities/${match.opportunity_id}`}
                  className="opportunity-title"
                >
                  {match.opportunity?.title}
                </Link>
                <span className={`match-badge ${getMatchBadgeClass(match.match_percentage)}`}>
                  {match.match_percentage.toFixed(0)}% Match
                </span>
              </div>
              
              <div className="opportunity-meta">
                <span>Agency: {match.opportunity?.agency}</span>
                <span>Posted: {formatDate(match.opportunity?.posted_date)}</span>
                <span>Due: {formatDate(match.opportunity?.due_date)}</span>
              </div>
              
              <div className="detail-section" style={{ marginTop: '1rem' }}>
                <strong>Matched Capability: </strong>{match.capability?.name}
              </div>
              
              {match.match_details && (
                <div className="tags" style={{ marginTop: '0.5rem' }}>
                  {match.match_details.keyword_matches?.length > 0 && (
                    <span className="tag">
                      Keywords: {match.match_details.keyword_matches.join(', ')}
                    </span>
                  )}
                  {match.match_details.naics_match && (
                    <span className="tag">NAICS Match</span>
                  )}
                  {match.match_details.agency_match && (
                    <span className="tag">Agency Match</span>
                  )}
                </div>
              )}
              
              <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                <Link 
                  to={`/opportunities/${match.opportunity_id}`}
                  className="btn btn-primary"
                >
                  View Details
                </Link>
                <a 
                  href={match.opportunity?.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  View on SAM.gov
                </a>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No high matches found</h3>
          <p>Try lowering the match threshold or analyzing more opportunities</p>
        </div>
      )}
    </div>
  );
}

export default HighMatches;