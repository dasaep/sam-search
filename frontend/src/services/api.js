import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const opportunityService = {
  getOpportunities: async (filters = {}) => {
    const response = await api.get('/opportunities', { params: filters });
    return response.data;
  },

  getOpportunity: async (id) => {
    const response = await api.get(`/opportunities/${id}`);
    return response.data;
  },

  analyzeOpportunity: async (id) => {
    const response = await api.post(`/opportunities/${id}/analyze`);
    return response.data;
  },
};

export const capabilityService = {
  getCapabilities: async (activeOnly = true) => {
    const response = await api.get('/capabilities', { params: { active: activeOnly } });
    return response.data;
  },

  createCapability: async (capability) => {
    const response = await api.post('/capabilities', capability);
    return response.data;
  },

  updateCapability: async (id, updates) => {
    const response = await api.put(`/capabilities/${id}`, updates);
    return response.data;
  },
};

export const matchService = {
  getHighMatches: async (threshold = 70, limit = 50) => {
    const response = await api.get('/matches/high', { params: { threshold, limit } });
    return response.data;
  },
};

export const statisticsService = {
  getStatistics: async () => {
    const response = await api.get('/statistics');
    return response.data;
  },
};

export default api;