"""Saldo, lotes (FEFO), consumo médio, confiança e qualidade dos dados."""

from datetime import timedelta

import pandas as pd

from motor.analise import analisar
from motor.config import PADRAO
from motor.consumo import confianca

from .conftest import REF, mov, saidas_regulares, tabela


def _prod(res, chave):
    return res.produto(chave)


def test_saldo_e_entradas_menos_saidas():
    res = analisar(tabela(mov("Diesel", "entrada", 1000, 20, "L"), mov("Diesel", "saida", 300, 10, "L"),
                          mov("Diesel", "saida", 200, 0, "L")))
    assert _prod(res, "diesel")["saldo"] == 500


def test_saida_sem_lote_consome_primeiro_o_que_vence_primeiro():
    res = analisar(tabela(
        mov("Fungicida", "entrada", 10, 50, "L", lote="NOVO", validade="2027-06-01"),
        mov("Fungicida", "entrada", 10, 40, "L", lote="VELHO", validade="2026-12-01"),
        mov("Fungicida", "saida", 6, 0, "L"),
    ))
    lotes = {l["lote"]: l["qtd"] for l in _prod(res, "fungicida")["lotes"]}
    assert lotes == {"NOVO": 10, "VELHO": 4}


def test_saida_com_lote_informado_respeita_o_lote():
    res = analisar(tabela(
        mov("Fungicida", "entrada", 10, 50, "L", lote="A", validade="2026-12-01"),
        mov("Fungicida", "entrada", 10, 40, "L", lote="B", validade="2027-06-01"),
        mov("Fungicida", "saida", 6, 0, "L", lote="B"),
    ))
    lotes = {l["lote"]: l["qtd"] for l in _prod(res, "fungicida")["lotes"]}
    assert lotes == {"A": 10, "B": 4}


def test_saldo_negativo_vira_aviso_de_qualidade():
    res = analisar(tabela(mov("Bico", "entrada", 2, 30, "un"), mov("Bico", "saida", 5, 0, "un")))
    assert _prod(res, "bico")["saldo"] == -3
    assert any(q["tipo"] == "saldo_negativo" for q in res.qualidade)


def test_niveis_de_confianca_documentados():
    assert confianca(10, PADRAO) == "alta"
    assert confianca(5, PADRAO) == "média"
    assert confianca(2, PADRAO) == "baixa"
    assert confianca(1, PADRAO) is None


def test_consumo_zero_nao_gera_cobertura_nem_divisao_por_zero():
    res = analisar(tabela(mov("Graxa", "entrada", 10, 30)))
    p = _prod(res, "graxa")
    assert p["consumo"]["consumo_diario"] is None and p["cobertura"] is None


def test_historico_curto_nao_estima():
    res = analisar(tabela(mov("Peça", "entrada", 10, 30, "un"), mov("Peça", "saida", 1, 0, "un")))
    assert _prod(res, "peca")["consumo"]["confianca"] is None


def test_janela_de_30_dias_quando_ha_saidas_suficientes():
    linhas = [mov("Ureia", "entrada", 5000, 89)] + saidas_regulares("Ureia", 30, 3)
    p = _prod(analisar(tabela(*linhas)), "ureia")
    assert p["consumo"]["janela"] == 30
    assert abs(p["consumo"]["consumo_diario"] - 10) < 0.01   # 10 saídas de 30 kg em 30 dias


def test_preco_ausente_nao_vira_zero():
    res = analisar(tabela(
        mov("Sem preço", "entrada", 10, 20, "un"),
        mov("Com preço", "entrada", 10, 20, "un", preco_unitario=5.0),
    ))
    assert _prod(res, "sem preco")["valor_estoque"] is None
    assert res.resumo["valor_total"] == 50
    assert res.resumo["sem_preco"] == ["Sem preço"]
    assert any(q["tipo"] == "preco_ausente" for q in res.qualidade)


def test_validade_ausente_em_categoria_que_exige_vira_aviso():
    res = analisar(tabela(mov("Semente de soja", "entrada", 10, 20, "sc", categoria="Sementes")))
    assert any(q["tipo"] == "validade_ausente" for q in res.qualidade)


def test_unidades_mistas_sem_fator_ficam_fora_e_geram_aviso():
    res = analisar(tabela(
        mov("Ureia", "entrada", 10, 30, "sc"),
        mov("Ureia", "saida", 100, 20, "kg"), mov("Ureia", "saida", 100, 10, "kg"),
    ))
    p = _prod(res, "ureia")
    assert p["unidade"] == "kg" and p["saldo"] == -200
    assert any(q["tipo"] == "unidade_inconsistente" for q in res.qualidade)


def test_unidades_mistas_com_fator_sao_somadas():
    res = analisar(tabela(
        mov("Ureia", "entrada", 10, 30, "sc"),
        mov("Ureia", "saida", 100, 20, "kg"), mov("Ureia", "saida", 100, 10, "kg"),
    ), fatores={("ureia", "sc"): (50, "kg")})
    assert _prod(res, "ureia")["saldo"] == 300
    assert not any(q["tipo"] == "unidade_inconsistente" for q in res.qualidade)


def test_gramas_e_quilos_somam_sem_fator():
    res = analisar(tabela(mov("FTE", "entrada", 2, 30, "kg"), mov("FTE", "saida", 500, 0, "g")))
    assert _prod(res, "fte")["saldo"] == 1.5


def test_apelido_confirmado_junta_os_produtos():
    dados = tabela(mov("Ureia", "entrada", 100, 30), mov("ureia granulada", "saida", 40, 0))
    assert len(analisar(dados).produtos) == 2
    res = analisar(dados, apelidos={"ureia granulada": "ureia"})
    assert len(res.produtos) == 1 and res.produtos[0]["saldo"] == 60


def test_data_de_referencia_ignora_movimentacoes_posteriores():
    dados = tabela(mov("Diesel", "entrada", 1000, 20, "L"), mov("Diesel", "saida", 900, 0, "L"))
    res = analisar(dados, data_ref=pd.Timestamp(REF - timedelta(days=5)))
    assert _prod(res, "diesel")["saldo"] == 1000
    assert res.resumo["futuras"] == 1
