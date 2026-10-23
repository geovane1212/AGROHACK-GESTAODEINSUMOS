"""Cada regra de alerta, incluindo casos de borda."""

from motor.analise import analisar

from .conftest import REF, mov, saidas_regulares, tabela


def _alertas(res, tipo, chave=None):
    return [a for a in res.alertas if a.tipo == tipo and (chave is None or a.chave_produto == chave)]


# ------------------------------------------------------------------ estoque crítico
def test_cobertura_curta_e_critica_com_justificativa_no_estilo_oficial():
    # 10 L/dia nos últimos 30 dias; saldo de 60 L → ~6 dias.
    linhas = [mov("Diesel", "entrada", 960, 89, "L")] + saidas_regulares("Diesel", 30, 3, unidade="L")
    res = analisar(tabela(*linhas))
    [alerta] = _alertas(res, "estoque_critico")
    assert alerta.severidade == "Crítico"
    assert "poderá ser suficiente por aproximadamente 6 dias" in alerta.mensagem
    assert "Confiança alta" in alerta.mensagem
    assert alerta.regra and alerta.limite


def test_cobertura_entre_7_e_15_dias_e_atencao():
    linhas = [mov("Diesel", "entrada", 1000, 89, "L")] + saidas_regulares("Diesel", 30, 3, unidade="L")
    [alerta] = _alertas(analisar(tabela(*linhas)), "estoque_critico")   # saldo 100 L → 10 dias
    assert alerta.severidade == "Atenção" and alerta.titulo == "Estoque baixo"


def test_saldo_abaixo_do_minimo_e_critico_mesmo_com_boa_cobertura():
    linhas = [mov("Herbicida", "entrada", 200, 89, "L", estoque_minimo=150)] + \
             saidas_regulares("Herbicida", 3, 3, unidade="L", estoque_minimo=150)
    [alerta] = _alertas(analisar(tabela(*linhas)), "estoque_critico")    # saldo 110 L, mínimo 150
    assert alerta.severidade == "Crítico"
    assert "abaixo do estoque mínimo" in alerta.mensagem


def test_estoque_confortavel_nao_gera_alerta():
    linhas = [mov("Diesel", "entrada", 3000, 89, "L")] + saidas_regulares("Diesel", 30, 3, unidade="L")
    assert _alertas(analisar(tabela(*linhas)), "estoque_critico") == []


def test_baixa_confianca_aparece_no_texto_e_reduz_prioridade():
    linhas = [mov("Peça", "entrada", 10, 50, "un"), mov("Peça", "saida", 4, 20, "un"),
              mov("Peça", "saida", 4, 0, "un")]
    [alerta] = _alertas(analisar(tabela(*linhas)), "estoque_critico")
    assert "Baixa confiança: só 2 saídas" in alerta.mensagem
    assert any("baixa confiança" in parte for parte in alerta.score_partes)


# ------------------------------------------------------------------ vencimento
def test_lote_que_vence_antes_de_ser_usado():
    linhas = [mov("Inoculante", "entrada", 40, 60, "L", lote="L1", validade="2026-10-20", preco_unitario=45.0)] + \
             saidas_regulares("Inoculante", 1, 7, dias=60, unidade="L")
    [alerta] = _alertas(analisar(tabela(*linhas)), "vencimento")
    assert alerta.severidade == "Crítico"          # vence em 20 dias e sobra produto
    assert "vencem em 20 dias" in alerta.mensagem and "R$" in alerta.mensagem


def test_lote_vencido_com_saldo():
    linhas = [mov("Trichoderma", "entrada", 10, 100, lote="T1", validade="2026-09-15"),
              mov("Trichoderma", "saida", 2, 50)]
    [alerta] = _alertas(analisar(tabela(*linhas), data_ref=REF), "vencimento")
    assert alerta.titulo == "Lote vencido" and alerta.severidade == "Crítico"


def test_lote_que_sera_consumido_a_tempo_nao_alerta():
    # 1 L/dia e 30 L que vencem em 60 dias: dá tempo de usar.
    linhas = [mov("Adjuvante", "entrada", 120, 89, "L", lote="A", validade="2026-11-29")] + \
             saidas_regulares("Adjuvante", 3, 3, unidade="L")
    assert _alertas(analisar(tabela(*linhas)), "vencimento") == []


