/* ===================================================================
   VG 24H — Client-side Interactions
   =================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initCharCounters();
  initWizard();
  initSelectionCards();
  initModals();
  initTabs();
  initMobileMenu();
  initRatingStars();
  initAnimateOnScroll();
});

/* ------- Character Counter ------- */
function initCharCounters() {
  document.querySelectorAll('[data-maxlength]').forEach(textarea => {
    const max = parseInt(textarea.dataset.maxlength, 10);
    const counter = textarea.parentElement.querySelector('.char-counter');
    if (!counter) return;

    const update = () => {
      const len = textarea.value.length;
      counter.textContent = `${len}/${max} caracteres`;
      counter.classList.remove('warning', 'danger');
      if (len > max * 0.9) counter.classList.add('danger');
      else if (len > max * 0.7) counter.classList.add('warning');
    };

    textarea.addEventListener('input', update);
    update();
  });
}

/* ------- Wizard (Step Navigation) ------- */
function initWizard() {
  document.querySelectorAll('.wizard-container').forEach(wizard => {
    const steps = wizard.querySelectorAll('.wizard-step');
    const indicators = wizard.querySelectorAll('.step-indicator .step-dot');
    let current = 0;

    const show = (idx) => {
      steps.forEach((s, i) => {
        s.classList.toggle('active', i === idx);
      });
      indicators.forEach((dot, i) => {
        dot.classList.toggle('active', i <= idx);
        dot.classList.toggle('current', i === idx);
      });
      current = idx;
    };

    wizard.querySelectorAll('[data-wizard-next]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (current < steps.length - 1) show(current + 1);
      });
    });

    wizard.querySelectorAll('[data-wizard-prev]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (current > 0) show(current - 1);
      });
    });

    show(0);
  });
}

/* ------- Selection Cards (Radio-like) ------- */
function initSelectionCards() {
  document.querySelectorAll('.selection-grid').forEach(grid => {
    grid.querySelectorAll('.selection-card').forEach(card => {
      card.addEventListener('click', () => {
        grid.querySelectorAll('.selection-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        // Update hidden input if present
        const input = grid.querySelector('input[type="hidden"]');
        if (input) input.value = card.dataset.value || '';
      });
    });
  });
}

/* ------- Modals ------- */
function initModals() {
  // Open
  document.querySelectorAll('[data-modal-open]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.getElementById(trigger.dataset.modalOpen);
      if (target) target.classList.add('active');
    });
  });

  // Close
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.vg-modal-overlay').classList.remove('active');
    });
  });

  // Click overlay to close
  document.querySelectorAll('.vg-modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('active');
    });
  });
}

/* ------- Tabs ------- */
function initTabs() {
  document.querySelectorAll('[data-tab-group]').forEach(group => {
    const buttons = group.querySelectorAll('[data-tab-target]');
    const panels = group.querySelectorAll('.tab-content');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tabTarget;

        buttons.forEach(b => b.classList.remove('active', 'is-active'));
        btn.classList.add('active', 'is-active');

        panels.forEach(p => {
          p.classList.toggle('active', p.id === target);
        });
      });
    });
  });
}

/* ------- Mobile Menu ------- */
function initMobileMenu() {
  const menuTrigger = document.querySelector('.header-menu-trigger button');
  const menu = document.getElementById('main-navigation');

  if (menuTrigger && menu) {
    menuTrigger.addEventListener('click', () => {
      menu.classList.toggle('active');
    });
  }

  const closeBtn = menu?.querySelector('[data-dismiss="menu"]');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      menu.classList.remove('active');
    });
  }

  const scrim = menu?.querySelector('.menu-scrim');
  if (scrim) {
    scrim.addEventListener('click', () => {
      menu.classList.remove('active');
    });
  }
}

/* ------- Rating Stars ------- */
function initRatingStars() {
  document.querySelectorAll('.rating-stars').forEach(container => {
    const stars = container.querySelectorAll('.star');
    const input = container.querySelector('input[type="hidden"]');

    stars.forEach((star, idx) => {
      star.addEventListener('click', () => {
        const value = idx + 1;
        stars.forEach((s, i) => {
          s.classList.toggle('active', i < value);
        });
        if (input) input.value = value;
      });

      star.addEventListener('mouseenter', () => {
        stars.forEach((s, i) => {
          s.style.color = i <= idx ? 'var(--vg-warning)' : '';
        });
      });

      star.addEventListener('mouseleave', () => {
        stars.forEach(s => s.style.color = '');
      });
    });
  });
}

/* ------- Animate on Scroll ------- */
function initAnimateOnScroll() {
  const elements = document.querySelectorAll('.animate-on-scroll');
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animated');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  elements.forEach(el => observer.observe(el));
}

/* ------- Utility: Animated Counter ------- */
function animateCounter(element, target, duration = 1500) {
  let start = 0;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const value = Math.floor(progress * target);
    element.textContent = value.toLocaleString('pt-BR');
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// Auto-init counters when they scroll into view
document.querySelectorAll('[data-counter]').forEach(el => {
  const observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      animateCounter(el, parseInt(el.dataset.counter, 10));
      observer.disconnect();
    }
  }, { threshold: 0.5 });
  observer.observe(el);
});
