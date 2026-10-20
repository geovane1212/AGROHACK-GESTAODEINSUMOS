"""Normalização de nomes de produtos e SUGESTÃO de unificações.

Regra de ouro: o sistema nunca unifica produtos sozinho. Ele só sugere; o usuário
confirma e a confirmação vira um apelido (alias → produto canônico).

A única equivalência automática é quando dois nomes ficam idênticos depois de
normalizar maiúsculas, acentos, pontuação e espaços ("Óleo  hidráulico" = "oleo hidraulico"):
essas diferenças não mudam o produto.
"""

import re
import unicodedata
from dataclasses import dataclass
from itertools import combinations

from rapidfuzz import fuzz

# Palavras que só descrevem a apresentação e não mudam o produto.
PALAVRAS_DESCRITIVAS = {
    "de", "da", "do", "das", "dos", "para", "com", "e", "em",
    "granulado", "granulada", "agricola", "liquido", "liquida", "po",
    "comum", "tipo", "saco", "sc", "kg", "l", "litro", "litros", "gr", "un",
}

SIMILARIDADE_MINIMA = 85   # rapidfuzz, 0 a 100
SIMILARIDADE_ERRO_DIGITACAO = 85

_TOKEN = re.compile(r"\d+(?:[-./,]\d+)*%?|[a-z]+")


def normalizar_texto(texto) -> str:
    """Minúsculas, sem acentos, sem pontuação solta e com espaços simples."""
    if texto is None:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return " ".join(_TOKEN.findall(texto))


def _eh_numero(token: str) -> bool:
    return token[0].isdigit()


def numeros(nome: str) -> set:
    """Números e formulações do nome: '45%' → '45', 'NPK 04-14-08' → '04-14-08'."""
    return {t.rstrip("%").replace(",", ".") for t in normalizar_texto(nome).split() if _eh_numero(t)}


def nucleo(nome: str) -> set:
    """Palavras que identificam o produto (sem números e sem palavras descritivas)."""
    return {t for t in normalizar_texto(nome).split()
            if not _eh_numero(t) and t not in PALAVRAS_DESCRITIVAS}


@dataclass
class Sugestao:
    nome_a: str
    nome_b: str
    similaridade: int
    motivo: str


def motivo_bloqueio(a: str, b: str):
    """Diz por que dois nomes NÃO podem ser o mesmo produto, ou None se podem."""
    na, nb = numeros(a), numeros(b)
    if na and nb and na != nb:
        return f"números/formulações diferentes ({', '.join(sorted(na))} x {', '.join(sorted(nb))})"
    ca, cb = nucleo(a), nucleo(b)
    if not ca or not cb:
        return "nome sem palavra identificadora"
    so_a, so_b = ca - cb, cb - ca
    if so_a and so_b:
        # Cada lado tem uma palavra que o outro não tem: só aceita se forem erros de digitação
        # ("luva" x "luvas"), nunca palavras diferentes ("oleo" x "ar").
        for t in so_a:
            if max(fuzz.ratio(t, u) for u in so_b) < SIMILARIDADE_ERRO_DIGITACAO:
                return f"especificação diferente ('{t}' x '{', '.join(sorted(so_b))}')"
    return None


def similaridade(a: str, b: str) -> int:
    ca, cb = nucleo(a), nucleo(b)
    if ca <= cb or cb <= ca:
        return 100
    return round(fuzz.token_sort_ratio(" ".join(sorted(ca)), " ".join(sorted(cb))))


def sugerir_unificacoes(nomes, ja_unificados=None) -> list:
    """Compara todos os pares de nomes (já agrupados) e devolve sugestões ordenadas.

    `ja_unificados` é um conjunto de pares de chaves normalizadas que já são o mesmo
    produto (por apelido) ou que o usuário rejeitou; eles não são sugeridos de novo.
    """
    ja_unificados = ja_unificados or set()
    unicos = sorted({n for n in nomes if n}, key=normalizar_texto)
    sugestoes = []
    for a, b in combinations(unicos, 2):
        ka, kb = normalizar_texto(a), normalizar_texto(b)
        if ka == kb or (ka, kb) in ja_unificados or (kb, ka) in ja_unificados:
            continue
        if motivo_bloqueio(a, b):
            continue
        s = similaridade(a, b)
        if s >= SIMILARIDADE_MINIMA:
            if s == 100:
                motivo = "um nome contém o outro, diferindo só em números ou palavras descritivas"
            else:
                motivo = f"nomes muito parecidos (similaridade {s}%)"
            sugestoes.append(Sugestao(a, b, s, motivo))
    return sorted(sugestoes, key=lambda x: -x.similaridade)
