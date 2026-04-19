import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import './DashboardStats.css';

export default function DashboardStats({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      label: 'Total Attempts',
      value: stats.totalAttempts.toLocaleString(),
      icon: CheckCircle,
      color: 'accent',
      sub: 'Lifetime scored',
    },
    {
      label: 'Average Score',
      value: stats.averageScore.toFixed(2),
      icon: stats.averageScore >= 0.6 ? TrendingUp : TrendingDown,
      color: stats.averageScore >= 0.6 ? 'low' : stats.averageScore >= 0.3 ? 'medium' : 'high',
      sub: stats.averageScore >= 0.6 ? 'Healthy range' : 'Needs attention',
    },
    {
      label: 'High Risk',
      value: stats.highRiskCount.toLocaleString(),
      icon: AlertTriangle,
      color: 'high',
      sub: `${stats.totalAttempts > 0 ? ((stats.highRiskCount / stats.totalAttempts) * 100).toFixed(1) : 0}% of total`,
    },
    {
      label: 'Flagged Rate',
      value: `${stats.flaggedRate.toFixed(1)}%`,
      icon: AlertTriangle,
      color: stats.flaggedRate > 40 ? 'high' : stats.flaggedRate > 20 ? 'medium' : 'low',
      sub: 'High + Medium risk',
    },
  ];

  return (
    <div className="stats-grid stagger-children">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.label} className={`stat-card card stat-card-${card.color}`}>
            <div className="stat-card-header">
              <span className="label">{card.label}</span>
              <div className={`stat-icon stat-icon-${card.color}`}>
                <Icon size={18} />
              </div>
            </div>
            <div className="stat-card-value">{card.value}</div>
            <div className="stat-card-sub">{card.sub}</div>
          </div>
        );
      })}
    </div>
  );
}
