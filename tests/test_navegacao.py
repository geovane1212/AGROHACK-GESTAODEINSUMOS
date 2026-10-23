"""Navegação da v2: menu, busca, atalhos, página Mais e paginação do histórico."""


def test_menu_principal_com_cinco_itens_e_pagina_atual(cliente):
    html = cliente.get("/alertas").get_data(as_text=True)
    barra = html.split('class="barra-inferior"')[1].split("</nav>")[0]
    assert barra.count('class="nav-item') == 5
    for rotulo in ("Início", "Alertas", "Registrar", "Estoque", "Mais"):
        assert rotulo in barra
    atual = barra.split('aria-current="page"')[0].rsplit("<a", 1)[1]
    assert "/alertas" in atual


def test_atalhos_do_botao_registrar_funcionam_sem_javascript(cliente):
    html = cliente.get("/registrar/atalhos").get_data(as_text=True)
    for texto in ("Registrar retirada", "Registrar entrada", "Importar planilha", "Ver urgentes"):
        assert texto in html
    assert 'value="entrada" checked' in cliente.get("/registrar?tipo=entrada").get_data(as_text=True)


def test_busca_com_um_resultado_abre_o_produto(cliente):
    resposta = cliente.get("/busca?q=diesel")
    assert resposta.status_code == 302 and "/produto/" in resposta.headers["Location"]


def test_busca_com_varios_resultados_lista_os_produtos(cliente):
    html = cliente.get("/busca?q=npk").get_data(as_text=True)
    assert "NPK 04-14-08" in html and "NPK 04-30-16" in html


def test_busca_sem_resultado(cliente):
    assert "Nenhum produto encontrado" in cliente.get("/busca?q=xyzabc").get_data(as_text=True)


def test_pagina_mais_tem_data_de_referencia_e_restauracao(cliente):
    html = cliente.get("/mais").get_data(as_text=True)
    assert 'id="data-referencia"' in html and "Restaurar base de demonstração" in html


def test_historico_paginado(cliente):
    pagina1 = cliente.get("/movimentacoes").get_data(as_text=True)
    assert "página 1 de" in pagina1
    assert cliente.get("/movimentacoes?pagina=2").status_code == 200
    assert cliente.get("/movimentacoes?pagina=9999").status_code == 200   # página fora do limite não quebra
