import { useState, useEffect } from 'react';
import { getDashboardStats, getRecentAttempts } from '../services/api';
import DashboardStats from '../components/DashboardStats';
import AttemptTable from '../components/AttemptTable';
import './Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, recentData] = await Promise.all([
          getDashboardStats(),
          getRecentAttempts(),
        ]);
        setStats(statsData);
        setRecent(recentData);
      } catch (err) {
        setError('Failed to load dashboard data. Is the backend running?');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <span>Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error card">
        <p>⚠️ {error}</p>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', marginTop: 8 }}>
          Make sure Spring Boot (port 8080) and Flask (port 5000) are running.
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard animate-fade-in">
      <div className="dashboard-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Delivery attempt credibility monitoring</p>
        </div>
      </div>

      <DashboardStats stats={stats} />

      {/* Score Distribution mini-chart */}
      {stats && stats.totalAttempts > 0 && (
        <div className="distribution-bar card">
          <div className="distribution-header">
            <span className="section-title" style={{ marginBottom: 0 }}>Risk Distribution</span>
            <span className="label">{stats.totalAttempts} total</span>
          </div>
          <div className="distribution-track">
            {stats.highRiskCount > 0 && (
              <div
                className="distribution-segment seg-high"
                style={{ flex: stats.highRiskCount }}
                title={`High Risk: ${stats.highRiskCount}`}
              >
                <span>{stats.highRiskCount}</span>
              </div>
            )}
            {stats.mediumRiskCount > 0 && (
              <div
                className="distribution-segment seg-medium"
                style={{ flex: stats.mediumRiskCount }}
                title={`Medium Risk: ${stats.mediumRiskCount}`}
              >
                <span>{stats.mediumRiskCount}</span>
              </div>
            )}
            {stats.lowRiskCount > 0 && (
              <div
                className="distribution-segment seg-low"
                style={{ flex: stats.lowRiskCount }}
                title={`Low Risk: ${stats.lowRiskCount}`}
              >
                <span>{stats.lowRiskCount}</span>
              </div>
            )}
          </div>
          <div className="distribution-legend">
            <span><span className="risk-dot risk-dot-high"></span> High</span>
            <span><span className="risk-dot risk-dot-medium"></span> Medium</span>
            <span><span className="risk-dot risk-dot-low"></span> Low</span>
          </div>
        </div>
      )}

      <AttemptTable attempts={recent} />
    </div>
  );
}
