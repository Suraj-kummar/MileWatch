import { ArrowDown, ArrowUp } from 'lucide-react';
import './ReasonBreakdown.css';

export default function ReasonBreakdown({ reasons }) {
  if (!reasons || reasons.length === 0) return null;

  // Find max impact for bar width scaling
  const maxImpact = Math.max(...reasons.map(r => r.impact));

  return (
    <div className="reasons-list stagger-children">
      {reasons.map((reason, index) => {
        const isNeg = reason.direction === 'negative';
        const barWidth = maxImpact > 0 ? (reason.impact / maxImpact) * 100 : 0;

        return (
          <div key={index} className={`reason-card card ${isNeg ? 'reason-negative' : 'reason-positive'}`}>
            <div className="reason-header">
              <div className="reason-icon-wrap">
                {isNeg
                  ? <ArrowDown size={14} className="reason-icon-neg" />
                  : <ArrowUp size={14} className="reason-icon-pos" />
                }
              </div>
              <span className="reason-feature-label">{reason.feature_label}</span>
              <span className={`reason-direction ${isNeg ? 'neg' : 'pos'}`}>
                {isNeg ? 'Reduces' : 'Increases'} credibility
              </span>
            </div>

            <p className="reason-description">{reason.description}</p>

            <div className="reason-bar-container">
              <div
                className={`reason-bar ${isNeg ? 'reason-bar-neg' : 'reason-bar-pos'}`}
                style={{ width: `${barWidth}%` }}
              />
            </div>

            <div className="reason-meta">
              <span className="mono" style={{ fontSize: '0.75rem' }}>
                Impact: {reason.impact.toFixed(4)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
