"""Fluxos da interface: cadastro, importação, unificação, fator, data de referência e reanálise."""

import io

from app import db, servicos


def _alertas(app):
    with app.app_context():
        return {(a.titulo, a.produto): a.severidade for a in servicos.analise_atual().alertas}


def _ultima_mudanca(app):
    with app.app_context():
        return servicos.ultima_mudanca()


def test_retirada_grande_gera_alerta_na_reanalise(app, cliente):
    """Roteiro da demonstração ao vivo."""
    assert ("Retirada fora do padrão", "Óleo hidráulico") not in _alertas(app)
    resposta = cliente.post("/registrar", data={
        "tipo": "saida", "produto": "Óleo hidráulico", "quantidade": "60", "unidade": "L",
        "data": "2026-09-30", "destino": "Trator 1", "responsavel": "Tratorista A"})
    assert resposta.status_code == 302
    alertas = _alertas(app)
    assert ("Retirada fora do padrão", "Óleo hidráulico") in alertas
    assert alertas[("Estoque crítico", "Óleo hidráulico")] == "Crítico"
    assert ("Consumo crescente", "Óleo hidráulico") not in alertas    # pico isolado não é tendência
    novos = {(x["titulo"], x["produto"]) for x in _ultima_mudanca(app)["novos"]}
    assert ("Retirada fora do padrão", "Óleo hidráulico") in novos
    html = cliente.get("/").get_data(as_text=True)
    assert "O que mudou na última reanálise" in html and "Óleo hidráulico" in html


def test_registro_invalido_nao_e_salvo(app, cliente):
    with app.app_context():
        antes = db.contar_movimentacoes()
    resposta = cliente.post("/registrar", data={"tipo": "saida", "produto": "Diesel S10", "quantidade": "-5",
                                                "unidade": "L", "data": "2026-09-30"})
    assert resposta.status_code == 400 and "quantidade" in resposta.get_data(as_text=True)
    with app.app_context():
        assert db.contar_movimentacoes() == antes


def test_unificar_nomes_resolve_alertas_causados_pela_duplicidade(app, cliente):
    assert ("Alto valor parado", "UREIA 45%") in _alertas(app)
    cliente.post("/qualidade/unificar", data={"canonico": "ureia", "outro": "ureia 45%"})
    cliente.post("/qualidade/unificar", data={"canonico": "ureia", "outro": "ureia granulada"})
    alertas = _alertas(app)
    assert ("Alto valor parado", "UREIA 45%") not in alertas
    with app.app_context():
        assert {a["apelido"] for a in db.listar_apelidos()} == {"ureia 45%", "ureia granulada"}


def test_fator_de_unidade_corrige_o_saldo(app, cliente):
    assert _alertas(app)[("Estoque crítico", "Ureia")] == "Crítico"
    cliente.post("/qualidade/fator", data={"produto": "ureia", "unidade": "sc", "fator": "50", "destino": "kg"})
    assert ("Estoque crítico", "Ureia") not in _alertas(app)
    with app.app_context():
        assert servicos.analise_atual().produto("ureia")["saldo"] > 0


def test_rejeitar_sugestao(app, cliente):
    cliente.post("/qualidade/rejeitar", data={"a": "luva nitrilica", "b": "luvas nitrilicas"})
    with app.app_context():
        sugestoes = {(s.chave_a, s.chave_b) for s in servicos.analise_atual().sugestoes}
    assert ("luva nitrilica", "luvas nitrilicas") not in sugestoes


def test_importar_csv_com_outros_nomes_de_coluna(app, cliente):
    csv = ("Insumo;Qtd;UN;Data;E/S;Valor Unitário\n"
           "Diesel S10;5000;L;30/09/2026;Entrada;6,10\n"
           "Produto Novo;10;kg;30/09/2026;Entrada;\n"
           ";10;kg;30/09/2026;Entrada;\n").encode("utf-8")
    resposta = cliente.post("/importar", data={"arquivo": (io.BytesIO(csv), "base.csv")},
                            content_type="multipart/form-data")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200 and "Conferir colunas" in html
    token = html.split('name="token" value="')[1].split('"')[0]
    campos = {"campo_produto": "Insumo", "campo_quantidade": "Qtd", "campo_unidade": "UN", "campo_data": "Data",
              "campo_tipo": "E/S", "campo_preco_unitario": "Valor Unitário"}
    resposta = cliente.post("/importar/confirmar", data={"token": token, "nome": "base.csv", **campos})
    html = resposta.get_data(as_text=True)
    assert "2 movimentação(ões) importada(s)" in html
    assert "Linha 4" in html                                  # linha sem produto recusada
    assert ("Estoque crítico", "Diesel S10") not in _alertas(app)   # a compra resolveu o diesel


def test_importar_substituindo_a_base(app, cliente):
    csv = "produto,tipo,quantidade,data,unidade\nCalcário,entrada,10,2026-10-01,t\n".encode("utf-8")
    html = cliente.post("/importar", data={"arquivo": (io.BytesIO(csv), "oficial.csv")},
                        content_type="multipart/form-data").get_data(as_text=True)
    token = html.split('name="token" value="')[1].split('"')[0]
    cliente.post("/importar/confirmar", data={
        "token": token, "nome": "oficial.csv", "substituir": "1", "campo_produto": "produto",
        "campo_tipo": "tipo", "campo_quantidade": "quantidade", "campo_data": "data", "campo_unidade": "unidade"})
    with app.app_context():
        assert db.contar_movimentacoes() == 1 and db.contar_movimentacoes("simulado") == 0
    assert "SIMULADOS" not in cliente.get("/").get_data(as_text=True)


def test_data_de_referencia_configuravel(app, cliente):
    cliente.post("/data-referencia", data={"data_referencia": "2026-08-31", "acao": "manual"})
    html = cliente.get("/").get_data(as_text=True)
    assert "31/08/2026" in html and "escolhida manualmente" in html
    cliente.post("/data-referencia", data={"acao": "automatica"})
    assert "30/09/2026" in cliente.get("/").get_data(as_text=True)


def test_restaurar_demonstracao(app, cliente):
    cliente.post("/qualidade/fator", data={"produto": "ureia", "unidade": "sc", "fator": "50", "destino": "kg"})
    cliente.post("/demo/restaurar")
    with app.app_context():
        assert db.listar_fatores() == [] and db.contar_movimentacoes("simulado") > 1000
