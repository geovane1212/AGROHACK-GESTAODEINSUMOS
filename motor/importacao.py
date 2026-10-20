"""Importação de CSV/XLSX com mapeamento flexível de colunas.

O cabeçalho do arquivo é comparado (normalizado) com uma lista de sinônimos de cada
campo. O usuário confere e ajusta o mapeamento na tela antes de importar, então a base
oficial pode chegar com outros nomes de coluna sem precisar mudar o código.
"""

import io
import re

import pandas as pd

from .nomes import normalizar_texto
from .unidades import normalizar_unidade

CAMPOS = {
    "produto": ("Produto", True),
    "tipo": ("Tipo (entrada/saída)", True),
    "quantidade": ("Quantidade", True),
    "data": ("Data", True),
    "unidade": ("Unidade", True),
    "categoria": ("Categoria", False),
    "estoque_minimo": ("Estoque mínimo", False),
    "preco_unitario": ("Preço unitário", False),
    "lote": ("Lote", False),
    "validade": ("Validade", False),
    "fornecedor": ("Fornecedor", False),
    "destino": ("Destino da retirada", False),
    "responsavel": ("Responsável", False),
}

SINONIMOS = {
    "produto": ["produto", "item", "insumo", "descricao", "nome", "material", "nome do produto",
                "descricao do produto", "produto insumo"],
    "tipo": ["tipo", "tipo de movimentacao", "tipo movimentacao", "movimentacao", "operacao", "e s",
             "entrada saida", "natureza"],
    "quantidade": ["quantidade", "qtd", "qtde", "quant", "qt", "quantidade movimentada"],
    "data": ["data", "dt", "data movimentacao", "data da movimentacao", "data mov", "dia"],
    "unidade": ["unidade", "un", "und", "unid", "unidade de medida", "medida", "um"],
    "categoria": ["categoria", "grupo", "classe", "tipo de produto", "familia"],
    "estoque_minimo": ["estoque minimo", "minimo", "estoque min", "est minimo", "qtd minima",
                       "quantidade minima", "ponto de pedido"],
    "preco_unitario": ["preco", "preco unitario", "preco de aquisicao", "valor unitario", "custo",
                       "custo unitario", "preco un", "vl unitario", "valor"],
    "lote": ["lote", "numero do lote", "n lote", "lote numero"],
    "validade": ["validade", "data de validade", "vencimento", "data de vencimento", "venc",
                 "dt validade"],
    "fornecedor": ["fornecedor", "fornecedor nome", "fabricante", "origem"],
    "destino": ["destino", "destino da retirada", "aplicacao", "local", "talhao", "setor", "uso"],
    "responsavel": ["responsavel", "funcionario", "usuario", "operador", "requisitante"],
}

TIPOS = {
    "entrada": "entrada", "e": "entrada", "compra": "entrada", "recebimento": "entrada", "in": "entrada",
    "ent": "entrada",
    "saida": "saida", "s": "saida", "retirada": "saida", "consumo": "saida", "uso": "saida",
    "out": "saida", "sai": "saida", "baixa": "saida",
}


def ler_arquivo(conteudo: bytes, nome_arquivo: str) -> pd.DataFrame:
    """Lê CSV (separador e codificação detectados) ou XLSX, tudo como texto."""
    if nome_arquivo.lower().endswith((".xlsx", ".xlsm")):
        return pd.read_excel(io.BytesIO(conteudo), dtype=object)
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            texto = conteudo.decode(codificacao)
            break
        except UnicodeDecodeError:
            continue
    primeira = texto.splitlines()[0] if texto else ""
    separador = max([";", ",", "\t", "|"], key=primeira.count)
    return pd.read_csv(io.StringIO(texto), sep=separador, dtype=str, keep_default_na=False)


def _norm_cabecalho(coluna) -> str:
    return normalizar_texto(str(coluna).replace("_", " ").replace("/", " "))


