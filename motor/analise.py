"""Ponto de entrada do motor: recebe as movimentações e devolve tudo que o painel mostra."""

from dataclasses import dataclass, field

import pandas as pd

from .alertas import ORDEM_SEVERIDADE, gerar_alertas
from .config import PADRAO
from .consumo import estimar_consumo, serie_semanal
from .nomes import normalizar_texto, sugerir_unificacoes
from .preparar import preparar
from .qualidade import problema, verificar_produto
from .saldos import calcular_saldo


@dataclass
class Resultado:
    data_referencia: object
    produtos: list = field(default_factory=list)
    alertas: list = field(default_factory=list)
    qualidade: list = field(default_factory=list)
    sugestoes: list = field(default_factory=list)
    resumo: dict = field(default_factory=dict)

    def produto(self, chave):
        return next((p for p in self.produtos if p["chave"] == chave), None)


def _custo_medio(entradas: pd.DataFrame):
    """Média ponderada do preço por unidade base, só com entradas que têm preço."""
    com_preco = entradas.dropna(subset=["preco_base"])
    if com_preco.empty or com_preco["qtd_base"].sum() <= 0:
        return None
    return float((com_preco["preco_base"] * com_preco["qtd_base"]).sum() / com_preco["qtd_base"].sum())


def _resumir_produto(chave, grupo, data_ref, p):
    incluidas = grupo[grupo["incluida"]]
    saidas = incluidas[incluidas["tipo"] == "saida"]
    entradas = incluidas[incluidas["tipo"] == "entrada"]
    saldo = calcular_saldo(incluidas)
    consumo = estimar_consumo(saidas, incluidas["data"].min(), data_ref, p)
    c = consumo["consumo_diario"]
    if c and c > 0:
        cobertura = max(saldo["saldo"], 0.0) / c
    else:
        cobertura = None
    minimos = incluidas.dropna(subset=["minimo_base"])
    custo = _custo_medio(entradas)
    return {
        "chave": chave,
        "nome": grupo["nome"].iloc[0],
        "categoria": grupo["categoria"].iloc[0],
        "unidade": grupo["unidade_principal"].iloc[0],
        "saldo": saldo["saldo"],
        "lotes": saldo["lotes"],
        "negativo_em": saldo["negativo_em"],
        "menor_saldo": saldo["menor_saldo"],
        "minimo": float(minimos["minimo_base"].iloc[-1]) if not minimos.empty else None,
        "consumo": consumo,
        "cobertura": cobertura,
        "custo_medio": custo,
        "valor_estoque": max(saldo["saldo"], 0.0) * custo if custo is not None else None,
        "ultima_movimentacao": grupo["data"].max(),
        "serie": serie_semanal(saidas, data_ref),
        "saidas": saidas,
        "entradas": entradas,
    }


def _curva_abc(produtos, p):
    com_valor = sorted([x for x in produtos if x["valor_estoque"]], key=lambda x: -x["valor_estoque"])
    total = sum(x["valor_estoque"] for x in com_valor)
    acumulado = 0.0
    for x in produtos:
        x["classe_abc"] = None
        x["participacao_valor"] = 0.0
    for x in com_valor:
        inicio = acumulado / total
        acumulado += x["valor_estoque"]
        x["participacao_valor"] = x["valor_estoque"] / total
        # O item que cruza o corte ainda pertence à classe (ex.: o que leva de 70% a 85% é A).
        x["classe_abc"] = "A" if inicio < p.abc_corte_a else ("B" if inicio < p.abc_corte_b else "C")
    return total


def analisar(movs: pd.DataFrame, apelidos=None, fatores=None, data_ref=None, p=PADRAO,
             rejeitadas=None) -> Resultado:
    df, data_ref, futuras = preparar(movs, apelidos, fatores, data_ref)
    if df.empty:
        return Resultado(data_referencia=data_ref, resumo={"n_produtos": 0, "valor_total": 0.0,
                                                           "sem_preco": [], "severidades": {},
                                                           "futuras": futuras})
    produtos, qualidade = [], []
    grupos = dict(tuple(df.groupby("chave")))
    for chave, grupo in grupos.items():
        produtos.append(_resumir_produto(chave, grupo, data_ref, p))
    valor_total = _curva_abc(produtos, p)

    alertas = []
    for prod in produtos:
        qualidade += verificar_produto(prod, grupos[prod["chave"]], p)
        alertas += gerar_alertas(prod, p, data_ref)
    alertas.sort(key=lambda a: (-a.score, ORDEM_SEVERIDADE[a.severidade], a.produto))

    nomes = {prod["nome"]: prod["chave"] for prod in produtos}
    sugestoes = sugerir_unificacoes(nomes.keys(), rejeitadas)
    for s in sugestoes:
        s.chave_a, s.chave_b = nomes[s.nome_a], nomes[s.nome_b]
        qualidade.append(problema(
            "nome_duplicado", "Possível nome duplicado", f"{s.nome_a} / {s.nome_b}",
            f"'{s.nome_a}' e '{s.nome_b}' podem ser o mesmo produto ({s.motivo}). Confirme ou rejeite "
            "a unificação; o sistema não unifica sozinho."))
    if futuras:
        qualidade.append(problema(
            "movimentacao_futura", "Movimentações após a data de referência", "—",
            f"{futuras} movimentação(ões) com data posterior à data de referência "
            f"({data_ref:%d/%m/%Y}) foram ignoradas nesta análise."))

    sem_preco = [x["nome"] for x in produtos if x["custo_medio"] is None and x["saldo"] > 0]
    severidades = {s: sum(1 for a in alertas if a.severidade == s) for s in ORDEM_SEVERIDADE}
    resumo = {"n_produtos": len(produtos), "valor_total": valor_total, "sem_preco": sem_preco,
              "severidades": severidades, "futuras": futuras, "n_movimentacoes": len(df)}
    produtos.sort(key=lambda x: normalizar_texto(x["nome"]))
    return Resultado(data_ref, produtos, alertas, qualidade, sugestoes, resumo)
