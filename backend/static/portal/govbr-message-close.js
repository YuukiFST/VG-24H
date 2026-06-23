/**
 * Fecha mensagens .br-message ao clicar em .close (alinhado ao exemplo message-padrao do @govbr-ds/core;
 * o BRAlert em core 3.7 usa um seletor que não liga o clique neste markup).
 */
// rodo dentro de uma IIFE so pra nao vazar variavel pro escopo global da pagina
(function () {
  // uso querySelectorAll pra pegar todos os botoes X de fechar das .br-message de uma vez
  document.querySelectorAll(".br-message > .close .br-button").forEach(function (btn) {
    // engancho o clique no X pra fechar a msg
    btn.addEventListener("click", function () {
      // subo do botao ate a .br-message inteira e removo ela do DOM (fecha de vez, nao so esconde)
      var root = btn.closest(".br-message");
      if (root && root.parentNode) root.parentNode.removeChild(root);
    });
  });
})();