def sugerir_mapeamento(colunas) -> dict:
    """{campo: coluna do arquivo}. Primeiro procura igualdade exata com um sinônimo."""
    mapa, usadas = {}, set()
    normalizadas = {c: _norm_cabecalho(c) for c in colunas}
    for campo, sinonimos in SINONIMOS.items():
        for coluna, norm in normalizadas.items():
            if coluna not in usadas and norm in sinonimos:
                mapa[campo] = coluna
                usadas.add(coluna)
                break
    return mapa


def parse_numero(valor):
    """'1.234,5' → 1234.5 ; '1,5' → 1.5 ; '1234.5' → 1234.5 ; vazio → None."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = re.sub(r"[^\d,.\-]", "", str(valor))
    if not texto or texto in "-.,":
        return None
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def parse_data(valor):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    if isinstance(valor, pd.Timestamp):
        return valor.normalize()
    if hasattr(valor, "year"):
        return pd.Timestamp(valor).normalize()
    texto = str(valor).strip()
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"]
    for formato in formatos:
        try:
            return pd.to_datetime(texto, format=formato).normalize()
        except ValueError:
            continue
    return None


def _texto(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    return texto or None


def aplicar_mapeamento(bruto: pd.DataFrame, mapa: dict):
    """Converte o arquivo para o formato interno. Devolve (válidas, erros, avisos).

    Linhas com erro em campo obrigatório são recusadas e listadas com o motivo.
    Preço e validade inválidos ou vazios viram ausentes (None), nunca zero.
    """
    faltando = [CAMPOS[c][0] for c, (_, obrig) in CAMPOS.items() if obrig and not mapa.get(c)]
    if faltando:
        return pd.DataFrame(), [f"Mapeie as colunas obrigatórias: {', '.join(faltando)}."], []

    validas, erros, avisos = [], [], []
    for i, linha in enumerate(bruto.to_dict("records"), start=2):  # linha 1 = cabeçalho
        pega = lambda campo: linha.get(mapa[campo]) if mapa.get(campo) else None  # noqa: E731
        problemas = []
        produto = _texto(pega("produto"))
        if not produto:
            problemas.append("produto vazio")
        tipo = TIPOS.get(normalizar_texto(pega("tipo")))
        if not tipo:
            problemas.append(f"tipo '{pega('tipo')}' não reconhecido (use entrada ou saída)")
        quantidade = parse_numero(pega("quantidade"))
        if quantidade is None or quantidade <= 0:
            problemas.append(f"quantidade '{pega('quantidade')}' inválida (deve ser maior que zero)")
        data = parse_data(pega("data"))
        if data is None:
            problemas.append(f"data '{pega('data')}' inválida")
        unidade = _texto(pega("unidade"))
        if not unidade:
            problemas.append("unidade vazia")
        if problemas:
            erros.append(f"Linha {i}: {'; '.join(problemas)}.")
            continue

        preco = parse_numero(pega("preco_unitario"))
        if preco is not None and preco <= 0:
            avisos.append(f"Linha {i}: preço {pega('preco_unitario')} tratado como ausente.")
            preco = None
        validade_bruta = _texto(pega("validade"))
        validade = parse_data(validade_bruta) if validade_bruta else None
        if validade_bruta and validade is None:
            avisos.append(f"Linha {i}: validade '{validade_bruta}' inválida, tratada como ausente.")
        minimo = parse_numero(pega("estoque_minimo"))
        validas.append({
            "produto": produto, "tipo": tipo, "quantidade": quantidade, "data": data,
            "unidade": normalizar_unidade(unidade), "categoria": _texto(pega("categoria")),
            "estoque_minimo": minimo, "preco_unitario": preco, "lote": _texto(pega("lote")),
            "validade": validade, "fornecedor": _texto(pega("fornecedor")),
            "destino": _texto(pega("destino")), "responsavel": _texto(pega("responsavel")),
        })
    return pd.DataFrame(validas), erros, avisos