def test_validade_ausente_nao_gera_alerta_de_vencimento():
    linhas = [mov("Semente", "entrada", 100, 30, "kg", lote="S1")]
    assert _alertas(analisar(tabela(*linhas)), "vencimento") == []


# ------------------------------------------------------------------ excesso
def test_cobertura_muito_longa_e_excesso():
    linhas = [mov("Graxa", "entrada", 300, 89)] + saidas_regulares("Graxa", 1, 6)   # ~0,17 kg/dia
    [alerta] = _alertas(analisar(tabela(*linhas)), "excesso")
    assert alerta.severidade == "Atenção" and "acima do limite de 180 dias" in alerta.mensagem


def test_sem_consumo_e_muito_acima_do_minimo_e_informativo():
    [alerta] = _alertas(analisar(tabela(mov("Disco", "entrada", 50, 30, "un", estoque_minimo=5))), "excesso")
    assert alerta.severidade == "Informativo"


# ------------------------------------------------------------------ retirada fora do padrão
def test_retirada_muito_acima_da_mediana():
    linhas = [mov("Óleo", "entrada", 500, 89, "L")] + \
             [mov("Óleo", "saida", 5, d, "L") for d in range(5, 89, 5)] + \
             [mov("Óleo", "saida", 60, 2, "L", destino="Trator 2")]
    [alerta] = _alertas(analisar(tabela(*linhas)), "fora_do_padrao")
    assert "60 L" in alerta.mensagem and "Trator 2" in alerta.mensagem


def test_variacao_normal_nao_e_fora_do_padrao():
    qtds = [5, 6, 4, 5, 7, 5, 6, 4, 5, 6, 8]
    linhas = [mov("Óleo", "entrada", 500, 89, "L")] + \
             [mov("Óleo", "saida", q, 3 + i * 7, "L") for i, q in enumerate(qtds)]
    assert _alertas(analisar(tabela(*linhas)), "fora_do_padrao") == []


def test_poucas_saidas_nao_permitem_julgar_o_padrao():
    linhas = [mov("Óleo", "entrada", 500, 89, "L"), mov("Óleo", "saida", 5, 40, "L"),
              mov("Óleo", "saida", 5, 20, "L"), mov("Óleo", "saida", 60, 2, "L")]
    assert _alertas(analisar(tabela(*linhas)), "fora_do_padrao") == []


# ------------------------------------------------------------------ consumo crescente
def test_consumo_crescente_em_tres_blocos():
    linhas = [mov("Fungicida", "entrada", 2000, 95, "L")]
    for d in range(0, 90, 3):
        linhas.append(mov("Fungicida", "saida", 2 if d >= 60 else (3 if d >= 30 else 5), d, "L"))
    [alerta] = _alertas(analisar(tabela(*linhas)), "consumo_crescente")
    assert "alta de 150%" in alerta.mensagem


def test_pico_isolado_nao_vira_consumo_crescente():
    # Leve alta (24 → 27 → 27 L) + um pico de 60 L: sem excluir o pico, pareceria tendência (24 → 27 → 87 L).
    linhas = [mov("Óleo", "entrada", 500, 95, "L"), mov("Óleo", "saida", 60, 1, "L")]
    linhas += [mov("Óleo", "saida", 4 if d >= 60 else 4.5, d, "L") for d in range(0, 90, 5)]
    res = analisar(tabela(*linhas))
    assert len(_alertas(res, "fora_do_padrao")) == 1
    assert _alertas(res, "consumo_crescente") == []


def test_consumo_estavel_nao_e_crescente():
    linhas = [mov("Fungicida", "entrada", 2000, 95, "L")] + saidas_regulares("Fungicida", 3, 3, unidade="L")
    assert _alertas(analisar(tabela(*linhas)), "consumo_crescente") == []


# ------------------------------------------------------------------ preço
def test_compra_muito_mais_cara_que_a_mediana():
    linhas = [mov("KCl", "entrada", 1000, d, preco_unitario=3.0) for d in (150, 120, 90)] + \
             [mov("KCl", "entrada", 1000, 10, preco_unitario=4.2)]
    [alerta] = _alertas(analisar(tabela(*linhas)), "variacao_preco")
    assert alerta.severidade == "Atenção" and "40% acima" in alerta.mensagem


