import { useState, useEffect } from 'react';
import { listAttempts } from '../services/api';
import AttemptTable from '../components/AttemptTable';
import { ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import './History.css';

export default function History() {
  const [attempts, setAttempts] = useState([]);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalElements, setTotalElements] = useState(0);
  const [riskFilter, setRiskFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const pageSize = 15;

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const data = await listAttempts({
          page,
          size: pageSize,
          riskLevel: riskFilter || undefined,
        });
        setAttempts(data.content || []);
        setTotalPages(data.totalPages || 0);
        setTotalElements(data.totalElements || 0);
      } catch (err) {
        console.error('Failed to load history', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [page, riskFilter]);

  const handleFilterChange = (value) => {
    setRiskFilter(value);
    setPage(0);
  };

  return (
    <div className="history-page animate-fade-in">
      <div className="history-header">
        <div>
          <h1 className="page-title">Attempt History</h1>
          <p className="page-subtitle">{totalElements} total scored attempts</p>
        </div>

        <div className="history-filters">
          <Filter size={16} style={{ color: 'var(--text-tertiary)' }} />
          <select
            value={riskFilter}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="form-input form-select"
            style={{ minWidth: 160 }}
          >
            <option value="">All Risk Levels</option>
            <option value="HIGH_RISK">High Risk</option>
            <option value="MEDIUM_RISK">Medium Risk</option>
            <option value="LOW_RISK">Low Risk</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <span>Loading attempts...</span>
        </div>
      ) : (
        <>
          <AttemptTable attempts={attempts} showTitle={false} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-ghost btn-sm"
                disabled={page === 0}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft size={16} /> Previous
              </button>

              <span className="pagination-info">
                Page {page + 1} of {totalPages}
              </span>

              <button
                className="btn btn-ghost btn-sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage(p => p + 1)}
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
