"""Consumo médio, confiança da estimativa, cobertura e série histórica."""

from datetime import timedelta

import pandas as pd


def confianca(n_saidas: int, p) -> str | None:
    """Nível de confiança pelo nº de saídas nos últimos 60 dias (None = sem estimativa)."""
    if n_saidas >= p.confianca_alta:
        return "alta"
    if n_saidas >= p.confianca_media:
        return "média"
    if n_saidas >= p.confianca_minima:
        return "baixa"
    return None


def estimar_consumo(saidas: pd.DataFrame, primeira_data, data_ref, p) -> dict:
    """Consumo médio diário recente.

    Usa a janela de 30 dias se nela houver pelo menos 5 saídas; senão, 60 dias.
    Se o produto começou a ser movimentado há menos tempo que a janela, divide pelos
    dias desde a primeira movimentação (para não subestimar produtos novos).
    """
    idade = lambda d: (data_ref - saidas["data"]).dt.days < d  # noqa: E731
    n60 = int(idade(p.janela_longa_dias).sum())
    n30 = int(idade(p.janela_curta_dias).sum())
    nivel = confianca(n60, p)
    resultado = {"n_saidas_60": n60, "confianca": nivel, "consumo_diario": None, "janela": None}
    if nivel is None:
        return resultado
    janela = p.janela_curta_dias if n30 >= p.min_saidas_janela_curta else p.janela_longa_dias
    dias_base = max(1, min(janela, (data_ref - primeira_data).days + 1))
    total = float(saidas.loc[idade(janela), "qtd_base"].sum())
    resultado.update(consumo_diario=total / dias_base, janela=janela, dias_base=dias_base,
                     total_janela=total)
    return resultado


def soma_periodo(saidas: pd.DataFrame, data_ref, inicio_dias: int, fim_dias: int):
    """Soma e contagem das saídas com idade em [inicio_dias, fim_dias) dias."""
    idade = (data_ref - saidas["data"]).dt.days
    sel = saidas[(idade >= inicio_dias) & (idade < fim_dias)]
    return float(sel["qtd_base"].sum()), len(sel)


def serie_semanal(saidas: pd.DataFrame, data_ref, semanas: int = 26) -> list:
    """Consumo por semana (semanas terminando na data de referência), da mais antiga à mais recente."""
    serie = []
    idade = (data_ref - saidas["data"]).dt.days
    for i in range(semanas - 1, -1, -1):
        fim = data_ref - timedelta(days=7 * i)
        total = float(saidas.loc[(idade >= 7 * i) & (idade < 7 * (i + 1)), "qtd_base"].sum())
        serie.append({"semana": fim.strftime("%d/%m"), "total": round(total, 2)})
    return serie
