"""Liga o banco ao motor: monta as entradas, roda a análise e registra a reanálise."""

import os
from pathlib import Path

import pandas as pd
from flask import current_app

from motor.analise import analisar
from motor.importacao import aplicar_mapeamento, ler_arquivo, sugerir_mapeamento
from motor.mudancas import comparar, fotografar

from . import db

ARQUIVO_SIMULADO = Path(__file__).resolve().parent.parent / "data" / "simulado" / "movimentacoes_simulado.csv"

# Cache da última análise: só recalcula quando os dados ou configurações mudam.
_cache = {"versao": None, "resultado": None}


def versao_atual() -> str:
    return db.ler_config("versao", "0")


def data_referencia_configurada():
    """Data escolhida pelo usuário (ou pela variável DATA_REFERENCIA); None = última movimentação."""
    valor = db.ler_config("data_referencia") or os.environ.get("DATA_REFERENCIA") or None
    return pd.Timestamp(valor) if valor else None


def entradas_da_analise():
    apelidos = {a["apelido"]: a["produto"] for a in db.listar_apelidos()}
    fatores = {(f["produto"], f["unidade"]): (f["fator"], f["unidade_destino"]) for f in db.listar_fatores()}
    return apelidos, fatores, data_referencia_configurada(), db.listar_rejeicoes()


def analise_atual():
    versao = versao_atual()
    if _cache["versao"] != versao or _cache.get("banco") != str(db.caminho_banco()):
        apelidos, fatores, data_ref, rejeitadas = entradas_da_analise()
        resultado = analisar(db.carregar_movimentacoes(), apelidos, fatores, data_ref,
                             rejeitadas=rejeitadas)
        _cache.update(versao=versao, resultado=resultado, banco=str(db.caminho_banco()))
    return _cache["resultado"]


def reanalisar(motivo: str) -> dict:
    """Chamado depois de QUALQUER mudança: recalcula, guarda a fotografia e devolve o que mudou."""
    db.gravar_config("versao", int(versao_atual()) + 1)
    resultado = analise_atual()
    anterior = db.ultimas_analises(1)
    foto = fotografar(resultado.alertas)
    ref = resultado.data_referencia.strftime("%Y-%m-%d") if resultado.data_referencia is not None else None
    db.gravar_analise(motivo, ref, foto)
    return comparar(anterior[0]["alertas"] if anterior else {}, foto)


def ultima_mudanca():
    analises = db.ultimas_analises(2)
    if len(analises) < 2:
        return None
    return {"motivo": analises[0]["motivo"], "quando": analises[0]["criado_em"],
            **comparar(analises[1]["alertas"], analises[0]["alertas"])}


def importar_dataframe(bruto: pd.DataFrame, origem: str, substituir=False, mapa=None):
    mapa = mapa or sugerir_mapeamento(bruto.columns)
    validas, erros, avisos = aplicar_mapeamento(bruto, mapa)
    if validas.empty:
        return 0, erros, avisos
    if substituir:
        db.apagar_movimentacoes()
    return db.inserir_movimentacoes(validas, origem), erros, avisos


def carregar_demo():
    """Apaga tudo e carrega a base SIMULADA (usado no primeiro início e no botão de restaurar)."""
    db.apagar_tudo()
    bruto = ler_arquivo(ARQUIVO_SIMULADO.read_bytes(), ARQUIVO_SIMULADO.name)
    n, erros, _ = importar_dataframe(bruto, "simulado")
    if erros:
        current_app.logger.warning("Base simulada com %d linha(s) recusada(s)", len(erros))
    reanalisar("Carga da base de demonstração (dados simulados)")
    return n


def iniciar_banco(app):
    with app.app_context():
        db.criar_tabelas()
        if db.contar_movimentacoes() == 0 and app.config["SEED_DEMO"]:
            carregar_demo()
        db.fechar()
