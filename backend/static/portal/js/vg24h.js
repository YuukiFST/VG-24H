/* ===================================================================
   vg24h.js — Interacoes client-side do Portal VG 24H
   ===================================================================
   [!] Inicializa 8 funcionalidades ao carregar a pagina:
       - initCharCounters    — Contador de caracteres (textarea)
       - initWizard          — Wizard 3 etapas do cadastro
       - initSelectionCards  — Cards selecionaveis (categorias/servicos)
       - initModals          - Modais de confirmacao
       - initTabs            — Abas de navegacao
       - initMobileMenu      — Menu responsivo (mobile)
       - initRatingStars     — Estrelas de avaliacao (click)
       - initAnimateOnScroll — Animacao ao rolar a pagina
   =================================================================== */

// rodo a maioria dos init no DOMContentLoaded pra nao esperar imagem/css carregar
document.addEventListener('DOMContentLoaded', () => {
  initCharCounters();
  initWizard();
  initSelectionCards();
  initModals();
  initTabs();

  initRatingStars();
  initAnimateOnScroll();
});

// deixo o toggle de senha pro 'load' porque ele troca o botao por um clone (replaceChild);
// se eu rodasse antes, podia disputar com o JS do GOV.br que tambem mexe nesse botao
window.addEventListener('load', () => {
  initPasswordToggles();
});

/* ------- Character Counter ------- */
// mostro "X/MAX caracteres" embaixo de cada textarea que tem data-maxlength.
// uso o data-maxlength como fonte do limite pra nao chumbar numero aqui no JS
function initCharCounters() {
  document.querySelectorAll('[data-maxlength]').forEach(textarea => {
    const max = parseInt(textarea.dataset.maxlength, 10);
    // o contador tem que estar dentro do mesmo pai do textarea; se nao achar, pulo
    const counter = textarea.parentElement.querySelector('.char-counter');
    if (!counter) return;

    const update = () => {
      const len = textarea.value.length;
      counter.textContent = `${len}/${max} caracteres`;
      // troco a cor por faixa: amarelo (warning) a partir de 70%, vermelho (danger) a partir de 90%
      counter.classList.remove('warning', 'danger');
      if (len > max * 0.9) counter.classList.add('danger');
      else if (len > max * 0.7) counter.classList.add('warning');
    };

    textarea.addEventListener('input', update);
    update(); // rodo uma vez na carga pra ja mostrar a contagem do que veio preenchido
  });
}

/* ------- Wizard (Step Navigation) ------- */
// controlo o wizard de etapas (ex: 3 passos do cadastro) so trocando classe 'active',
// sem recarregar pagina. guardo o passo atual em 'current' por wizard
function initWizard() {
  document.querySelectorAll('.wizard-container').forEach(wizard => {
    const steps = wizard.querySelectorAll('.wizard-step');
    const indicators = wizard.querySelectorAll('.step-indicator .step-dot');
    let current = 0;

    // mostro so o passo idx e atualizo as bolinhas: 'active' em tudo que ja passou (<=),
    // 'current' so na bolinha do passo atual
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

    // botao "proximo": so avanca se nao estiver no ultimo passo (trava no fim)
    wizard.querySelectorAll('[data-wizard-next]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (current < steps.length - 1) show(current + 1);
      });
    });

    // botao "voltar": so volta se nao estiver no primeiro passo (trava no inicio)
    wizard.querySelectorAll('[data-wizard-prev]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (current > 0) show(current - 1);
      });
    });

    show(0); // sempre comeco no passo 0
  });
}

/* ------- Selection Cards (Radio-like) ------- */
// faco os cards (categoria/servico) se comportarem feito radio: clicar num seleciona
// e desmarca os outros do mesmo grid. uso card no lugar de <input radio> pra ter UI bonita
function initSelectionCards() {
  document.querySelectorAll('.selection-grid').forEach(grid => {
    grid.querySelectorAll('.selection-card').forEach(card => {
      card.addEventListener('click', () => {
        // limpo a selecao de todos antes de marcar o clicado (garante so um selecionado)
        grid.querySelectorAll('.selection-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        // jogo o valor do card no input hidden do grid pra ir junto no submit do form
        const input = grid.querySelector('input[type="hidden"]');
        if (input) input.value = card.dataset.value || '';
      });
    });
  });
}

/* ------- Modals ------- */
// trato dois tipos de modal: o meu (.vg-modal-overlay com data-modal-*) e o do GOV.br
// (.br-scrim com data-toggle/data-dismiss). abrir/fechar e so ligar/desligar a classe 'active'
function initModals() {
  // abrir modal meu: o data-modal-open guarda o id do alvo
  document.querySelectorAll('[data-modal-open]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault(); // seguro o default caso o trigger seja um <a href>
      const target = document.getElementById(trigger.dataset.modalOpen);
      if (target) target.classList.add('active');
    });
  });

  // fechar modal meu pelo botao X/cancelar: subo ate o overlay mais proximo e desligo
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.vg-modal-overlay').classList.remove('active');
    });
  });

  // fechar clicando no fundo escuro: so fecho se o clique foi no proprio overlay,
  // nao se foi num filho (evita fechar quando clico dentro da caixa do modal)
  document.querySelectorAll('.vg-modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('active');
    });
  });

  // modal do GOV.br: data-toggle="modal" aponta pro alvo via data-target; acho o .br-scrim em volta e abro
  document.querySelectorAll('[data-toggle="modal"]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const targetId = trigger.getAttribute('data-target');
      if (!targetId) return;
      const modal = document.querySelector(targetId);
      if (!modal) return;
      const scrim = modal.closest('.br-scrim');
      if (scrim) scrim.classList.add('active');
    });
  });

  // modal do GOV.br: data-dismiss="modal" fecha subindo ate o .br-scrim do botao
  document.querySelectorAll('[data-dismiss="modal"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const scrim = btn.closest('.br-scrim');
      if (scrim) scrim.classList.remove('active');
    });
  });
}

