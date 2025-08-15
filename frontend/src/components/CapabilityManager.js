import React, { useState, useEffect } from 'react';
import { capabilityService } from '../services/api';

function CapabilityManager() {
  const [capabilities, setCapabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCapability, setEditingCapability] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    keywords: [],
    naics_codes: [],
    preferred_agencies: [],
    preferred_set_asides: [],
    active: true
  });
  const [keywordInput, setKeywordInput] = useState('');
  const [naicsInput, setNaicsInput] = useState('');
  const [agencyInput, setAgencyInput] = useState('');

  useEffect(() => {
    fetchCapabilities();
  }, []);

  const fetchCapabilities = async () => {
    try {
      setLoading(true);
      const response = await capabilityService.getCapabilities(false);
      setCapabilities(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleAddKeyword = () => {
    if (keywordInput.trim()) {
      setFormData({
        ...formData,
        keywords: [...formData.keywords, keywordInput.trim()]
      });
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (index) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((_, i) => i !== index)
    });
  };

  const handleAddNaics = () => {
    if (naicsInput.trim()) {
      setFormData({
        ...formData,
        naics_codes: [...formData.naics_codes, naicsInput.trim()]
      });
      setNaicsInput('');
    }
  };

  const handleRemoveNaics = (index) => {
    setFormData({
      ...formData,
      naics_codes: formData.naics_codes.filter((_, i) => i !== index)
    });
  };

  const handleAddAgency = () => {
    if (agencyInput.trim()) {
      setFormData({
        ...formData,
        preferred_agencies: [...formData.preferred_agencies, agencyInput.trim()]
      });
      setAgencyInput('');
    }
  };

  const handleRemoveAgency = (index) => {
    setFormData({
      ...formData,
      preferred_agencies: formData.preferred_agencies.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCapability) {
        await capabilityService.updateCapability(editingCapability._id, formData);
      } else {
        await capabilityService.createCapability(formData);
      }
      fetchCapabilities();
      resetForm();
    } catch (err) {
      alert('Error saving capability: ' + err.message);
    }
  };

  const handleEdit = (capability) => {
    setEditingCapability(capability);
    setFormData({
      name: capability.name,
      description: capability.description || '',
      keywords: capability.keywords || [],
      naics_codes: capability.naics_codes || [],
      preferred_agencies: capability.preferred_agencies || [],
      preferred_set_asides: capability.preferred_set_asides || [],
      active: capability.active
    });
    setShowForm(true);
  };

  const handleToggleActive = async (capability) => {
    try {
      await capabilityService.updateCapability(capability._id, {
        active: !capability.active
      });
      fetchCapabilities();
    } catch (err) {
      alert('Error updating capability: ' + err.message);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      keywords: [],
      naics_codes: [],
      preferred_agencies: [],
      preferred_set_asides: [],
      active: true
    });
    setEditingCapability(null);
    setShowForm(false);
    setKeywordInput('');
    setNaicsInput('');
    setAgencyInput('');
  };

  if (loading) return <div className="loading">Loading capabilities...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="capability-manager">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Capability Management</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : 'Add New Capability'}
        </button>
      </div>

      {showForm && (
        <form className="capability-form" onSubmit={handleSubmit}>
          <h3>{editingCapability ? 'Edit Capability' : 'New Capability'}</h3>
          
          <div className="form-group">
            <label>Name *</label>
            <input 
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea 
              name="description"
              value={formData.description}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label>Keywords</label>
            <div className="keywords-input">
              <input 
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
                placeholder="Add keyword and press Enter"
              />
              <button type="button" className="btn btn-secondary" onClick={handleAddKeyword}>
                Add
              </button>
            </div>
            <div className="keyword-list">
              {formData.keywords.map((keyword, index) => (
                <span key={index} className="keyword-tag">
                  {keyword}
                  <button type="button" onClick={() => handleRemoveKeyword(index)}>×</button>
                </span>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>NAICS Codes</label>
            <div className="keywords-input">
              <input 
                type="text"
                value={naicsInput}
                onChange={(e) => setNaicsInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddNaics())}
                placeholder="Add NAICS code and press Enter"
              />
              <button type="button" className="btn btn-secondary" onClick={handleAddNaics}>
                Add
              </button>
            </div>
            <div className="keyword-list">
              {formData.naics_codes.map((naics, index) => (
                <span key={index} className="keyword-tag">
                  {naics}
                  <button type="button" onClick={() => handleRemoveNaics(index)}>×</button>
                </span>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Preferred Agencies</label>
            <div className="keywords-input">
              <input 
                type="text"
                value={agencyInput}
                onChange={(e) => setAgencyInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAgency())}
                placeholder="Add agency and press Enter"
              />
              <button type="button" className="btn btn-secondary" onClick={handleAddAgency}>
                Add
              </button>
            </div>
            <div className="keyword-list">
              {formData.preferred_agencies.map((agency, index) => (
                <span key={index} className="keyword-tag">
                  {agency}
                  <button type="button" onClick={() => handleRemoveAgency(index)}>×</button>
                </span>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>
              <input 
                type="checkbox"
                name="active"
                checked={formData.active}
                onChange={(e) => setFormData({...formData, active: e.target.checked})}
              />
              {' '}Active
            </label>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="submit" className="btn btn-primary">
              {editingCapability ? 'Update' : 'Create'} Capability
            </button>
            <button type="button" className="btn btn-secondary" onClick={resetForm}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {capabilities.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Keywords</th>
              <th>NAICS Codes</th>
              <th>Agencies</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {capabilities.map((cap) => (
              <tr key={cap._id}>
                <td>{cap.name}</td>
                <td>{cap.keywords?.join(', ') || 'None'}</td>
                <td>{cap.naics_codes?.join(', ') || 'None'}</td>
                <td>{cap.preferred_agencies?.join(', ') || 'None'}</td>
                <td>
                  <span className={`tag ${cap.active ? 'match-badge match-high' : ''}`}>
                    {cap.active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => handleEdit(cap)}
                    style={{ marginRight: '0.5rem' }}
                  >
                    Edit
                  </button>
                  <button 
                    className={`btn ${cap.active ? 'btn-secondary' : 'btn-success'}`}
                    onClick={() => handleToggleActive(cap)}
                  >
                    {cap.active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">
          <h3>No capabilities defined</h3>
          <p>Create your first capability to start matching opportunities</p>
        </div>
      )}
    </div>
  );
}

export default CapabilityManager;