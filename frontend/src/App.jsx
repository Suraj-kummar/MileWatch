import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import AttemptDetail from './pages/AttemptDetail';
import SubmitAttempt from './pages/SubmitAttempt';
import History from './pages/History';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar />
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
