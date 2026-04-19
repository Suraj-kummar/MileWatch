import { useEffect, useRef, useState } from 'react';
import './ScoreGauge.css';

export default function ScoreGauge({ score, size = 200 }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const canvasRef = useRef(null);

  const riskLevel = score < 0.3 ? 'high' : score < 0.6 ? 'medium' : 'low';
  const riskLabel = score < 0.3 ? 'High Risk' : score < 0.6 ? 'Needs Review' : 'Likely Genuine';
  const riskColors = {
    high: { main: '#ef4444', glow: 'rgba(239,68,68,0.3)' },
    medium: { main: '#f59e0b', glow: 'rgba(245,158,11,0.3)' },
    low: { main: '#22c55e', glow: 'rgba(34,197,94,0.3)' },
  };

  // Animate score counting up
  useEffect(() => {
    let start = 0;
    const duration = 1200;
    const startTime = performance.now();

    function animate(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(score * eased);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    }

    requestAnimationFrame(animate);
  }, [score]);

  // Draw the gauge
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 16;
    const lineWidth = 10;
    const startAngle = 0.75 * Math.PI;
    const endAngle = 2.25 * Math.PI;
    const totalAngle = endAngle - startAngle;

    ctx.clearRect(0, 0, size, size);

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.lineWidth = lineWidth;
    ctx.strokeStyle = 'hsla(215, 15%, 25%, 0.4)';
    ctx.lineCap = 'round';
    ctx.stroke();

    // Score arc
    const scoreAngle = startAngle + totalAngle * animatedScore;
    if (animatedScore > 0.001) {
      const color = riskColors[riskLevel];

      // Glow effect
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, scoreAngle);
      ctx.lineWidth = lineWidth + 6;
      ctx.strokeStyle = color.glow;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Main arc
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, scoreAngle);
      ctx.lineWidth = lineWidth;
      ctx.strokeStyle = color.main;
      ctx.lineCap = 'round';
      ctx.stroke();
    }
  }, [animatedScore, size, riskLevel]);

  return (
    <div className="score-gauge animate-scale-in" style={{ width: size, height: size }}>
      <canvas
        ref={canvasRef}
        style={{ width: size, height: size }}
        className="score-gauge-canvas"
      />
      <div className="score-gauge-center">
        <div className="score-gauge-value" style={{ color: riskColors[riskLevel].main }}>
          {(animatedScore * 100).toFixed(0)}
        </div>
        <div className="score-gauge-label">/ 100</div>
        <div className={`risk-badge risk-badge-${riskLevel}`} style={{ marginTop: 8 }}>
          <span className={`risk-dot risk-dot-${riskLevel}`}></span>
          {riskLabel}
        </div>
      </div>
    </div>
  );
}
