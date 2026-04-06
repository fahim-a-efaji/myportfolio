/* ============================================================
   main.js — Fahim Al Efaji Portfolio
   Fixes applied:
     1. openDemo() is a plain global function (was missing/broken)
     2. IntersectionObserver wires up .fade-up visibility
     3. Navbar scroll shrink effect
     4. Typed role animation
     5. Modal close logic (button + backdrop click + Escape key)
     6. Contact form — saves to IndexedDB locally, shows status
   ============================================================ */

const API_BASE = window.PORTFOLIO_API_BASE || '';

/* ── 1. Scroll-triggered fade-up animations ─────────────────
   FIX: Without this observer, every .fade-up element stays at
   opacity:0 forever — causing "nothing showing" bug.           */
(function initFadeUp() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
})();

/* ── 2. Navbar shrink on scroll ─────────────────────────────*/
window.addEventListener('scroll', () => {
  const nav = document.getElementById('navbar');
  if (!nav) return;
  nav.classList.toggle('scrolled', window.scrollY > 60);
});

/* ── 3. Typed role animation ─────────────────────────────── */
(function initTyped() {
  const el = document.getElementById('typed-role');
  if (!el) return;
  const roles = [
    'Analytics Engineer',
    'Data Pipeline Builder',
    'Azure & AI Specialist',
    'Power BI Developer',
    'ETL Architect',
  ];
  let ri = 0, ci = 0, deleting = false;

  function tick() {
    const word = roles[ri];
    el.textContent = deleting ? word.slice(0, ci--) : word.slice(0, ++ci);

    if (!deleting && ci === word.length) {
      setTimeout(() => { deleting = true; tick(); }, 1800);
      return;
    }
    if (deleting && ci === 0) {
      deleting = false;
      ri = (ri + 1) % roles.length;
    }
    setTimeout(tick, deleting ? 50 : 90);
  }
  setTimeout(tick, 600);
})();

/* ── 4. Project Demo Modal ───────────────────────────────────
   FIX: openDemo must be a plain global function so onclick=""
   attributes in HTML can call it. Module-scoped functions don't
   work in onclick handlers.                                    */
function openDemo(url, title) {
  const modal   = document.getElementById('demo-modal');
  const iframe  = document.getElementById('demo-iframe');
  const titleEl = document.getElementById('modal-title');
  const newtab  = document.getElementById('modal-newtab');
  if (!modal || !iframe) return;

  iframe.src          = url;
  titleEl.textContent = title || 'Project Demo';
  newtab.href         = url;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeDemo() {
  const modal  = document.getElementById('demo-modal');
  const iframe = document.getElementById('demo-iframe');
  if (!modal) return;
  modal.style.display = 'none';
  if (iframe) iframe.src = '';
  document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', () => {
  const modal     = document.getElementById('demo-modal');
  const closeBtn  = document.getElementById('modal-close');

  if (closeBtn) closeBtn.addEventListener('click', closeDemo);

  // Click outside the modal box closes it
  if (modal) {
    modal.addEventListener('click', e => {
      if (e.target === modal) closeDemo();
    });
  }
});

// Escape key closes modal
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDemo();
});

/* ── 5. Contact form ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const form   = document.getElementById('contact-form');
  const status = document.getElementById('form-status');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      name:    form.name.value.trim(),
      email:   form.email.value.trim(),
      subject: form.subject.value.trim(),
      message: form.message.value.trim(),
      ts:      new Date().toISOString(),
    };

    setStatus('Sending…', '');

    // Try Azure Function first; fall back to IndexedDB local save
    if (API_BASE) {
      try {
        const res = await fetch(`${API_BASE}/contact`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setStatus('✅ Message sent! I\'ll get back to you soon.', 'ok');
        form.reset();
        return;
      } catch (err) {
        console.warn('Azure Function unavailable, saving locally:', err);
      }
    }

    // Local IndexedDB fallback
    saveLocal(data)
      .then(() => {
        setStatus('✅ Message saved locally. (Azure Function not connected yet)', 'ok');
        form.reset();
      })
      .catch(() => setStatus('❌ Something went wrong. Please email me directly.', 'err'));
  });

  function setStatus(msg, cls) {
    if (!status) return;
    status.textContent  = msg;
    status.className    = 'form-status' + (cls ? ` form-status--${cls}` : '');
    status.style.display = msg ? 'block' : 'none';
  }
});

function saveLocal(data) {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('portfolio_contacts', 1);
    req.onupgradeneeded = e => e.target.result.createObjectStore('messages', { autoIncrement: true });
    req.onsuccess = e => {
      const db  = e.target.result;
      const tx  = db.transaction('messages', 'readwrite');
      tx.objectStore('messages').add(data);
      tx.oncomplete = resolve;
      tx.onerror    = reject;
    };
    req.onerror = reject;
  });
}

/* ── 6. Smooth scroll for nav links ─────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth' });
  });
});