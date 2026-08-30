/* =========================================================
   api.js — RailMadat API Client

   Fetch wrappers for all backend endpoints.
   Handles auth tokens, error responses, and 401 redirects.
   Auto-detects localhost vs production deployment.
   ========================================================= */

// Auto-detect: localhost uses local backend, deployed uses production URL
const _isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_BASE = _isLocal
    ? 'http://localhost:8000/api'
    : 'https://rail-madat-backend.onrender.com/api';

async function apiRequest(path, { method = 'GET', body, query } = {}) {
    const token = AUTH.getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    let url = API_BASE + path;
    if (query) {
        const params = new URLSearchParams();
        Object.entries(query).forEach(([k, v]) => {
            if (v !== undefined && v !== null && v !== '') params.set(k, v);
        });
        const qs = params.toString();
        if (qs) url += '?' + qs;
    }

    try {
        const res = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined,
        });

        if (res.status === 401) {
            AUTH.clearSession();
            window.location.href = '/login.html';
            return null;
        }

        if (res.status === 204) return null;

        const data = await res.json().catch(() => null);

        if (!res.ok) {
            throw new Error(data?.detail || data?.message || 'Request failed (' + res.status + ')');
        }

        return data;
    } catch (err) {
        if (err.message === 'Failed to fetch') {
            throw new Error('Could not reach the server. Check your connection.');
        }
        throw err;
    }
}
