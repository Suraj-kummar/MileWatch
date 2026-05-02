import { Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, History, PlusCircle, Sun, Moon } from 'lucide-react';
import './Navbar.css';

export default function Navbar({ theme, onToggleTheme }) {
  const location = useLocation();

  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/submit', label: 'Score Attempt', icon: PlusCircle },
    { to: '/history', label: 'History', icon: History },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <Shield size={24} className="navbar-logo" />
          <span className="navbar-title">MileWatch</span>
          <span className="navbar-tag">AI</span>
        </Link>

        <div className="navbar-links">
          {links.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`navbar-link ${location.pathname === to ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{label}</span>
            </Link>
          ))}
        </div>

        <div className="navbar-right">
          <button
            id="theme-toggle"
            className="theme-toggle-btn"
            onClick={onToggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            <span className="theme-toggle-label">
              {theme === 'dark' ? 'Light' : 'Dark'}
            </span>
          </button>

          <div className="navbar-status">
            <span className="status-dot"></span>
            <span className="status-text">System Online</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
