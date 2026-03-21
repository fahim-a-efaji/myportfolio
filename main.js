/* ============================================================
   FAHIM AL EFAJI — Portfolio JavaScript
   All data → Azure Cosmos DB via Azure Functions
   ============================================================ */

// ─────────────────────────────────────────────────────────────
// CONFIGURE THIS: your Azure Function App base URL
// e.g. 'https://portfolio-fn.azurewebsites.net/api'
// ─────────────────────────────────────────────────────────────
const API_BASE = window.PORTFOLIO_API_BASE || '';

// ── Navbar scroll effect ──
const navbar = document.getElementById('navbar');
const navLinks = document.querySelectorAll('.nav-links a');

window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 40);
  highlightNav();
});

function highlightNav() {
  const sections = document.querySelectorAll('section[id]');
  let current = '';
  sections.forEach(s => {
    if (window.scrollY >= s.offsetTop - 120) current = s.id;
  });
  navLinks.forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${current}`);
  });
}

// ── Fade-in on scroll ──
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('visible'), i * 80);
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));

// ── Project Demo Modal ──
const modal = document.getElementById('demo-modal');
const demoFrame = document.getElementById('demo-frame');
const modalTitle = document.getElementById('modal-title');

function openDemo(url, title) {
  demoFrame.src = url;
  modalTitle.textContent = title;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeDemo() {
  modal.classList.remove('open');
  demoFrame.src = '';
  document.body.style.overflow = '';
}

document.getElementById('modal-close').addEventListener('click', closeDemo);
modal.addEventListener('click', (e) => { if (e.target === modal) closeDemo(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDemo(); });

// ─────────────────────────────────────────────────────────────
// CONTACT FORM  →  POST /api/contact  →  Cosmos DB: contacts
// ─────────────────────────────────────────────────────────────
const contactForm = document.getElementById('contact-form');
const formStatus  = document.getElementById('form-status');

if (contactForm) {
  contactForm.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = contactForm.querySelector('button[type="submit"]');
    const data = {
      name:    contactForm.name.value.trim(),
      email:   contactForm.email.value.trim(),
      subject: contactForm.subject.value.trim(),
      message: contactForm.message.value.trim(),
    };
    btn.textContent = 'Sending…';
    btn.disabled = true;
    formStatus.className = 'form-status';

    try {
      if (!API_BASE) throw new Error('API_BASE not configured');
      const res = await fetch(`${API_BASE}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Server error');
      showStatus('✓ Message saved to Azure Cosmos DB! I\'ll get back to you soon.', 'success');
      contactForm.reset();
    } catch (err) {
      console.error(err);
      showStatus(API_BASE
        ? 'Something went wrong. Please email directly.'
        : 'Deploy the Azure Function and set API_BASE in js/main.js', 'error');
    } finally {
      btn.textContent = 'Send Message';
      btn.disabled = false;
    }
  });
}

function showStatus(msg, type) {
  formStatus.textContent = msg;
  formStatus.className   = `form-status ${type}`;
}

// ── Typed hero subtitle ──
const roles = ['Analytics Engineer', 'Data Pipeline Builder', 'AI Integration Dev', 'Power BI Expert'];
let ri = 0, ci = 0, deleting = false;
const typedEl = document.getElementById('typed-role');

function typeLoop() {
  if (!typedEl) return;
  const word = roles[ri];
  if (!deleting) {
    typedEl.textContent = word.slice(0, ++ci);
    if (ci === word.length) { deleting = true; setTimeout(typeLoop, 1800); return; }
  } else {
    typedEl.textContent = word.slice(0, --ci);
    if (ci === 0) { deleting = false; ri = (ri + 1) % roles.length; }
  }
  setTimeout(typeLoop, deleting ? 55 : 95);
}
typeLoop();

// ── Smooth scroll for anchor buttons ──
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});
