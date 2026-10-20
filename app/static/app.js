/* Melhorias progressivas: sem JavaScript, todos os links e formulários continuam funcionando. */
(function () {
  "use strict";

  // "+ Registrar": abre o painel de atalhos em vez de ir para a página /registrar/atalhos.
  document.querySelectorAll("[data-abre-folha]").forEach(function (link) {
    var folha = document.getElementById(link.dataset.abreFolha);
    if (!folha || typeof folha.showModal !== "function") return;
    link.addEventListener("click", function (evento) {
      evento.preventDefault();
      folha.showModal();
    });
  });

  // Fecha o painel ao tocar fora dele.
  document.querySelectorAll("dialog.folha").forEach(function (folha) {
    folha.addEventListener("click", function (evento) {
      var r = folha.getBoundingClientRect();
      var fora = evento.clientX < r.left || evento.clientX > r.right ||
                 evento.clientY < r.top || evento.clientY > r.bottom;
      if (evento.target === folha && fora) folha.close();
    });
  });
})();
