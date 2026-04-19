import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, MapPin, Clock, Phone, CreditCard, User, Timer, Map } from 'lucide-react';
import { getAttempt } from '../services/api';
import ScoreGauge from '../components/ScoreGauge';
import ReasonBreakdown from '../components/ReasonBreakdown';
import DisputeDraft from '../components/DisputeDraft';
import './AttemptDetail.css';

export default function AttemptDetail() {
  const { id } = useParams();
  const [attempt, setAttempt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchAttempt() {
      try {
        const data = await getAttempt(id);
        setAttempt(data);
      } catch (err) {
        setError('Failed to load attempt details');
      } finally {
        setLoading(false);
      }
    }
    fetchAttempt();
  }, [id]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <span>Loading attempt details...</span>
      </div>
    );
  }

  if (error || !attempt) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 'var(--space-2xl)' }}>
        <p>❌ {error || 'Attempt not found'}</p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 16 }}>
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>
    );
  }

  const featureCards = [
    { icon: MapPin, label: 'GPS Distance', value: attempt.gpsDistanceM >= 1000 ? `${(attempt.gpsDistanceM / 1000).toFixed(1)} km` : `${attempt.gpsDistanceM?.toFixed(0)} m` },
    { icon: Clock, label: 'Time Gap', value: `${attempt.timeGapMinutes?.toFixed(0)} min` },
    { icon: Phone, label: 'Call Made', value: attempt.callMade ? 'Yes' : 'No' },
    { icon: CreditCard, label: 'Payment', value: attempt.isCod ? 'COD' : 'Prepaid' },
    { icon: User, label: 'Exec Fake Rate', value: `${(attempt.execHistoricalFakeRate * 100).toFixed(1)}%` },
    { icon: Timer, label: 'To Shift End', value: `${attempt.minutesToShiftEnd?.toFixed(0)} min` },
    { icon: Map, label: 'Pincode Tier', value: attempt.pincodeTier === 1 ? 'Metro' : attempt.pincodeTier === 2 ? 'Tier-2' : 'Tier-3' },
  ];

  return (
    <div className="attempt-detail animate-fade-in">
      <div className="detail-header">
        <Link to="/" className="btn btn-ghost">
          <ArrowLeft size={16} /> Back
        </Link>
        <div>
          <h1 className="page-title">Attempt Analysis</h1>
          <p className="page-subtitle mono" style={{ fontSize: '0.8rem' }}>ID: {attempt.id}</p>
        </div>
      </div>

      <div className="detail-grid">
        {/* Left: Score Gauge */}
        <div className="detail-score-section card">
          <h3 className="section-title" style={{ textAlign: 'center' }}>Credibility Score</h3>
          <ScoreGauge score={attempt.credibilityScore} size={220} />
        </div>

        {/* Right: Feature Values */}
        <div className="detail-features-section">
          <h3 className="section-title">Raw Feature Values</h3>
          <div className="feature-grid stagger-children">
            {featureCards.map(({ icon: Icon, label, value }) => (
              <div key={label} className="feature-chip card">
                <Icon size={16} className="feature-chip-icon" />
                <div>
                  <div className="label">{label}</div>
                  <div className="feature-chip-value">{value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Reason Breakdown */}
      <div style={{ marginTop: 'var(--space-xl)' }}>
        <h3 className="section-title">Why This Score?</h3>
        <ReasonBreakdown reasons={attempt.reasons} />
      </div>

      {/* Dispute Draft */}
      <div style={{ marginTop: 'var(--space-xl)' }}>
        <DisputeDraft draft={attempt.disputeDraft} />
      </div>
    </div>
  );
}
