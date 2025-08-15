import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import axios from 'axios';
import './CRMWorkflow.css';

const STAGES = [
  { id: 'discovered', name: 'Discovered', color: '#6b7280' },
  { id: 'reviewing', name: 'Reviewing', color: '#3b82f6' },
  { id: 'qualified', name: 'Qualified', color: '#8b5cf6' },
  { id: 'proposal_prep', name: 'Proposal Prep', color: '#f59e0b' },
  { id: 'submitted', name: 'Submitted', color: '#10b981' },
  { id: 'awarded', name: 'Awarded', color: '#059669' },
  { id: 'lost', name: 'Lost', color: '#ef4444' },
  { id: 'declined', name: 'Declined', color: '#991b1b' }
];

function CRMWorkflow() {
  const [opportunities, setOpportunities] = useState({});
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pipelineStats, setPipelineStats] = useState(null);

  useEffect(() => {
    fetchOpportunities();
    fetchPipelineStats();
  }, []);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/crm/opportunities');
      
      // Group opportunities by stage
      const grouped = {};
      STAGES.forEach(stage => {
        grouped[stage.id] = [];
      });
      
      response.data.data.forEach(opp => {
        const stage = opp.crm_tracking?.stage || 'discovered';
        if (!grouped[stage]) grouped[stage] = [];
        grouped[stage].push(opp);
      });
      
      setOpportunities(grouped);
    } catch (error) {
      console.error('Error fetching CRM opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPipelineStats = async () => {
    try {
      const response = await axios.get('/api/crm/pipeline');
      setPipelineStats(response.data.data);
    } catch (error) {
      console.error('Error fetching pipeline stats:', error);
    }
  };

  const handleDragEnd = async (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;
    
    if (source.droppableId === destination.droppableId) return;

    // Move opportunity between stages
    const sourceStage = source.droppableId;
    const destStage = destination.droppableId;
    
    const sourceOpps = Array.from(opportunities[sourceStage]);
    const destOpps = Array.from(opportunities[destStage] || []);
    
    const [movedOpp] = sourceOpps.splice(source.index, 1);
    destOpps.splice(destination.index, 0, movedOpp);
    
    setOpportunities({
      ...opportunities,
      [sourceStage]: sourceOpps,
      [destStage]: destOpps
    });

    // Update stage in backend
    try {
      await axios.put(`/api/crm/opportunities/${draggableId}/stage`, {
        stage: destStage
      });
      
      // Refresh pipeline stats
      fetchPipelineStats();
    } catch (error) {
      console.error('Error updating opportunity stage:', error);
      // Revert on error
      fetchOpportunities();
    }
  };

  const handleOpportunityClick = (opportunity) => {
    setSelectedOpportunity(opportunity);
    setShowDetails(true);
  };

  const updateOpportunityField = async (field, value) => {
    if (!selectedOpportunity) return;

    try {
      await axios.put(`/api/crm/opportunities/${selectedOpportunity._id}/fields`, {
        [field]: value
      });
      
      // Update local state
      setSelectedOpportunity({
        ...selectedOpportunity,
        crm_tracking: {
          ...selectedOpportunity.crm_tracking,
          [field]: value
        }
      });
      
      // Refresh opportunities
      fetchOpportunities();
    } catch (error) {
      console.error('Error updating opportunity field:', error);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value);
  };

  if (loading) return <div className="loading">Loading CRM workflow...</div>;

  return (
    <div className="crm-workflow">
      <div className="crm-header">
        <h2>Opportunity Pipeline</h2>
        {pipelineStats && (
          <div className="pipeline-summary">
            <span>Total: {pipelineStats.total_opportunities} opportunities</span>
            <span>Total Value: {formatCurrency(
              pipelineStats.pipeline.reduce((sum, stage) => sum + stage.total_value, 0)
            )}</span>
          </div>
        )}
      </div>

      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="stages-container">
          {STAGES.map(stage => (
            <div key={stage.id} className="stage-column">
              <div 
                className="stage-header"
                style={{ borderTop: `3px solid ${stage.color}` }}
              >
                <h3>{stage.name}</h3>
                <span className="stage-count">
                  {opportunities[stage.id]?.length || 0}
                </span>
              </div>
              
              <Droppable droppableId={stage.id}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`stage-content ${snapshot.isDraggingOver ? 'dragging-over' : ''}`}
                  >
                    {opportunities[stage.id]?.map((opp, index) => (
                      <Draggable
                        key={opp._id}
                        draggableId={opp._id}
                        index={index}
                      >
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className={`opportunity-card ${snapshot.isDragging ? 'dragging' : ''}`}
                            onClick={() => handleOpportunityClick(opp)}
                          >
                            <div className="opp-title">{opp.title}</div>
                            <div className="opp-agency">{opp.agency}</div>
                            <div className="opp-meta">
                              <span>Due: {opp.due_date}</span>
                              {opp.crm_tracking?.estimated_value && (
                                <span className="opp-value">
                                  {formatCurrency(opp.crm_tracking.estimated_value)}
                                </span>
                              )}
                            </div>
                            {opp.crm_tracking?.priority && (
                              <span className={`priority-badge priority-${opp.crm_tracking.priority}`}>
                                {opp.crm_tracking.priority}
                              </span>
                            )}
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          ))}
        </div>
      </DragDropContext>

      {showDetails && selectedOpportunity && (
        <div className="opportunity-details-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Opportunity Details</h3>
              <button 
                className="close-button"
                onClick={() => setShowDetails(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <h4>{selectedOpportunity.title}</h4>
              
              <div className="detail-section">
                <label>Agency</label>
                <p>{selectedOpportunity.agency}</p>
              </div>
              
              <div className="detail-section">
                <label>Current Stage</label>
                <p>{STAGES.find(s => s.id === selectedOpportunity.crm_tracking?.stage)?.name}</p>
              </div>
              
              <div className="detail-section">
                <label>Priority</label>
                <select
                  value={selectedOpportunity.crm_tracking?.priority || 'medium'}
                  onChange={(e) => updateOpportunityField('priority', e.target.value)}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              
              <div className="detail-section">
                <label>Estimated Value</label>
                <input
                  type="number"
                  value={selectedOpportunity.crm_tracking?.estimated_value || ''}
                  onChange={(e) => updateOpportunityField('estimated_value', parseFloat(e.target.value))}
                  placeholder="Enter estimated value"
                />
              </div>
              
              <div className="detail-section">
                <label>Win Probability (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={selectedOpportunity.crm_tracking?.win_probability || 0}
                  onChange={(e) => updateOpportunityField('win_probability', parseInt(e.target.value))}
                />
              </div>
              
              <div className="detail-section">
                <label>Assigned To</label>
                <input
                  type="text"
                  value={selectedOpportunity.crm_tracking?.assigned_to || ''}
                  onChange={(e) => updateOpportunityField('assigned_to', e.target.value)}
                  placeholder="Enter assignee name"
                />
              </div>
              
              <div className="detail-actions">
                <a 
                  href={selectedOpportunity.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                >
                  View on SAM.gov
                </a>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setShowDetails(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CRMWorkflow;