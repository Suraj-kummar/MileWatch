import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Loader } from 'lucide-react';
import { submitAttempt } from '../services/api';
import ScoreGauge from '../components/ScoreGauge';
import ReasonBreakdown from '../components/ReasonBreakdown';
import './SubmitAttempt.css';

const initialForm = {
  gpsDistanceM: '',
  timeGapMinutes: '',
  callMade: false,
  isCod: false,
  execHistoricalFakeRate: '',
  minutesToShiftEnd: '',
  pincodeTier: 1,
  execId: '',
  customerAddress: '',
};

export default function SubmitAttempt() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        gpsDistanceM: parseFloat(form.gpsDistanceM),
        timeGapMinutes: parseFloat(form.timeGapMinutes),
        callMade: form.callMade,
        isCod: form.isCod,
        execHistoricalFakeRate: parseFloat(form.execHistoricalFakeRate),
        minutesToShiftEnd: parseFloat(form.minutesToShiftEnd),
        pincodeTier: parseInt(form.pincodeTier),
        execId: form.execId || undefined,
        customerAddress: form.customerAddress || undefined,
      };

      const data = await submitAttempt(payload);
      setResult(data);
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.fields || 'Submission failed';
      setError(typeof msg === 'object' ? JSON.stringify(msg) : msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setForm(initialForm);
    setResult(null);
    setError(null);
  };

  // Quick-fill presets
  const presets = {
    suspicious: {
      gpsDistanceM: '3200', timeGapMinutes: '8', callMade: false, isCod: true,
      execHistoricalFakeRate: '0.28', minutesToShiftEnd: '12', pincodeTier: 2,
      execId: 'EXEC-042', customerAddress: '123 MG Road, Bangalore',
    },
    genuine: {
      gpsDistanceM: '120', timeGapMinutes: '38', callMade: true, isCod: false,
      execHistoricalFakeRate: '0.03', minutesToShiftEnd: '240', pincodeTier: 1,
      execId: 'EXEC-007', customerAddress: '456 Brigade Road, Bangalore',
    },
    borderline: {
      gpsDistanceM: '800', timeGapMinutes: '25', callMade: true, isCod: true,
      execHistoricalFakeRate: '0.12', minutesToShiftEnd: '45', pincodeTier: 2,
      execId: 'EXEC-019', customerAddress: '789 Koramangala, Bangalore',
    },
  };

  return (
    <div className="submit-page animate-fade-in">
      <h1 className="page-title">Score a Delivery Attempt</h1>
      <p className="page-subtitle">Enter the delivery attempt features to get a credibility score</p>

      {/* Presets */}
      <div className="presets-row">
        <span className="label">Quick Fill:</span>
        {Object.entries(presets).map(([key, values]) => (
          <button
            key={key}
            className="btn btn-ghost btn-sm"
            onClick={() => { setForm(prev => ({ ...prev, ...values })); setResult(null); }}
          >
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </button>
        ))}
      </div>

      <div className="submit-layout">
        {/* Form */}
        <form className="submit-form card" onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">GPS Distance (meters)</label>
              <input type="number" name="gpsDistanceM" value={form.gpsDistanceM}
                onChange={handleChange} className="form-input" placeholder="e.g. 3200"
                min="0" max="50000" step="any" required />
            </div>

            <div className="form-group">
              <label className="form-label">Time Gap (minutes)</label>
              <input type="number" name="timeGapMinutes" value={form.timeGapMinutes}
                onChange={handleChange} className="form-input" placeholder="e.g. 8"
                min="0" max="1440" step="any" required />
            </div>

            <div className="form-group">
              <label className="form-label">Historical Fake Rate (0-1)</label>
              <input type="number" name="execHistoricalFakeRate" value={form.execHistoricalFakeRate}
                onChange={handleChange} className="form-input" placeholder="e.g. 0.28"
                min="0" max="1" step="0.01" required />
            </div>

            <div className="form-group">
              <label className="form-label">Minutes to Shift End</label>
              <input type="number" name="minutesToShiftEnd" value={form.minutesToShiftEnd}
                onChange={handleChange} className="form-input" placeholder="e.g. 12"
                min="0" max="720" step="any" required />
            </div>

            <div className="form-group">
              <label className="form-label">Pincode Tier</label>
              <select name="pincodeTier" value={form.pincodeTier}
                onChange={handleChange} className="form-input form-select">
                <option value={1}>1 — Metro</option>
                <option value={2}>2 — Tier-2 City</option>
                <option value={3}>3 — Tier-3 City</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Executive ID (optional)</label>
              <input type="text" name="execId" value={form.execId}
                onChange={handleChange} className="form-input" placeholder="e.g. EXEC-042" />
            </div>
          </div>

          <div className="toggle-row">
            <label className="toggle-label">
              <input type="checkbox" name="callMade" checked={form.callMade}
                onChange={handleChange} className="toggle-input" />
              <span className="toggle-switch"></span>
              <span>Call Made to Customer</span>
            </label>

            <label className="toggle-label">
              <input type="checkbox" name="isCod" checked={form.isCod}
                onChange={handleChange} className="toggle-input" />
              <span className="toggle-switch"></span>
              <span>Cash on Delivery</span>
            </label>
          </div>

          {error && (
            <div className="submit-error">⚠️ {error}</div>
          )}

          <div className="submit-actions">
            <button type="submit" className="btn btn-primary btn-lg" disabled={submitting}>
              {submitting ? <Loader size={18} className="spin" /> : <Send size={18} />}
              {submitting ? 'Scoring...' : 'Score Attempt'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={handleReset}>Reset</button>
          </div>
        </form>

        {/* Result */}
        {result && (
          <div className="submit-result animate-slide-up">
            <div className="card" style={{ textAlign: 'center' }}>
              <h3 className="section-title">Credibility Score</h3>
              <ScoreGauge score={result.credibilityScore} size={180} />
              <button
                className="btn btn-secondary"
                style={{ marginTop: 'var(--space-lg)' }}
                onClick={() => navigate(`/attempt/${result.id}`)}
              >
                View Full Analysis →
              </button>
            </div>

            <div style={{ marginTop: 'var(--space-lg)' }}>
              <h3 className="section-title">Key Findings</h3>
              <ReasonBreakdown reasons={result.reasons} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
