"""Importação com mapeamento flexível de colunas e validação."""

import io

import pandas as pd

from motor.importacao import aplicar_mapeamento, ler_arquivo, parse_numero, sugerir_mapeamento


def test_reconhece_cabecalhos_com_sinonimos():
    mapa = sugerir_mapeamento(["Insumo", "Qtd", "UN", "Data Movimentação", "E/S", "Valor Unitário",
                               "Vencimento", "Talhão"])
    assert mapa == {"produto": "Insumo", "quantidade": "Qtd", "unidade": "UN", "data": "Data Movimentação",
                    "tipo": "E/S", "preco_unitario": "Valor Unitário", "validade": "Vencimento",
                    "destino": "Talhão"}


def test_le_csv_com_ponto_e_virgula_e_latin1():
    conteudo = "Produto;Quantidade\nCalcário;1,5\n".encode("latin-1")
    df = ler_arquivo(conteudo, "base.csv")
    assert list(df.columns) == ["Produto", "Quantidade"] and df.iloc[0]["Produto"] == "Calcário"


def test_le_xlsx():
    buffer = io.BytesIO()
    pd.DataFrame({"produto": ["Ureia"], "quantidade": [10]}).to_excel(buffer, index=False)
    df = ler_arquivo(buffer.getvalue(), "base.xlsx")
    assert df.iloc[0]["produto"] == "Ureia"


def test_numeros_no_formato_brasileiro():
    assert parse_numero("1.234,5") == 1234.5
    assert parse_numero("1,5") == 1.5
    assert parse_numero("1234.5") == 1234.5
    assert parse_numero("R$ 12,90") == 12.9
    assert parse_numero("") is None


def _bruto(**colunas):
    base = {"produto": ["Ureia"], "tipo": ["Saída"], "quantidade": ["10"], "data": ["30/09/2026"],
            "unidade": ["Kg"]}
    base.update(colunas)
    return pd.DataFrame(base)


MAPA = {c: c for c in ["produto", "tipo", "quantidade", "data", "unidade", "preco_unitario", "validade"]}


def test_linha_valida_e_normalizada():
    df, erros, _ = aplicar_mapeamento(_bruto(), MAPA)
    assert erros == []
    linha = df.iloc[0]
    assert linha["tipo"] == "saida" and linha["unidade"] == "kg" and linha["quantidade"] == 10
    assert linha["data"] == pd.Timestamp("2026-09-30")


def test_linhas_invalidas_sao_recusadas_com_motivo():
    df, erros, _ = aplicar_mapeamento(_bruto(quantidade=["-3"], tipo=["transferência"]), MAPA)
    assert df.empty
    assert "Linha 2" in erros[0] and "quantidade" in erros[0] and "tipo" in erros[0]


def test_preco_e_validade_ausentes_continuam_ausentes():
    df, erros, avisos = aplicar_mapeamento(_bruto(preco_unitario=[""], validade=["não sei"]), MAPA)
    assert erros == []
    assert df.iloc[0]["preco_unitario"] is None and df.iloc[0]["validade"] is None
    assert any("validade" in a for a in avisos)


def test_preco_zero_e_tratado_como_ausente():
    df, _, avisos = aplicar_mapeamento(_bruto(preco_unitario=["0"]), MAPA)
    assert df.iloc[0]["preco_unitario"] is None and avisos


def test_falta_coluna_obrigatoria():
    df, erros, _ = aplicar_mapeamento(_bruto(), {"produto": "produto"})
    assert df.empty and "obrigatórias" in erros[0]
