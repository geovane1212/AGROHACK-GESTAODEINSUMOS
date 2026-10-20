"""Unificação de nomes (só sugestão) e conversão de unidades."""

import pytest

from motor.nomes import motivo_bloqueio, normalizar_texto, sugerir_unificacoes
from motor.unidades import normalizar_unidade, para_base


def test_normaliza_maiusculas_acentos_e_espacos():
    assert normalizar_texto("  Óleo   HIDRÁULICO ") == "oleo hidraulico"
    assert normalizar_texto("Oleo hidraulico") == normalizar_texto("ÓLEO HIDRÁULICO")


@pytest.mark.parametrize("a, b", [
    ("Ureia", "UREIA 45%"),
    ("Ureia", "ureia granulada"),
    ("UREIA 45%", "ureia granulada"),
    ("Luva nitrílica", "Luvas nitrilicas"),
])
def test_sugere_grafias_do_mesmo_produto(a, b):
    sugestoes = sugerir_unificacoes([a, b])
    assert len(sugestoes) == 1


@pytest.mark.parametrize("a, b", [
    ("NPK 04-14-08", "NPK 04-30-16"),
    ("NPK 10-10-10", "NPK 04-14-08"),
    ("Filtro de óleo", "Filtro de ar"),
    ("Óleo de motor 15W40", "Óleo hidráulico"),
    ("Semente de milho", "Semente de soja"),
])
def test_nao_sugere_formulacoes_ou_especificacoes_diferentes(a, b):
    assert motivo_bloqueio(a, b) is not None
    assert sugerir_unificacoes([a, b]) == []


def test_par_rejeitado_nao_volta_a_ser_sugerido():
    rejeitados = {(normalizar_texto("Ureia"), normalizar_texto("UREIA 45%"))}
    assert sugerir_unificacoes(["Ureia", "UREIA 45%"], rejeitados) == []


def test_mesma_grandeza_converte():
    assert para_base(500, "g") == (0.5, "kg")
    assert para_base(2, "t") == (2000, "kg")
    assert para_base(250, "mL") == (0.25, "L")


def test_unidade_do_produto_so_converte_com_fator():
    assert para_base(2, "sc") == (2, "sc")
    assert para_base(2, "sc", {"sc": (50, "kg")}) == (100, "kg")


def test_sinonimos_de_unidade():
    assert normalizar_unidade("Litros") == "L"
    assert normalizar_unidade("KG") == "kg"
    assert normalizar_unidade("saco") == "sc"
    assert normalizar_unidade("unid") == "un"
