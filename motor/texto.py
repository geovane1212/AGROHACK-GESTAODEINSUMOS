"""Formatação de números, datas e valores no padrão brasileiro."""

import math


def num(valor, casas=None) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    if casas is None:
        casas = 0 if abs(valor) >= 100 or float(valor).is_integer() else 1
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda(valor) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    return "R$ " + num(valor, 2)


def data(valor) -> str:
    if valor is None:
        return "—"
    try:
        return valor.strftime("%d/%m/%Y")
    except (AttributeError, ValueError):
        return "—"


def qtd(valor, unidade) -> str:
    return f"{num(valor)} {unidade}"


def dias(valor) -> str:
    n = round(valor)
    return "1 dia" if n == 1 else f"{n} dias"
