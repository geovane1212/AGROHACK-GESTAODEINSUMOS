"""Prepara as movimentações para análise.

1. Aplica a data de referência (movimentações posteriores são ignoradas).
2. Agrupa nomes pela chave normalizada + apelidos confirmados.
3. Converte quantidades para a unidade base de cada produto.
4. Marca como excluídas as movimentações cuja unidade não pode ser convertida.
"""

import pandas as pd

from .nomes import normalizar_texto
from .unidades import normalizar_unidade, para_base

COLUNAS = [
    "produto", "categoria", "unidade", "quantidade", "estoque_minimo", "tipo", "data",
    "preco_unitario", "lote", "validade", "fornecedor", "destino", "responsavel",
]


def resolver_apelido(chave: str, apelidos: dict) -> str:
    vistos = set()
    while chave in apelidos and chave not in vistos:
        vistos.add(chave)
        chave = apelidos[chave]
    return chave


def _mais_frequente(serie: pd.Series):
    serie = serie.dropna()
    serie = serie[serie.astype(str).str.strip() != ""]
    return serie.mode().iloc[0] if not serie.empty else None


def preparar(movs: pd.DataFrame, apelidos=None, fatores=None, data_ref=None):
    """Devolve (df preparado, data de referência, nº de movimentações futuras ignoradas).

    apelidos: {chave normalizada do apelido: chave normalizada do produto canônico}
    fatores:  {(chave do produto, unidade): (fator, unidade destino)}
    """
    apelidos = apelidos or {}
    fatores = fatores or {}
    df = movs.copy()
    for coluna in COLUNAS:
        if coluna not in df.columns:
            df[coluna] = None
    df["data"] = pd.to_datetime(df["data"]).dt.normalize()
    df["validade"] = pd.to_datetime(df["validade"], errors="coerce").dt.normalize()
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df["preco_unitario"] = pd.to_numeric(df["preco_unitario"], errors="coerce")
    df["estoque_minimo"] = pd.to_numeric(df["estoque_minimo"], errors="coerce")
    df["tipo"] = df["tipo"].str.lower().str.replace("í", "i")

    if df.empty:
        return df.assign(chave=[], nome=[], qtd_base=[], unidade_base=[], incluida=[]), data_ref, 0

    data_ref = pd.Timestamp(data_ref).normalize() if data_ref is not None else df["data"].max()
    futuras = int((df["data"] > data_ref).sum())
    df = df[df["data"] <= data_ref].copy()

    df["chave_original"] = df["produto"].map(normalizar_texto)
    df["chave"] = df["chave_original"].map(lambda k: resolver_apelido(k, apelidos))
    df["unidade"] = df["unidade"].map(normalizar_unidade)

    def converter(linha):
        fat = {u: f for (k, u), f in fatores.items() if k == linha["chave"]}
        q, u = para_base(linha["quantidade"], linha["unidade"], fat)
        minimo = None
        if pd.notna(linha["estoque_minimo"]):
            minimo, _ = para_base(linha["estoque_minimo"], linha["unidade"], fat)
        return pd.Series({"qtd_base": q, "unidade_base": u, "minimo_base": minimo})

    df = df.join(df.apply(converter, axis=1)) if not df.empty else df
    # Preço por unidade base. Preço ausente continua ausente (nunca vira zero).
    df["preco_base"] = df["preco_unitario"] * df["quantidade"] / df["qtd_base"]

    principal = df.groupby("chave")["unidade_base"].agg(lambda s: s.value_counts().index[0])
    df["unidade_principal"] = df["chave"].map(principal)
    df["incluida"] = df["unidade_base"] == df["unidade_principal"]

    nomes = {}
    for chave, grupo in df.groupby("chave"):
        proprios = grupo[grupo["chave_original"] == chave]["produto"]
        nomes[chave] = _mais_frequente(proprios if not proprios.empty else grupo["produto"])
    df["nome"] = df["chave"].map(nomes)
    categorias = df.groupby("chave")["categoria"].agg(_mais_frequente)
    df["categoria"] = df["chave"].map(categorias).fillna("Sem categoria")
    return df.sort_values(["data", "tipo"]).reset_index(drop=True), data_ref, futuras
