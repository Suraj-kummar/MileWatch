import axios from 'axios';

const API_BASE = 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Attempts ──────────────────────────────────────────────────────────

export async function submitAttempt(data) {
  const res = await api.post('/attempts', data);
  return res.data;
}

export async function getAttempt(id) {
  const res = await api.get(`/attempts/${id}`);
  return res.data;
}

export async function listAttempts({ page = 0, size = 20, sortBy = 'createdAt', direction = 'desc', riskLevel } = {}) {
  const params = { page, size, sortBy, direction };
  if (riskLevel) params.riskLevel = riskLevel;
  const res = await api.get('/attempts', { params });
  return res.data;
}

export async function getRecentAttempts() {
  const res = await api.get('/attempts/recent');
  return res.data;
}

export async function getDisputeDraft(id) {
  const res = await api.get(`/attempts/${id}/dispute`);
  return res.data;
}

// ── Dashboard ─────────────────────────────────────────────────────────

export async function getDashboardStats() {
  const res = await api.get('/dashboard/stats');
  return res.data;
}

export async function checkHealth() {
  const res = await api.get('/dashboard/health');
  return res.data;
}

export default api;
