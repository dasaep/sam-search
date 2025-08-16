import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { opportunityService, hubspotService } from '../services/api';

function OpportunityListEnhanced() {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOpps, setSelectedOpps] = useState([]);
  const [syncStatus, setSyncStatus] = useState({});
  const [syncMessage, setSyncMessage] = useState(null);
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
      const response = await opportunityService.getOpportunitiesWithSync(filters);
      setOpportunities(response.data);
      
      // Extract sync status from opportunities
      const status = {};
      response.data.forEach(opp => {
        if (opp.hubspot_sync) {
          status[opp._id] = opp.hubspot_sync;
        }
      });
      setSyncStatus(status);
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

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedOpps(opportunities.map(opp => opp._id));
    } else {
      setSelectedOpps([]);
    }
  };

  const handleSelectOne = (oppId) => {
    if (selectedOpps.includes(oppId)) {
      setSelectedOpps(selectedOpps.filter(id => id !== oppId));
    } else {
      setSelectedOpps([...selectedOpps, oppId]);
    }
  };

  const handleSyncToHubSpot = async () => {
    if (selectedOpps.length === 0) {
      setSyncMessage({ type: 'error', text: 'Please select opportunities to sync' });
      return;
    }

    try {
      setLoading(true);
      setSyncMessage(null);
      
      const response = await hubspotService.syncToHubSpot(selectedOpps);
      
      if (response.success) {
        setSyncMessage({ 
          type: 'success', 
          text: `Synced ${response.data.successful} of ${response.data.total} opportunities successfully` 
        });
        
        // Refresh opportunities to show updated sync status
        await fetchOpportunities();
        setSelectedOpps([]);
      } else {
        setSyncMessage({ type: 'error', text: response.error || 'Sync failed' });
      }
    } catch (err) {
      setSyncMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncFromHubSpot = async () => {
    try {
      setLoading(true);
      setSyncMessage(null);
      
      const response = await hubspotService.syncFromHubSpot();
      
      if (response.success) {
        setSyncMessage({ 
          type: 'success', 
          text: `Updated ${response.data.updated} opportunities from HubSpot` 
        });
        
        // Refresh opportunities to show updated status
        await fetchOpportunities();
      } else {
        setSyncMessage({ type: 'error', text: response.error || 'Sync from HubSpot failed' });
      }
    } catch (err) {
      setSyncMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const getSyncStatusBadge = (oppId) => {
    const sync = syncStatus[oppId];
    if (!sync) {
      return <span className="badge badge-gray">Not Synced</span>;
    }
    
    switch (sync.sync_status) {
      case 'created':
      case 'updated':
        return (
          <span className="badge badge-green" title={`Deal ID: ${sync.hubspot_deal_id}`}>
            Synced to HubSpot
          </span>
        );
      case 'error':
        return (
          <span className="badge badge-red" title={sync.sync_error}>
            Sync Error
          </span>
        );
      default:
        return <span className="badge badge-gray">Unknown</span>;
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
      <div className="list-header">
        <h2>Opportunities</h2>
        <div className="sync-actions">
          <button 
            className="btn btn-primary"
            onClick={handleSyncToHubSpot}
            disabled={loading || selectedOpps.length === 0}
          >
            Sync {selectedOpps.length || ''} to HubSpot
          </button>
          
          <button 
            className="btn btn-secondary"
            onClick={handleSyncFromHubSpot}
            disabled={loading}
          >
            Sync from HubSpot
          </button>
        </div>
      </div>

      {syncMessage && (
        <div className={`message ${syncMessage.type}`}>
          {syncMessage.text}
        </div>
      )}
      
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
          <label>Days</label>
          <select 
            name="days" 
            value={filters.days}
            onChange={handleFilterChange}
          >
            <option value="1">Last 24 hours</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
        
        <button 
          className="btn btn-primary"
          onClick={handleApplyFilters}
        >
          Apply Filters
        </button>
      </div>

      <div className="opportunities-table">
        <table>
          <thead>
            <tr>
              <th>
                <input 
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={selectedOpps.length === opportunities.length && opportunities.length > 0}
                />
              </th>
              <th>Title</th>
              <th>Agency</th>
              <th>NAICS</th>
              <th>Set Aside</th>
              <th>Posted</th>
              <th>Due</th>
              <th>HubSpot Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map(opp => (
              <tr key={opp._id}>
                <td>
                  <input 
                    type="checkbox"
                    checked={selectedOpps.includes(opp._id)}
                    onChange={() => handleSelectOne(opp._id)}
                  />
                </td>
                <td className="opp-title">
                  <Link to={`/opportunity/${opp._id}`}>
                    {opp.title || 'Untitled'}
                  </Link>
                </td>
                <td>{opp.agency || 'N/A'}</td>
                <td>{opp.naics || 'N/A'}</td>
                <td>{opp.set_aside || 'N/A'}</td>
                <td>{formatDate(opp.posted_date)}</td>
                <td>{formatDate(opp.due_date)}</td>
                <td>{getSyncStatusBadge(opp._id)}</td>
                <td>
                  <div className="action-buttons">
                    <Link 
                      to={`/opportunity/${opp._id}`}
                      className="btn btn-sm btn-secondary"
                    >
                      View
                    </Link>
                    {opp.url && (
                      <a 
                        href={opp.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm btn-link"
                      >
                        SAM.gov
                      </a>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {opportunities.length === 0 && (
          <div className="no-results">
            No opportunities found matching your criteria.
          </div>
        )}
      </div>

      <div className="list-footer">
        <div className="selection-info">
          {selectedOpps.length} of {opportunities.length} selected
        </div>
        <div className="pagination">
          {/* Add pagination controls here if needed */}
        </div>
      </div>
    </div>
  );
}

export default OpportunityListEnhanced;