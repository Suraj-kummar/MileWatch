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
          {/* 3D perspective wrapper for the shield */}
          <div className="logo-3d-wrap">
            <Shield size={26} className="navbar-logo" />
          </div>
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
              {/* 3D perspective wrapper for each nav icon */}
              <span className="icon-3d-wrap">
                <Icon size={16} className="nav-icon-3d" />
              </span>
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
            <span className="icon-3d-wrap toggle-icon-wrap">
              {theme === 'dark' ? <Sun size={18} className="nav-icon-3d" /> : <Moon size={18} className="nav-icon-3d" />}
            </span>
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
