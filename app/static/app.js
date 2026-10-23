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

  // Sombra no cabeçalho fixo depois que a página rola.
  var cabecalho = document.getElementById("cabecalho");
  if (cabecalho) {
    var marcar = function () { cabecalho.classList.toggle("rolado", window.scrollY > 4); };
    window.addEventListener("scroll", marcar, { passive: true });
    marcar();
  }

  // Mensagens: botão de fechar (só aparece com JavaScript).
  document.querySelectorAll("[data-fechar]").forEach(function (botao) {
    botao.hidden = false;
    botao.addEventListener("click", function () { botao.closest(".mensagem").remove(); });
  });

  // Upload: arrastar e soltar + nome do arquivo escolhido.
  document.querySelectorAll(".zona-upload").forEach(function (zona) {
    var campo = zona.querySelector('input[type="file"]');
    var nome = zona.querySelector(".nome-arquivo");
    if (!campo) return;
    var mostrar = function () {
      if (nome && campo.files.length) nome.textContent = "Arquivo escolhido: " + campo.files[0].name;
    };
    campo.addEventListener("change", mostrar);
    ["dragenter", "dragover"].forEach(function (tipo) {
      zona.addEventListener(tipo, function (evento) { evento.preventDefault(); zona.classList.add("arrastando"); });
    });
    ["dragleave", "drop"].forEach(function (tipo) {
      zona.addEventListener(tipo, function () { zona.classList.remove("arrastando"); });
    });
    zona.addEventListener("drop", function (evento) {
      evento.preventDefault();
      if (evento.dataTransfer && evento.dataTransfer.files.length) {
        campo.files = evento.dataTransfer.files;
        mostrar();
      }
    });
  });
})();
