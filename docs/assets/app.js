(function() {
  'use strict';

  const STORAGE_KEY = 'vg24h_v2';
  let data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{"checks":{},"theme":"light"}');
  if (!data.checks) data.checks = {};

  function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); }

  /* ========== NAVIGATION ========== */
  const sections = document.querySelectorAll('.content-section');
  const navLinks = document.querySelectorAll('.nav-link[data-section]');

  function showSection(targetId) {
    sections.forEach(sec => {
      sec.classList.toggle('active', sec.id === targetId);
      if (sec.id === targetId) {
        sec.style.animation = 'none';
        requestAnimationFrame(() => { sec.style.animation = ''; });
      }
    });
    navLinks.forEach(lnk => {
      lnk.classList.toggle('active', lnk.dataset.section === targetId.replace('sec-', ''));
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.querySelector('.sidebar')?.classList.remove('open');
    document.querySelector('.sidebar-overlay')?.classList.remove('active');
  }

  navLinks.forEach(lnk => {
    lnk.addEventListener('click', (e) => {
      e.preventDefault();
      const target = 'sec-' + lnk.dataset.section;
      showSection(target);
      history.pushState(null, '', '#' + lnk.dataset.section);
    });
  });

  function handleHash() {
    const hash = location.hash.replace('#', '');
    if (hash) {
      const target = 'sec-' + hash;
      if (document.getElementById(target)) showSection(target);
    } else {
      showSection('sec-visao');
    }
  }
  handleHash();
  window.addEventListener('popstate', handleHash);

  /* ========== MOBILE MENU ========== */
  const mobileBtn = document.querySelector('.mobile-menu-btn');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  if (mobileBtn) {
    mobileBtn.addEventListener('click', () => {
      sidebar?.classList.toggle('open');
      overlay?.classList.toggle('active');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar?.classList.remove('open');
      overlay?.classList.remove('active');
    });
  }

  /* ========== THEME ========== */
  const themeBtn = document.querySelector('.theme-toggle');
  function applyTheme() {
    const t = data.theme || 'light';
    document.documentElement.setAttribute('data-theme', t);
    if (themeBtn) themeBtn.textContent = t === 'dark' ? '\u2600' : '\u{1F319}';
    const hljsLight = document.getElementById('hljs-light');
    const hljsDark = document.getElementById('hljs-dark');
    if (hljsLight && hljsDark) {
      hljsLight.disabled = t === 'dark';
      hljsDark.disabled = t !== 'dark';
    }
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      data.theme = (data.theme === 'dark') ? 'light' : 'dark';
      save(); applyTheme();
    });
  }
  applyTheme();

  /* ========== ACCORDION ========== */
  document.querySelectorAll('.accordion-header').forEach(hdr => {
    hdr.addEventListener('click', () => {
      const item = hdr.closest('.accordion-item');
      const wasOpen = item.classList.contains('open');
      const group = item.closest('.accordion-group');
      if (group) group.querySelectorAll('.accordion-item.open').forEach(c => c.classList.remove('open'));
      if (!wasOpen) item.classList.add('open');
    });
  });

  /* ========== CARD ACCORDION ========== */
  document.querySelectorAll('.card-header').forEach(hdr => {
    hdr.addEventListener('click', () => {
      const card = hdr.closest('.card');
      const wasOpen = card.classList.contains('open');
      const group = card.closest('.accordion-group');
      if (group) group.querySelectorAll('.card.open').forEach(c => c.classList.remove('open'));
      if (!wasOpen) card.classList.add('open');
    });
  });

  /* ========== FLASHCARDS INLINE ========== */
  document.querySelectorAll('.flashcard').forEach(fc => {
    fc.addEventListener('click', () => fc.classList.toggle('flipped'));
  });

  /* ========== FLASHCARD MODAL ========== */
  const modalOverlay = document.getElementById('modal-overlay');
  const modalClose = document.getElementById('modal-close');
  const flashcardModal = document.getElementById('flashcard-modal');
  const fcFront = document.getElementById('flashcard-front');
  const fcBack = document.getElementById('flashcard-back');
  const fcFlipBtn = document.getElementById('flashcard-flip');

  function closeModal() { modalOverlay?.classList.remove('active'); }
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (modalOverlay) modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });
  if (fcFlipBtn) fcFlipBtn.addEventListener('click', () => flashcardModal?.classList.toggle('flipped'));

  /* ========== CHECKLIST ========== */
  function initChecklist(container, groupKey) {
    const items = container.querySelectorAll('li[data-key]');
    items.forEach(li => {
      const key = li.dataset.key;
      const box = document.createElement('span');
      box.className = 'chk-box';
      const checked = !!(data.checks[groupKey] && data.checks[groupKey][key]);
      if (checked) { li.classList.add('done'); box.innerHTML = '\u2713'; }
      li.insertBefore(box, li.firstChild);
      li.addEventListener('click', () => {
        const isDone = li.classList.toggle('done');
        box.innerHTML = isDone ? '\u2713' : '';
        if (!data.checks[groupKey]) data.checks[groupKey] = {};
        data.checks[groupKey][key] = isDone;
        save();
        updateProgress(container, groupKey);
        updateGlobalProgress();
      });
    });
    updateProgress(container, groupKey);
  }

  function updateProgress(container, groupKey) {
    const wrap = container.closest('.checklist-wrap');
    const bar = wrap?.querySelector('.progress-fill');
    const txt = wrap?.querySelector('.progress-text');
    const items = container.querySelectorAll('li[data-key]');
    const done = Array.from(items).filter(li => li.classList.contains('done')).length;
    const pct = items.length ? Math.round((done / items.length) * 100) : 0;
    if (bar) bar.style.width = pct + '%';
    if (txt) txt.textContent = `${done}/${items.length} conclu\xeddos (${pct}%)`;
    updateRingProgress();
  }

  function updateRingProgress() {
    const ring = document.getElementById('global-progress');
    const ringText = document.getElementById('global-progress-text');
    if (!ring) return;
    let total = 0, done = 0;
    document.querySelectorAll('[data-checklist-group] li[data-key]').forEach(li => {
      total++;
      if (li.classList.contains('done')) done++;
    });
    const pct = total ? Math.round((done / total) * 100) : 0;
    const circumference = 2 * Math.PI * 15.9155;
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = circumference - (pct / 100) * circumference;
    if (ringText) ringText.textContent = pct + '%';
  }

  function updateGlobalProgress() {
    let total = 0, done = 0;
    document.querySelectorAll('[data-checklist-group] li[data-key]').forEach(li => {
      total++;
      if (li.classList.contains('done')) done++;
    });
    const pct = total ? Math.round((done / total) * 100) : 0;
    document.querySelectorAll('.global-progress-fill').forEach(b => b.style.width = pct + '%');
    document.querySelectorAll('.global-progress-text').forEach(t => t.textContent = `${done}/${total} itens (${pct}%)`);
    updateIndividualProgress();
  }

  function updateIndividualProgress() {
    const groups = {
      bruno: {bar:'prog-bruno',txt:'txt-bruno'},
      fausto: {bar:'prog-fausto',txt:'txt-fausto'},
      rafael: {bar:'prog-rafael',txt:'txt-rafael'}
    };
    for (const [gkey, ids] of Object.entries(groups)) {
      const container = document.querySelector(`[data-checklist-group="${gkey}"]`);
      if (!container) continue;
      const items = container.querySelectorAll('li[data-key]');
      const done = Array.from(items).filter(li => li.classList.contains('done')).length;
      const pct = items.length ? Math.round((done / items.length) * 100) : 0;
      const bar = document.getElementById(ids.bar);
      const txt = document.getElementById(ids.txt);
      if (bar) bar.style.width = pct + '%';
      if (txt) txt.textContent = `${done}/${items.length} (${pct}%)`;
    }
  }

  document.querySelectorAll('[data-checklist-group]').forEach(el => {
    initChecklist(el, el.dataset.checklistGroup);
  });
  updateGlobalProgress();

  /* ========== FAQ ========== */
  const faqSearch = document.getElementById('faq-filter');
  const faqItems = document.querySelectorAll('.faq-item');
  if (faqSearch) {
    faqSearch.addEventListener('input', () => {
      const q = faqSearch.value.toLowerCase();
      faqItems.forEach(item => {
        const text = (item.querySelector('.faq-question')?.textContent || '').toLowerCase();
        const ans = (item.querySelector('.faq-answer')?.textContent || '').toLowerCase();
        const show = text.includes(q) || ans.includes(q);
        item.style.display = show ? 'block' : 'none';
      });
    });
  }
  document.querySelectorAll('.faq-question').forEach(q => {
    q.addEventListener('click', () => {
      const item = q.closest('.faq-item');
      const wasOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
      if (!wasOpen) item.classList.add('open');
    });
  });

  /* ========== COPY TO CLIPBOARD ========== */
  const toast = document.getElementById('toast');
  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
  }

  document.querySelectorAll('.btn-copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const code = btn.closest('.code-block')?.querySelector('code')?.textContent || '';
      navigator.clipboard.writeText(code).then(() => showToast('\u{1F4CB} C\xf3digo copiado!'));
    });
  });
  document.querySelectorAll('pre').forEach(pre => {
    if (pre.querySelector('.copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn'; btn.textContent = 'Copiar';
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code')?.textContent || pre.textContent;
      navigator.clipboard.writeText(code).then(() => {
        btn.textContent = 'Copiado!';
        setTimeout(() => btn.textContent = 'Copiar', 1500);
        showToast('\u{1F4CB} C\xf3digo copiado!');
      });
    });
    pre.appendChild(btn);
  });

  /* ========== SEMAFORO ========== */
  const semSlider = document.getElementById('semaforo-slider');
  const semDias = document.getElementById('semaforo-dias');
  const semLabel = document.getElementById('semaforo-label');
  const luzVerde = document.getElementById('luz-verde');
  const luzAmarelo = document.getElementById('luz-amarelo');
  const luzVermelho = document.getElementById('luz-vermelho');
  const AM = 15, VM = 30;

  function updateSemaforo() {
    const d = parseInt(semSlider?.value || 0);
    if (semDias) semDias.textContent = d;
    if (luzVerde) luzVerde.classList.toggle('on', d < AM);
    if (luzAmarelo) luzAmarelo.classList.toggle('on', d >= AM && d < VM);
    if (luzVermelho) luzVermelho.classList.toggle('on', d >= VM);
    if (semLabel) {
      if (d < AM) semLabel.textContent = 'No prazo (Verde)';
      else if (d < VM) semLabel.textContent = 'Aten\xe7\xe3o (Amarelo)';
      else semLabel.textContent = 'Cr\xedtico (Vermelho)';
    }
  }
  if (semSlider) {
    semSlider.addEventListener('input', updateSemaforo);
    updateSemaforo();
  }

  /* ========== SCROLL REVEAL ========== */
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  /* ========== HIGHLIGHT JS ========== */
  if (window.hljs) {
    document.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }

})();
