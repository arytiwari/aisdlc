import React, { useState, useEffect } from 'react';
import {
  Upload,
  TrendingUp,
  Database,
  Bell,
  Settings,
  Play,
  RefreshCw,
  BarChart3,
  CheckCircle,
  XCircle,
  Clock,
  Download,
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService from './services/api';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [models, setModels] = useState([]);
  const [bestModel, setBestModel] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({});
  const [retrainHistory, setRetrainHistory] = useState([]);

  useEffect(() => {
    loadInitialData();
    // Poll for notifications every 30 seconds
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedDataset) {
      loadDatasetDetails(selectedDataset.id);
    }
  }, [selectedDataset]);

  const loadInitialData = async () => {
    try {
      await Promise.all([
        loadDatasets(),
        loadNotifications(),
        loadConfig(),
      ]);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };

  const loadDatasets = async () => {
    try {
      const response = await apiService.getDatasets();
      setDatasets(response.data);
      if (response.data.length > 0 && !selectedDataset) {
        setSelectedDataset(response.data[0]);
      }
    } catch (error) {
      console.error('Error loading datasets:', error);
    }
  };

  const loadDatasetDetails = async (datasetId) => {
    try {
      setLoading(true);
      const [modelsRes, comparisonRes, bestModelRes, historyRes] = await Promise.all([
        apiService.getModels(datasetId),
        apiService.compareModels(datasetId).catch(() => ({ data: null })),
        apiService.getBestModel(datasetId).catch(() => ({ data: null })),
        apiService.getRetrainHistory(datasetId).catch(() => ({ data: [] })),
      ]);

      setModels(modelsRes.data);
      setComparison(comparisonRes.data);
      setBestModel(bestModelRes.data);
      setRetrainHistory(historyRes.data);
    } catch (error) {
      console.error('Error loading dataset details:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await apiService.getNotifications(false, 50);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const response = await apiService.getConfig();
      setConfig(response.data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setLoading(true);
      await apiService.uploadDataset(file);
      await loadDatasets();
      alert('Dataset uploaded successfully!');
    } catch (error) {
      alert('Error uploading dataset: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateModels = async () => {
    if (!selectedDataset) return;

    try {
      setLoading(true);
      const response = await apiService.generateModels(selectedDataset.id);
      alert(`Successfully generated ${response.data.models.length} models!`);
      await loadDatasetDetails(selectedDataset.id);
    } catch (error) {
      alert('Error generating models: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModels = async () => {
    if (!selectedDataset) return;

    try {
      setLoading(true);
      const response = await apiService.trainModels(selectedDataset.id);
      alert(`Successfully trained models!`);
      await loadDatasetDetails(selectedDataset.id);
      await loadNotifications();
    } catch (error) {
      alert('Error training models: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerRetrain = async () => {
    if (!selectedDataset) return;

    if (!confirm('This will retrain all models for the selected dataset. Continue?')) {
      return;
    }

    try {
      setLoading(true);
      await apiService.triggerRetrain(selectedDataset.id, 'manual');
      alert('Retraining triggered successfully! This may take a few minutes.');
      await loadDatasetDetails(selectedDataset.id);
      await loadNotifications();
    } catch (error) {
      alert('Error triggering retrain: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkNotificationRead = async (id) => {
    try {
      await apiService.markNotificationRead(id);
      await loadNotifications();
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const handleConfigUpdate = async (key, value) => {
    try {
      await apiService.updateConfig(key, value);
      await loadConfig();
      alert('Configuration updated successfully!');
    } catch (error) {
      alert('Error updating configuration: ' + error.message);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle size={20} />;
      case 'error':
        return <XCircle size={20} />;
      case 'warning':
        return <Clock size={20} />;
      default:
        return <Bell size={20} />;
    }
  };

  const prepareForecastData = () => {
    if (!bestModel || !bestModel.forecast) return [];

    return bestModel.forecast.map((item) => ({
      date: new Date(item.date).toLocaleDateString(),
      value: item.value,
    }));
  };

  const prepareComparisonData = () => {
    if (!comparison || !comparison.comparison) return [];

    return comparison.comparison.map((model) => ({
      name: model.model_type.toUpperCase(),
      MAE: model.mae,
      RMSE: model.rmse,
      MAPE: model.mape,
      R2: model.r2_score * 100,
    }));
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>Automated Sales Forecasting System</h1>
        <p>AI-powered forecasting that generates, tests, and self-improves</p>
        <div className="header-actions">
          <label className="button button-primary">
            <Upload size={18} />
            Upload Dataset
            <input type="file" accept=".csv,.xlsx" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>
          {selectedDataset && (
            <>
              <button className="button button-success" onClick={handleGenerateModels} disabled={loading}>
                <TrendingUp size={18} />
                Generate Models
              </button>
              <button className="button button-success" onClick={handleTrainModels} disabled={loading}>
                <Play size={18} />
                Train Models
              </button>
              <button className="button button-secondary" onClick={handleTriggerRetrain} disabled={loading}>
                <RefreshCw size={18} />
                Retrain All
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart3 size={18} /> Dashboard
          </button>
          <button
            className={`tab ${activeTab === 'datasets' ? 'active' : ''}`}
            onClick={() => setActiveTab('datasets')}
          >
            <Database size={18} /> Datasets
          </button>
          <button
            className={`tab ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            <Bell size={18} /> Notifications
            {notifications.filter((n) => !n.is_read).length > 0 && (
              <span className="badge badge-danger" style={{ marginLeft: '0.5rem' }}>
                {notifications.filter((n) => !n.is_read).length}
              </span>
            )}
          </button>
          <button
            className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={18} /> Settings
          </button>
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div>
            {selectedDataset ? (
              <>
                {/* Dataset Info */}
                <div className="card">
                  <h2>Current Dataset: {selectedDataset.name}</h2>
                  <div className="grid grid-3" style={{ marginTop: '1rem' }}>
                    <div className="stat-card">
                      <div className="stat-value">{selectedDataset.row_count}</div>
                      <div className="stat-label">Data Points</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{models.length}</div>
                      <div className="stat-label">Models Generated</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">
                        {models.filter((m) => m.is_trained).length}
                      </div>
                      <div className="stat-label">Models Trained</div>
                    </div>
                  </div>
                  <p style={{ marginTop: '1rem', color: '#5a6c7d' }}>
                    Date Range: {selectedDataset.date_range_start} to {selectedDataset.date_range_end}
                  </p>
                </div>

                {/* Best Model */}
                {bestModel && (
                  <div className="card">
                    <h2>Best Performing Model</h2>
                    <div className="grid grid-2">
                      <div>
                        <h3>Model Information</h3>
                        <p><strong>Type:</strong> {bestModel.model.model_type.toUpperCase()}</p>
                        <p><strong>Created:</strong> {formatDate(bestModel.model.created_date)}</p>
                        <p style={{ marginTop: '1rem' }}>
                          <span className="badge badge-success">Best Model</span>
                        </p>
                      </div>
                      <div>
                        <h3>Performance Metrics</h3>
                        <table className="table">
                          <tbody>
                            <tr>
                              <td><strong>MAE</strong></td>
                              <td>{bestModel.evaluation.mae.toFixed(2)}</td>
                            </tr>
                            <tr>
                              <td><strong>RMSE</strong></td>
                              <td>{bestModel.evaluation.rmse.toFixed(2)}</td>
                            </tr>
                            <tr>
                              <td><strong>MAPE</strong></td>
                              <td>{bestModel.evaluation.mape.toFixed(2)}%</td>
                            </tr>
                            <tr>
                              <td><strong>R²</strong></td>
                              <td>{bestModel.evaluation.r2_score.toFixed(4)}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Forecast Chart */}
                    {bestModel.forecast && bestModel.forecast.length > 0 && (
                      <div>
                        <h3 style={{ marginTop: '2rem' }}>30-Day Forecast</h3>
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={prepareForecastData()}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="date" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Line
                                type="monotone"
                                dataKey="value"
                                stroke="#667eea"
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                name="Predicted Sales"
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Model Comparison */}
                {comparison && comparison.comparison && comparison.comparison.length > 0 && (
                  <div className="card">
                    <h2>Model Comparison</h2>
                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={prepareComparisonData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="MAE" fill="#667eea" />
                          <Bar dataKey="RMSE" fill="#764ba2" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    <table className="table" style={{ marginTop: '2rem' }}>
                      <thead>
                        <tr>
                          <th>Model</th>
                          <th>MAE</th>
                          <th>RMSE</th>
                          <th>MAPE</th>
                          <th>R²</th>
                          <th>Training Time</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparison.comparison.map((model, index) => (
                          <tr key={index}>
                            <td><strong>{model.model_type.toUpperCase()}</strong></td>
                            <td>{model.mae.toFixed(2)}</td>
                            <td>{model.rmse.toFixed(2)}</td>
                            <td>{model.mape.toFixed(2)}%</td>
                            <td>{model.r2_score.toFixed(4)}</td>
                            <td>{model.training_time.toFixed(2)}s</td>
                            <td>
                              {model.is_best ? (
                                <span className="badge badge-success">Best</span>
                              ) : (
                                <span className="badge badge-info">Trained</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Retrain History */}
                {retrainHistory && retrainHistory.length > 0 && (
                  <div className="card">
                    <h2>Retraining History</h2>
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Reason</th>
                          <th>Old MAE</th>
                          <th>New MAE</th>
                          <th>Improvement</th>
                          <th>Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {retrainHistory.map((log) => (
                          <tr key={log.id}>
                            <td>{formatDate(log.date)}</td>
                            <td>
                              <span className="badge badge-info">{log.reason}</span>
                            </td>
                            <td>{log.old_mae?.toFixed(2) || 'N/A'}</td>
                            <td>{log.new_mae.toFixed(2)}</td>
                            <td>
                              {log.improvement > 0 ? (
                                <span className="badge badge-success">
                                  +{log.improvement.toFixed(2)}%
                                </span>
                              ) : (
                                <span className="badge badge-warning">
                                  {log.improvement.toFixed(2)}%
                                </span>
                              )}
                            </td>
                            <td>{log.details}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Database size={64} />
                </div>
                <div className="empty-state-text">No dataset selected</div>
                <p>Upload a dataset to get started with forecasting</p>
              </div>
            )}
          </div>
        )}

        {/* Datasets Tab */}
        {activeTab === 'datasets' && (
          <div className="card">
            <h2>Your Datasets</h2>
            {datasets.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Rows</th>
                    <th>Date Range</th>
                    <th>Uploaded</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((dataset) => (
                    <tr key={dataset.id}>
                      <td><strong>{dataset.name}</strong></td>
                      <td>{dataset.row_count}</td>
                      <td>
                        {dataset.date_range_start} to {dataset.date_range_end}
                      </td>
                      <td>{formatDate(dataset.upload_date)}</td>
                      <td>
                        {dataset.is_active ? (
                          <span className="badge badge-success">Active</span>
                        ) : (
                          <span className="badge badge-danger">Inactive</span>
                        )}
                      </td>
                      <td>
                        <button
                          className="button button-secondary"
                          style={{ padding: '0.5rem 1rem' }}
                          onClick={() => {
                            setSelectedDataset(dataset);
                            setActiveTab('dashboard');
                          }}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Database size={64} />
                </div>
                <div className="empty-state-text">No datasets yet</div>
                <p>Upload your first sales dataset to begin</p>
              </div>
            )}
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === 'notifications' && (
          <div className="card">
            <h2>Notifications</h2>
            {notifications.length > 0 ? (
              <div>
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                    onClick={() => handleMarkNotificationRead(notification.id)}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                      <div style={{ marginTop: '0.25rem' }}>
                        {getNotificationIcon(notification.notification_type)}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div className="notification-title">
                          {notification.title}
                          {!notification.is_read && (
                            <span className="badge badge-primary" style={{ marginLeft: '0.5rem' }}>
                              New
                            </span>
                          )}
                        </div>
                        <div className="notification-message">{notification.message}</div>
                        <div className="notification-time">
                          {formatDate(notification.created_date)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Bell size={64} />
                </div>
                <div className="empty-state-text">No notifications</div>
                <p>You're all caught up!</p>
              </div>
            )}
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="card">
            <h2>System Settings</h2>

            <div className="form-group">
              <label className="form-label">Auto-Retraining</label>
              <select
                className="form-control"
                value={config.auto_retrain_enabled || 'true'}
                onChange={(e) => handleConfigUpdate('auto_retrain_enabled', e.target.value)}
              >
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
              <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#5a6c7d' }}>
                Automatically retrain models on schedule to improve performance
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Retrain Schedule (hours)</label>
              <input
                type="number"
                className="form-control"
                value={config.retrain_schedule_hours || '24'}
                onChange={(e) => handleConfigUpdate('retrain_schedule_hours', e.target.value)}
                min="1"
                max="168"
              />
              <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#5a6c7d' }}>
                How often to automatically retrain models (1-168 hours)
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Performance Threshold</label>
              <input
                type="number"
                className="form-control"
                value={config.performance_threshold || '0.10'}
                onChange={(e) => handleConfigUpdate('performance_threshold', e.target.value)}
                step="0.01"
                min="0.01"
                max="1.0"
              />
              <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#5a6c7d' }}>
                Trigger retraining when performance degrades by this percentage (e.g., 0.10 = 10%)
              </p>
            </div>

            <div className="alert alert-info" style={{ marginTop: '2rem' }}>
              <Bell size={18} />
              <div>
                <strong>About Auto-Retraining:</strong>
                <p style={{ marginTop: '0.5rem' }}>
                  The system monitors model performance and automatically retrains when performance
                  degrades or on the specified schedule. You'll receive notifications about all
                  retraining events and performance changes.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading Overlay */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p style={{ marginTop: '1rem' }}>Processing...</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