def test_preco_compara_por_unidade_base():
    # 1 sc de 50 kg por R$ 150 = R$ 3/kg: mesmo preço das compras em kg, não deve alertar.
    linhas = [mov("Ureia", "entrada", 1000, d, preco_unitario=3.0) for d in (150, 120, 90)] + \
             [mov("Ureia", "entrada", 10, 10, "sc", preco_unitario=150.0)]
    res = analisar(tabela(*linhas), fatores={("ureia", "sc"): (50, "kg")})
    assert _alertas(res, "variacao_preco") == []


# ------------------------------------------------------------------ alto valor parado
def test_item_caro_sem_saida_e_alto_valor_parado():
    linhas = [mov("Correia", "entrada", 4, 120, "un", preco_unitario=2800.0),
              mov("Luva", "entrada", 100, 120, "par", preco_unitario=4.0)] + \
             saidas_regulares("Luva", 2, 3, unidade="par")
    res = analisar(tabela(*linhas))
    assert len(_alertas(res, "alto_valor_parado", "correia")) == 1
    assert _alertas(res, "alto_valor_parado", "luva") == []


def test_item_sem_preco_fica_fora_da_curva_abc():
    res = analisar(tabela(mov("Peça cara", "entrada", 4, 120, "un")))
    assert res.produtos[0]["classe_abc"] is None and res.alertas == []


# ------------------------------------------------------------------ priorização
def test_alertas_ordenados_por_prioridade():
    linhas = [mov("Diesel", "entrada", 960, 89, "L")] + saidas_regulares("Diesel", 30, 3, unidade="L") + \
             [mov("Graxa", "entrada", 300, 89)] + saidas_regulares("Graxa", 1, 6)
    res = analisar(tabela(*linhas))
    assert [a.severidade for a in res.alertas] == ["Crítico", "Atenção"]
    assert res.alertas[0].score > res.alertas[1].score


# ------------------------------------------------------------------ resumo curto (painel compacto)
def test_resumo_do_estoque_critico():
    linhas = [mov("Diesel", "entrada", 960, 89, "L", estoque_minimo=100)] + \
             saidas_regulares("Diesel", 30, 3, unidade="L", estoque_minimo=100)
    [alerta] = _alertas(analisar(tabela(*linhas)), "estoque_critico")
    assert alerta.resumo == "Dura ~6 dias · saldo 60 L (mínimo: 100 L)"
    assert "poderá ser suficiente por aproximadamente 6 dias" in alerta.mensagem   # mensagem completa intacta


def test_resumo_do_vencimento_mostra_o_lote_mais_urgente():
    linhas = [mov("Inoculante", "entrada", 40, 60, "L", lote="L1", validade="2026-10-20")] + \
             saidas_regulares("Inoculante", 1, 7, dias=60, unidade="L")
    [alerta] = _alertas(analisar(tabela(*linhas)), "vencimento")
    assert alerta.resumo.startswith("Lote L1 vence em 20 dias, sobra ≈ ")


def test_resumo_da_retirada_fora_do_padrao():
    linhas = [mov("Óleo", "entrada", 500, 89, "L")] + \
             [mov("Óleo", "saida", 5, d, "L") for d in range(5, 89, 5)] + [mov("Óleo", "saida", 60, 2, "L")]
    [alerta] = _alertas(analisar(tabela(*linhas)), "fora_do_padrao")
    assert alerta.resumo == "Retirada de 60 L em 28/09/2026: 12× o normal"


def test_todo_alerta_da_base_simulada_tem_resumo_curto():
    from tests.test_gabarito import CSV
    from motor.importacao import aplicar_mapeamento, ler_arquivo, sugerir_mapeamento
    bruto = ler_arquivo(CSV.read_bytes(), CSV.name)
    df, _, _ = aplicar_mapeamento(bruto, sugerir_mapeamento(bruto.columns))
    for alerta in analisar(df).alertas:
        assert alerta.resumo, alerta.tipo
        assert len(alerta.resumo) <= 90, alerta.resumo