/* ------- Tabs ------- */
// abas: cada botao tem data-tab-target com o id do painel que ele abre.
// clicar troca o botao ativo e mostra so o painel correspondente
function initTabs() {
  document.querySelectorAll('[data-tab-group]').forEach(group => {
    const buttons = group.querySelectorAll('[data-tab-target]');
    const panels = group.querySelectorAll('.tab-content');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tabTarget;

        // tiro 'active'/'is-active' de todos os botoes e marco so o clicado.
        // ponho as duas classes pra cobrir tanto meu CSS quanto o do GOV.br
        buttons.forEach(b => b.classList.remove('active', 'is-active'));
        btn.classList.add('active', 'is-active');

        // mostro o painel cujo id bate com o target e escondo o resto
        panels.forEach(p => {
          p.classList.toggle('active', p.id === target);
        });
      });
    });
  });
}

/* ------- Mobile Menu ------- */
/* [!] Removido: initMobileMenu() conflitava com core.BRMenu (base.html).
   O BRMenu ja gerencia toggle, close e scrim do menu lateral. */

/* ------- Rating Stars ------- */
// estrelas de avaliacao: clicar na estrela idx grava nota idx+1 no input hidden.
// hover so pinta de previa, o valor real so muda no clique
function initRatingStars() {
  document.querySelectorAll('.rating-stars').forEach(container => {
    const stars = container.querySelectorAll('.star');
    const input = container.querySelector('input[type="hidden"]');

    stars.forEach((star, idx) => {
      // clique fixa a nota: acendo da primeira ate a clicada e salvo o numero no input
      star.addEventListener('click', () => {
        const value = idx + 1; // idx e base 0, nota e base 1
        stars.forEach((s, i) => {
          s.classList.toggle('active', i < value);
        });
        if (input) input.value = value;
      });

      // hover: pinto da primeira ate a estrela embaixo do mouse so como previa visual
      star.addEventListener('mouseenter', () => {
        stars.forEach((s, i) => {
          s.style.color = i <= idx ? 'var(--vg-warning)' : '';
        });
      });

      // tirou o mouse: limpo a cor inline da previa e deixo o CSS (.active) mandar de novo
      star.addEventListener('mouseleave', () => {
        stars.forEach(s => s.style.color = '');
      });
    });
  });
}

/* ------- Animate on Scroll ------- */
// adiciono a classe 'animated' quando o elemento entra na tela, pra disparar a animacao via CSS.
// uso IntersectionObserver no lugar de evento de scroll porque e mais leve (nao roda a cada pixel)
function initAnimateOnScroll() {
  const elements = document.querySelectorAll('.animate-on-scroll');
  if (!elements.length) return; // sem nada pra animar, nem crio o observer

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animated');
        observer.unobserve(entry.target); // animo so uma vez e paro de observar esse elemento
      }
    });
  }, { threshold: 0.15 }); // dispara quando 15% do elemento aparece

  elements.forEach(el => observer.observe(el));
}

/* ------- Password Toggle ------- */
// botao de mostrar/esconder senha do campo do GOV.br.
// clono o botao e troco pelo clone (replaceChild) de proposito: isso joga fora os listeners
// que o JS do GOV.br ja tinha pendurado, pra so o MEU clique valer e nao acontecer toggle duplo
function initPasswordToggles() {
  document.querySelectorAll('.br-input.input-button .br-button[aria-label="Mostrar senha"]').forEach(btn => {
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
    clone.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation(); // travo a propagacao pra esse clique nao mexer em label/form em volta
      const input = clone.parentElement.querySelector('input');
      const icon = clone.querySelector('i');
      // alterno o type do input e troco o icone do olho (Font Awesome) de acordo
      if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
      } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
      }
    });
  });
}

/* ------- Utility: Animated Counter ------- */
// faz o numero "subir" de 0 ate o alvo durante 'duration' ms (ex: contadores de estatistica).
// uso requestAnimationFrame pra animacao suave acompanhando o tempo real (timestamp), nao um passo fixo
function animateCounter(element, target, duration = 1500) {
  let start = 0;
  const step = (timestamp) => {
    if (!start) start = timestamp; // primeiro frame: marco o tempo inicial
    const progress = Math.min((timestamp - start) / duration, 1); // fracao 0..1 do quanto ja passou
    const value = Math.floor(progress * target);
    element.textContent = value.toLocaleString('pt-BR'); // formato com separador de milhar pt-BR
    if (progress < 1) requestAnimationFrame(step); // continuo ate chegar em 100%
  };
  requestAnimationFrame(step);
}

// disparo cada contador [data-counter] so quando ele aparece na tela, pra animacao
// rodar na hora que o usuario ve. desconecto o observer depois pra animar uma vez so
document.querySelectorAll('[data-counter]').forEach(el => {
  const observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      animateCounter(el, parseInt(el.dataset.counter, 10)); // o valor alvo vem do data-counter
      observer.disconnect();
    }
  }, { threshold: 0.5 }); // espero metade do elemento visivel pra comecar
  observer.observe(el);
});
