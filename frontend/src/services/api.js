import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Datasets
  uploadDataset: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getDatasets: () => api.get('/api/datasets'),

  getDataset: (id) => api.get(`/api/datasets/${id}`),

  deleteDataset: (id) => api.delete(`/api/datasets/${id}`),

  // Models
  generateModels: (datasetId, modelTypes = null) =>
    api.post('/api/models/generate', null, {
      params: { dataset_id: datasetId, model_types: modelTypes },
    }),

  trainModels: (datasetId, modelIds = null) =>
    api.post('/api/models/train', null, {
      params: { dataset_id: datasetId, model_ids: modelIds },
    }),

  getModels: (datasetId = null) =>
    api.get('/api/models', {
      params: datasetId ? { dataset_id: datasetId } : {},
    }),

  getModelEvaluation: (modelId) =>
    api.get(`/api/models/${modelId}/evaluation`),

  getBestModel: (datasetId) => api.get(`/api/models/best/${datasetId}`),

  compareModels: (datasetId) => api.get(`/api/compare/${datasetId}`),

  // Notifications
  getNotifications: (unreadOnly = false, limit = 50) =>
    api.get('/api/notifications', {
      params: { unread_only: unreadOnly, limit },
    }),

  markNotificationRead: (id) =>
    api.patch(`/api/notifications/${id}/read`),

  // Retraining
  triggerRetrain: (datasetId, reason = 'manual') =>
    api.post('/api/retrain', { dataset_id: datasetId, reason }),

  getRetrainHistory: (datasetId) =>
    api.get(`/api/retrain/history/${datasetId}`),

  // Configuration
  getConfig: () => api.get('/api/config'),

  updateConfig: (key, value) =>
    api.patch('/api/config', { config_key: key, config_value: value }),
};

export default apiService;
