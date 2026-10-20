"""Ponta a ponta: o sistema encontra os problemas plantados em data/simulado/GABARITO_SIMULADO.md?

Importa o CSV simulado pelo mesmo caminho do usuário (mapeamento automático de colunas) e compara
os alertas e avisos com o gabarito. Também confere que NÃO aparecem alertas fora do gabarito.
"""

from pathlib import Path

import pytest

from motor.analise import analisar
from motor.importacao import aplicar_mapeamento, ler_arquivo, sugerir_mapeamento

CSV = Path(__file__).resolve().parent.parent / "data" / "simulado" / "movimentacoes_simulado.csv"

# (id do gabarito, tipo do alerta, produto, severidade esperada)
ALERTAS_ESPERADOS = [
    ("G01", "estoque_critico", "Diesel S10", "Crítico"),
    ("G02", "estoque_critico", "Glifosato 480", "Crítico"),
    ("G03", "consumo_crescente", "Fungicida azoxistrobina", "Atenção"),
    ("G04", "excesso", "Graxa", "Atenção"),
    ("G05", "fora_do_padrao", "Óleo de motor 15W40", "Atenção"),
    ("G06", "variacao_preco", "Cloreto de potássio (KCl)", "Atenção"),
    ("G07", "vencimento", "Inoculante para soja", "Crítico"),
    ("G08", "vencimento", "Trichoderma", "Crítico"),
    ("G09", "vencimento", "Semente de feijão", "Atenção"),
    ("G10", "alto_valor_parado", "Inseticida clorantraniliprole", "Atenção"),
    ("G11", "alto_valor_parado", "Correia da colheitadeira", "Atenção"),
    ("G20", "estoque_critico", "Bico de pulverização", "Crítico"),
    # Consequências esperadas dos nomes duplicados e das unidades sem fator (somem após corrigir):
    ("C1", "estoque_critico", "Ureia", "Crítico"),
    ("C2", "estoque_critico", "Luvas nitrilicas", "Crítico"),
    ("C3", "alto_valor_parado", "UREIA 45%", "Atenção"),
]

QUALIDADE_ESPERADA = [
    ("G16", "unidade_inconsistente", "Ureia"),
    ("G18", "preco_ausente", "Atrazina"),
    ("G18", "preco_ausente", "Estacas de eucalipto"),
    ("G19", "validade_ausente", "Atrazina"),
    ("G19", "validade_ausente", "Semente de soja"),
    ("G14", "grafias_equivalentes", "Óleo hidráulico"),
    ("G20", "saldo_negativo", "Bico de pulverização"),
    ("C1", "saldo_negativo", "Ureia"),
    ("C2", "saldo_negativo", "Luvas nitrilicas"),
]

SUGESTOES_ESPERADAS = [
    ("G12", {"Ureia", "UREIA 45%"}),
    ("G12", {"Ureia", "ureia granulada"}),
    ("G12", {"UREIA 45%", "ureia granulada"}),
    ("G13", {"Luva nitrílica", "Luvas nitrilicas"}),
]


@pytest.fixture(scope="module")
def resultado():
    bruto = ler_arquivo(CSV.read_bytes(), CSV.name)
    df, erros, _ = aplicar_mapeamento(bruto, sugerir_mapeamento(bruto.columns))
    assert erros == []
    return analisar(df)


def test_data_de_referencia_e_a_ultima_movimentacao(resultado):
    assert resultado.data_referencia.strftime("%Y-%m-%d") == "2026-09-30"


@pytest.mark.parametrize("gid, tipo, produto, severidade", ALERTAS_ESPERADOS)
def test_alerta_do_gabarito_encontrado(resultado, gid, tipo, produto, severidade):
    achados = [a for a in resultado.alertas if a.tipo == tipo and a.produto == produto]
    assert achados, f"{gid}: alerta '{tipo}' de '{produto}' não encontrado"
    assert achados[0].severidade == severidade


def test_nenhum_alerta_fora_do_gabarito(resultado):
    esperados = {(tipo, produto) for _, tipo, produto, _ in ALERTAS_ESPERADOS}
    extras = [(a.tipo, a.produto) for a in resultado.alertas if (a.tipo, a.produto) not in esperados]
    assert extras == []


@pytest.mark.parametrize("gid, tipo, produto", QUALIDADE_ESPERADA)
def test_aviso_de_qualidade_encontrado(resultado, gid, tipo, produto):
    assert any(q["tipo"] == tipo and q["produto"] == produto for q in resultado.qualidade), gid


@pytest.mark.parametrize("gid, par", SUGESTOES_ESPERADAS)
def test_sugestao_de_unificacao_encontrada(resultado, gid, par):
    assert any({s.nome_a, s.nome_b} == par for s in resultado.sugestoes), gid


def test_g15_formulacoes_diferentes_nao_sao_sugeridas(resultado):
    pares = [{s.nome_a, s.nome_b} for s in resultado.sugestoes]
    assert {"NPK 04-14-08", "NPK 04-30-16"} not in pares
    assert {"Filtro de óleo", "Filtro de ar"} not in pares
    assert len(resultado.sugestoes) == len(SUGESTOES_ESPERADAS)


def test_g17_mililitros_convertidos_sem_aviso(resultado):
    adjuvante = resultado.produto("adjuvante")
    assert adjuvante["unidade"] == "L"
    assert not any(q["produto"] == "Adjuvante" for q in resultado.qualidade)


def test_g18_valor_em_estoque_avisa_itens_sem_preco(resultado):
    assert resultado.resumo["sem_preco"] == ["Estacas de eucalipto"]


def test_correcoes_resolvem_as_consequencias():
    bruto = ler_arquivo(CSV.read_bytes(), CSV.name)
    df, _, _ = aplicar_mapeamento(bruto, sugerir_mapeamento(bruto.columns))
    res = analisar(df, apelidos={"ureia 45%": "ureia", "ureia granulada": "ureia",
                                 "luvas nitrilicas": "luva nitrilica"},
                   fatores={("ureia", "sc"): (50, "kg")})
    produtos = {a.produto for a in res.alertas}
    assert not produtos & {"Ureia", "UREIA 45%", "Luvas nitrilicas", "Luva nitrílica"}
    assert res.produto("ureia")["saldo"] > 0
    assert not any(q["tipo"] in ("unidade_inconsistente", "nome_duplicado") for q in res.qualidade)
