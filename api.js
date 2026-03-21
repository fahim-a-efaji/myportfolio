/* ============================================================
   api.js — Shared Azure Cosmos DB API client
   Used by all 5 project HTML pages
   ============================================================
   Set window.PORTFOLIO_API_BASE before loading this script,
   OR edit API_BASE directly below.

   Example (in your HTML <head>):
     <script>window.PORTFOLIO_API_BASE = 'https://portfolio-fn.azurewebsites.net/api';</script>
     <script src="../js/api.js"></script>
   ============================================================ */

const API_BASE = window.PORTFOLIO_API_BASE || '';

// Each browser tab gets a stable anonymous user ID (sessionStorage so it resets per tab)
const USER_ID = (() => {
  let id = sessionStorage.getItem('portfolio_user_id');
  if (!id) {
    id = 'user_' + Math.random().toString(36).slice(2, 10);
    sessionStorage.setItem('portfolio_user_id', id);
  }
  return id;
})();

const SESSION_ID = (() => {
  let id = sessionStorage.getItem('portfolio_session_id');
  if (!id) {
    id = 'sess_' + Math.random().toString(36).slice(2, 14);
    sessionStorage.setItem('portfolio_session_id', id);
  }
  return id;
})();

/** Base fetch wrapper — always sends user/session headers */
async function apiFetch(path, options = {}) {
  if (!API_BASE) throw new Error('API_BASE not configured. Edit js/api.js or set window.PORTFOLIO_API_BASE.');
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id':    USER_ID,
      'X-Session-Id': SESSION_ID,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = j.error || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

/* ──────────────────────────────────────────────
   FINANCE TRACKER API  →  Cosmos: finance_tx
   ────────────────────────────────────────────── */
const FinanceAPI = {
  list:   ()     => apiFetch('/finance'),
  add:    (tx)   => apiFetch('/finance', { method: 'POST', body: JSON.stringify(tx) }),
  delete: (id)   => apiFetch(`/finance/${id}`, { method: 'DELETE' }),
  seed:   ()     => apiFetch('/finance/seed', { method: 'POST', body: '{}' }),
};

/* ──────────────────────────────────────────────
   SQL PLAYGROUND API  →  Cosmos: sql_queries
   ────────────────────────────────────────────── */
const SqlAPI = {
  list:   ()     => apiFetch('/sql/queries'),
  save:   (q)    => apiFetch('/sql/queries', { method: 'POST', body: JSON.stringify(q) }),
  delete: (id)   => apiFetch(`/sql/queries/${id}`, { method: 'DELETE' }),
};

/* ──────────────────────────────────────────────
   CSV ANALYZER API  →  Cosmos: csv_uploads
   ────────────────────────────────────────────── */
const CsvAPI = {
  list:   ()     => apiFetch('/csv'),
  save:   (meta) => apiFetch('/csv', { method: 'POST', body: JSON.stringify(meta) }),
};

/* ──────────────────────────────────────────────
   AI CHAT API  →  Cosmos: chat_history
   ────────────────────────────────────────────── */
const ChatAPI = {
  history: ()        => apiFetch(`/chat?session=${SESSION_ID}`),
  append:  (role, content) => apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ role, content }),
  }),
  clear:   ()        => apiFetch(`/chat/${SESSION_ID}`, { method: 'DELETE' }),
};

/* ──────────────────────────────────────────────
   CONTACT API  →  Cosmos: contacts
   ────────────────────────────────────────────── */
const ContactAPI = {
  send: (data) => apiFetch('/contact', { method: 'POST', body: JSON.stringify(data) }),
};
