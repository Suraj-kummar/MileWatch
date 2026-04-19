import { useNavigate } from 'react-router-dom';
import { Clock, MapPin, Phone, CreditCard } from 'lucide-react';
import './AttemptTable.css';

function getRiskClass(riskLevel) {
  if (riskLevel === 'HIGH_RISK') return 'high';
  if (riskLevel === 'MEDIUM_RISK') return 'medium';
  return 'low';
}

function getRiskLabel(riskLevel) {
  if (riskLevel === 'HIGH_RISK') return 'High Risk';
  if (riskLevel === 'MEDIUM_RISK') return 'Medium';
  return 'Low Risk';
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

export default function AttemptTable({ attempts, showTitle = true }) {
  const navigate = useNavigate();

  if (!attempts || attempts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <p>No delivery attempts scored yet</p>
        <p style={{ fontSize: '0.85rem', marginTop: 8 }}>Submit an attempt to see it here</p>
      </div>
    );
  }

  return (
    <div className="card attempt-table-wrapper animate-fade-in" style={{ padding: 0, overflow: 'hidden' }}>
      {showTitle && (
        <div style={{ padding: 'var(--space-lg) var(--space-lg) 0' }}>
          <h3 className="section-title">Recent Attempts</h3>
        </div>
      )}
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Score</th>
              <th>GPS Distance</th>
              <th>Call</th>
              <th>Type</th>
              <th>Executive</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {attempts.map((a) => {
              const risk = getRiskClass(a.riskLevel);
              return (
                <tr key={a.id} onClick={() => navigate(`/attempt/${a.id}`)}>
                  <td>
                    <div className={`risk-badge risk-badge-${risk}`}>
                      <span className={`risk-dot risk-dot-${risk}`}></span>
                      {getRiskLabel(a.riskLevel)}
                    </div>
                  </td>
                  <td>
                    <span className="mono" style={{ fontWeight: 600 }}>
                      {a.credibilityScore?.toFixed(2) ?? '—'}
                    </span>
                  </td>
                  <td>
                    <div className="table-cell-with-icon">
                      <MapPin size={14} className="table-icon" />
                      {a.gpsDistanceM >= 1000
                        ? `${(a.gpsDistanceM / 1000).toFixed(1)} km`
                        : `${a.gpsDistanceM?.toFixed(0)} m`
                      }
                    </div>
                  </td>
                  <td>
                    <span className={a.callMade ? 'text-positive' : 'text-negative'}>
                      {a.callMade ? '✓ Yes' : '✗ No'}
                    </span>
                  </td>
                  <td>
                    <span className="table-type-badge">
                      {a.isCod ? 'COD' : 'Prepaid'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    {a.execId || '—'}
                  </td>
                  <td style={{ color: 'var(--text-tertiary)', fontSize: '0.8rem' }}>
                    {formatDate(a.createdAt)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
