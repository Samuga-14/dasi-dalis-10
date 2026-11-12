/**
 * FE service boundary. Components call these domain methods instead of
 * constructing endpoint URLs throughout the dashboard.
 */
const TobaKostApi = {
  capabilities() {
    return fetch('/api/capabilities');
  },

  analytics() {
    return fetch('/api/data');
  },

  predict(payload) {
    return fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },

  warehouse(table) {
    return fetch(`/api/warehouse?table=${encodeURIComponent(table)}`);
  },

  createKos(payload) {
    return fetch('/api/kos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }
};
