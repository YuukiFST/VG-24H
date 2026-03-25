/**
 * Fecha mensagens .br-message ao clicar em .close (alinhado ao exemplo message-padrao do @govbr-ds/core;
 * o BRAlert em core 3.7 usa um seletor que não liga o clique neste markup).
 */
(function () {
  document.querySelectorAll(".br-message > .close .br-button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var root = btn.closest(".br-message");
      if (root && root.parentNode) root.parentNode.removeChild(root);
    });
  });
})();
