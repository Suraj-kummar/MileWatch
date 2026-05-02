import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import AttemptDetail from './pages/AttemptDetail';
import SubmitAttempt from './pages/SubmitAttempt';
import History from './pages/History';

export default function App() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem('milewatch-theme') || 'dark'
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('milewatch-theme', theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar theme={theme} onToggleTheme={toggleTheme} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/attempt/:id" element={<AttemptDetail />} />
            <Route path="/submit" element={<SubmitAttempt />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
