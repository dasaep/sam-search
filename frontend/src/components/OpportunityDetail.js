import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { opportunityService } from '../services/api';

function OpportunityDetail() {
  const { id } = useParams();
  const [opportunity, setOpportunity] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOpportunityDetail();
  }, [id]);

  const fetchOpportunityDetail = async () => {
    try {
      setLoading(true);
      const response = await opportunityService.getOpportunity(id);
      setOpportunity(response.data.opportunity);
      setMatches(response.data.matches || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      const response = await opportunityService.analyzeOpportunity(id);
      setMatches(response.data);
      alert('Analysis complete!');
    } catch (err) {
      alert('Error analyzing opportunity: ' + err.message);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getMatchBadgeClass = (percentage) => {
    if (percentage >= 80) return 'match-high';
    if (percentage >= 50) return 'match-medium';
    return 'match-low';
  };

  if (loading) return <div className="loading">Loading opportunity details...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!opportunity) return <div className="empty-state">Opportunity not found</div>;

  return (
    <div className="detail-container">
      <div className="detail-header">
        <h2>{opportunity.title}</h2>
        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
          <a 
            href={opportunity.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            View on SAM.gov
          </a>
          <button className="btn btn-success" onClick={handleAnalyze}>
            Re-analyze Matches
          </button>
          <Link to="/opportunities" className="btn btn-secondary">
            Back to List
          </Link>
        </div>
      </div>

      <div className="detail-section">
        <h3>Opportunity Details</h3>
        <div className="detail-grid">
          <div className="detail-item">
            <label>Agency</label>
            <div className="value">{opportunity.agency}</div>
          </div>
          <div className="detail-item">
            <label>Posted Date</label>
            <div className="value">{formatDate(opportunity.posted_date)}</div>
          </div>
          <div className="detail-item">
            <label>Due Date</label>
            <div className="value">{formatDate(opportunity.due_date)}</div>
          </div>
          <div className="detail-item">
            <label>Type</label>
            <div className="value">{opportunity.type}</div>
          </div>
          <div className="detail-item">
            <label>Set Aside</label>
            <div className="value">{opportunity.set_aside || 'None'}</div>
          </div>
          <div className="detail-item">
            <label>NAICS Code</label>
            <div className="value">{opportunity.naics}</div>
          </div>
        </div>
      </div>

      <div className="detail-section">
        <h3>Capability Matches ({matches.length})</h3>
        {matches.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Capability</th>
                <th>Match %</th>
                <th>Keywords Matched</th>
                <th>NAICS Match</th>
                <th>Agency Match</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((match) => (
                <tr key={match.capability_id}>
                  <td>{match.capability?.name || match.capability_name}</td>
                  <td>
                    <span className={`match-badge ${getMatchBadgeClass(match.match_percentage)}`}>
                      {match.match_percentage.toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    {match.match_details?.keyword_matches?.length > 0 
                      ? match.match_details.keyword_matches.join(', ')
                      : 'None'}
                  </td>
                  <td>{match.match_details?.naics_match ? 'Yes' : 'No'}</td>
                  <td>{match.match_details?.agency_match ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <p>No capability matches found. Click "Re-analyze Matches" to check for matches.</p>
          </div>
        )}
      </div>

      {opportunity.raw_data && opportunity.raw_data.description && (
        <div className="detail-section">
          <h3>Description</h3>
          <div style={{ whiteSpace: 'pre-wrap' }}>
            {opportunity.raw_data.description}
          </div>
        </div>
      )}
    </div>
  );
}

export default OpportunityDetail;