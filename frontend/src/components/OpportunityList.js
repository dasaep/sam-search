import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { opportunityService } from '../services/api';

function OpportunityList() {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    naics: '',
    agency: '',
    set_aside: '',
    days: '7'
  });

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const response = await opportunityService.getOpportunities(filters);
      setOpportunities(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value
    });
  };

  const handleApplyFilters = () => {
    fetchOpportunities();
  };

  const handleAnalyze = async (id) => {
    try {
      await opportunityService.analyzeOpportunity(id);
      alert('Analysis complete! Check the opportunity details for matches.');
    } catch (err) {
      alert('Error analyzing opportunity: ' + err.message);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  if (loading) return <div className="loading">Loading opportunities...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="opportunity-list-container">
      <h2>Opportunities</h2>
      
      <div className="filters">
        <div className="filter-group">
          <label>NAICS Code</label>
          <input 
            type="text" 
            name="naics" 
            value={filters.naics}
            onChange={handleFilterChange}
            placeholder="e.g., 541511"
          />
        </div>
        
        <div className="filter-group">
          <label>Agency</label>
          <input 
            type="text" 
            name="agency" 
            value={filters.agency}
            onChange={handleFilterChange}
            placeholder="e.g., DOD"
          />
        </div>
        
        <div className="filter-group">
          <label>Set Aside</label>
          <select 
            name="set_aside" 
            value={filters.set_aside}
            onChange={handleFilterChange}
          >
            <option value="">All</option>
            <option value="SBA">Total Small Business</option>
            <option value="8A">8(a)</option>
            <option value="HZC">HUBZone</option>
            <option value="SDVOSBC">SDVOSB</option>
            <option value="WOSB">WOSB</option>
          </select>
        </div>
        
        <div className="filter-group">
          <label>Days Back</label>
          <select 
            name="days" 
            value={filters.days}
            onChange={handleFilterChange}
          >
            <option value="1">1 Day</option>
            <option value="7">7 Days</option>
            <option value="14">14 Days</option>
            <option value="30">30 Days</option>
          </select>
        </div>
        
        <button className="btn btn-primary" onClick={handleApplyFilters}>
          Apply Filters
        </button>
      </div>

      {opportunities.length > 0 ? (
        <div className="opportunity-list">
          {opportunities.map((opp) => (
            <div key={opp._id} className="opportunity-card">
              <div className="opportunity-header">
                <Link 
                  to={`/opportunities/${opp._id}`} 
                  className="opportunity-title"
                >
                  {opp.title}
                </Link>
                <span className="agency-badge">{opp.agency}</span>
              </div>
              
              <div className="opportunity-meta">
                <span>Posted: {formatDate(opp.posted_date)}</span>
                <span>Due: {formatDate(opp.due_date)}</span>
                <span>Type: {opp.type}</span>
                <span>NAICS: {opp.naics}</span>
              </div>
              
              <div className="tags">
                {opp.set_aside && opp.set_aside !== 'NONE' && (
                  <span className="tag">{opp.set_aside}</span>
                )}
              </div>
              
              <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                <a 
                  href={opp.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  View on SAM.gov
                </a>
                <button 
                  className="btn btn-success"
                  onClick={() => handleAnalyze(opp._id)}
                >
                  Analyze Match
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No opportunities found</h3>
          <p>Try adjusting your filters</p>
        </div>
      )}
    </div>
  );
}

export default OpportunityList;