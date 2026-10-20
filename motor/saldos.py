"""Saldo por produto e por lote.

Suposição documentada (FEFO): quando a saída não informa o lote, considera-se que
saiu primeiro o lote que vence primeiro. Lotes sem validade saem por último.
"""

import pandas as pd

TOLERANCIA = 1e-9


def calcular_saldo(mov: pd.DataFrame) -> dict:
    """`mov`: movimentações de UM produto, já em unidade base (qtd_base) e ordenadas."""
    lotes = []           # cada lote: {"lote", "validade", "qtd", "entrada"}
    saldo = 0.0
    negativo_em = None
    menor_saldo = 0.0

    def ordem_fefo(item):
        validade = item["validade"]
        return (pd.isna(validade), validade if pd.notna(validade) else pd.Timestamp.max, item["entrada"])

    for linha in mov.itertuples(index=False):
        q = float(linha.qtd_base)
        lote = str(linha.lote).strip() if pd.notna(linha.lote) and str(linha.lote).strip() else None
        if linha.tipo == "entrada":
            saldo += q
            existente = next((l for l in lotes if l["lote"] == lote and
                              (l["validade"] == linha.validade or
                               (pd.isna(l["validade"]) and pd.isna(linha.validade)))), None)
            if existente:
                existente["qtd"] += q
            else:
                lotes.append({"lote": lote, "validade": linha.validade, "qtd": q, "entrada": linha.data})
            continue

        saldo -= q
        restante = q
        candidatos = sorted([l for l in lotes if l["qtd"] > TOLERANCIA], key=ordem_fefo)
        if lote:
            candidatos = [l for l in candidatos if l["lote"] == lote] + \
                         [l for l in candidatos if l["lote"] != lote]
        for item in candidatos:
            usado = min(item["qtd"], restante)
            item["qtd"] -= usado
            restante -= usado
            if restante <= TOLERANCIA:
                break
        if saldo < -TOLERANCIA and negativo_em is None:
            negativo_em = linha.data
        menor_saldo = min(menor_saldo, saldo)

    return {
        "saldo": saldo,
        "lotes": [l for l in lotes if l["qtd"] > TOLERANCIA],
        "negativo_em": negativo_em,
        "menor_saldo": menor_saldo,
    }
