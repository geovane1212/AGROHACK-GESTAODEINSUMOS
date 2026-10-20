"""Normalização e conversão de unidades.

- Mesma grandeza converte sempre: massa (g, kg, t → kg) e volume (mL, L → L).
- Unidades que dependem do produto (sc, un, rolo, galão, caixa...) só convertem
  se houver um fator explícito para aquele produto (ex.: Ureia: 1 sc = 50 kg).
- Sem fator, nada é somado com unidade diferente: a qualidade dos dados avisa.
"""

from .nomes import normalizar_texto

SINONIMOS = {
    "kg": "kg", "kgs": "kg", "quilo": "kg", "quilos": "kg", "kilo": "kg", "quilograma": "kg",
    "g": "g", "gr": "g", "grama": "g", "gramas": "g",
    "t": "t", "ton": "t", "tonelada": "t", "toneladas": "t",
    "ml": "mL", "mililitro": "mL", "mililitros": "mL",
    "l": "L", "lt": "L", "lts": "L", "litro": "L", "litros": "L",
    "sc": "sc", "saco": "sc", "sacos": "sc", "saca": "sc", "sacas": "sc",
    "un": "un", "und": "un", "unid": "un", "unidade": "un", "unidades": "un", "pc": "un",
    "peca": "un", "pecas": "un",
    "par": "par", "pares": "par",
    "rolo": "rolo", "rolos": "rolo",
    "galao": "galão", "galoes": "galão", "gl": "galão",
    "cx": "caixa", "caixa": "caixa", "caixas": "caixa",
    "m": "m", "metro": "m", "metros": "m",
    "pct": "pacote", "pacote": "pacote", "pacotes": "pacote",
    "balde": "balde", "baldes": "balde",
}

# unidade → (grandeza, fator para a unidade base)
GRANDEZA = {
    "g": ("massa", 0.001), "kg": ("massa", 1.0), "t": ("massa", 1000.0),
    "mL": ("volume", 0.001), "L": ("volume", 1.0),
}
BASE = {"massa": "kg", "volume": "L"}


def normalizar_unidade(unidade) -> str:
    chave = normalizar_texto(unidade).replace(" ", "")
    return SINONIMOS.get(chave, chave or "?")


def para_base(quantidade: float, unidade: str, fatores_produto=None):
    """Converte para a unidade base. Devolve (quantidade, unidade).

    `fatores_produto`: {unidade: (fator, unidade_destino)} só deste produto,
    ex.: {"sc": (50, "kg")}.
    """
    fatores_produto = fatores_produto or {}
    if unidade in fatores_produto:
        fator, destino = fatores_produto[unidade]
        quantidade, unidade = quantidade * fator, destino
    if unidade in GRANDEZA:
        grandeza, fator = GRANDEZA[unidade]
        return quantidade * fator, BASE[grandeza]
    return quantidade, unidade
