"""Acesso ao banco SQLite (módulo sqlite3 da biblioteca padrão)."""

import json
import sqlite3
from pathlib import Path

import pandas as pd
from flask import current_app, g

ESQUEMA = """
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT NOT NULL,
    categoria TEXT,
    unidade TEXT NOT NULL,
    quantidade REAL NOT NULL CHECK (quantidade > 0),
    estoque_minimo REAL,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    data TEXT NOT NULL,
    preco_unitario REAL,          -- NULL = preço ausente (nunca zero)
    lote TEXT,
    validade TEXT,                -- NULL = validade ausente
    fornecedor TEXT,
    destino TEXT,
    responsavel TEXT,
    origem TEXT NOT NULL,         -- simulado | importacao | manual
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Unificações confirmadas pelo usuário: chave normalizada do apelido → chave do produto canônico.
CREATE TABLE IF NOT EXISTS apelidos (
    apelido TEXT PRIMARY KEY,
    produto TEXT NOT NULL,
    nome_apelido TEXT,
    nome_produto TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Pares que o usuário disse NÃO serem o mesmo produto (não são sugeridos de novo).
CREATE TABLE IF NOT EXISTS rejeicoes (
    chave_a TEXT NOT NULL,
    chave_b TEXT NOT NULL,
    PRIMARY KEY (chave_a, chave_b)
);
-- Fatores de conversão por produto, ex.: ureia, sc → 50 kg.
CREATE TABLE IF NOT EXISTS fatores (
    produto TEXT NOT NULL,
    unidade TEXT NOT NULL,
    fator REAL NOT NULL CHECK (fator > 0),
    unidade_destino TEXT NOT NULL,
    nome_produto TEXT,
    PRIMARY KEY (produto, unidade)
);
CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT
);
-- Fotografia dos alertas após cada reanálise, para mostrar "o que mudou".
CREATE TABLE IF NOT EXISTS analises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    motivo TEXT NOT NULL,
    data_referencia TEXT,
    alertas TEXT NOT NULL
);
"""

CAMPOS_MOV = ["produto", "categoria", "unidade", "quantidade", "estoque_minimo", "tipo", "data",
              "preco_unitario", "lote", "validade", "fornecedor", "destino", "responsavel"]


def caminho_banco() -> Path:
    url = current_app.config["DATABASE_URL"]
    caminho = Path(url.removeprefix("sqlite:///"))
    if not caminho.is_absolute():
        caminho = Path(current_app.root_path).parent / caminho
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho


def conexao() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(caminho_banco())
        g.db.row_factory = sqlite3.Row
    return g.db


def fechar(_erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def criar_tabelas():
    conexao().executescript(ESQUEMA)


def apagar_tudo():
    db = conexao()
    for tabela in ("movimentacoes", "apelidos", "rejeicoes", "fatores", "analises"):
        db.execute(f"DELETE FROM {tabela}")
    # O contador de versão continua crescendo, para o cache nunca reaproveitar uma análise antiga.
    db.execute("DELETE FROM configuracoes WHERE chave != 'versao'")
    db.commit()


def _valor_sql(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)) or valor is pd.NaT:
        return None
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")
    return valor


def inserir_movimentacoes(df: pd.DataFrame, origem: str) -> int:
    linhas = [tuple(_valor_sql(r.get(c)) for c in CAMPOS_MOV) + (origem,) for r in df.to_dict("records")]
    db = conexao()
    db.executemany(
        f"INSERT INTO movimentacoes ({', '.join(CAMPOS_MOV)}, origem) "
        f"VALUES ({', '.join('?' * (len(CAMPOS_MOV) + 1))})", linhas)
    db.commit()
    return len(linhas)


def apagar_movimentacoes():
    conexao().execute("DELETE FROM movimentacoes")
    conexao().commit()


def carregar_movimentacoes() -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data, id", conexao())


def contar_movimentacoes(origem=None) -> int:
    if origem:
        return conexao().execute("SELECT COUNT(*) FROM movimentacoes WHERE origem = ?", (origem,)).fetchone()[0]
    return conexao().execute("SELECT COUNT(*) FROM movimentacoes").fetchone()[0]


def ler_config(chave, padrao=None):
    linha = conexao().execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,)).fetchone()
    return linha["valor"] if linha else padrao


def gravar_config(chave, valor):
    db = conexao()
    if valor is None:
        db.execute("DELETE FROM configuracoes WHERE chave = ?", (chave,))
    else:
        db.execute("INSERT INTO configuracoes (chave, valor) VALUES (?, ?) "
                   "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor", (chave, str(valor)))
    db.commit()


def listar_apelidos():
    return conexao().execute("SELECT * FROM apelidos ORDER BY nome_produto, nome_apelido").fetchall()


def gravar_apelido(apelido, produto, nome_apelido, nome_produto):
    db = conexao()
    db.execute("INSERT INTO apelidos (apelido, produto, nome_apelido, nome_produto) VALUES (?, ?, ?, ?) "
               "ON CONFLICT(apelido) DO UPDATE SET produto = excluded.produto, "
               "nome_produto = excluded.nome_produto", (apelido, produto, nome_apelido, nome_produto))
    # Quem apontava para o apelido passa a apontar para o novo produto canônico.
    db.execute("UPDATE apelidos SET produto = ?, nome_produto = ? WHERE produto = ?",
               (produto, nome_produto, apelido))
    db.commit()


def remover_apelido(apelido):
    conexao().execute("DELETE FROM apelidos WHERE apelido = ?", (apelido,))
    conexao().commit()


def listar_rejeicoes():
    return {(r["chave_a"], r["chave_b"]) for r in conexao().execute("SELECT * FROM rejeicoes")}


def gravar_rejeicao(a, b):
    conexao().execute("INSERT OR IGNORE INTO rejeicoes (chave_a, chave_b) VALUES (?, ?)", (a, b))
    conexao().commit()


def listar_fatores():
    return conexao().execute("SELECT * FROM fatores ORDER BY nome_produto, unidade").fetchall()


def gravar_fator(produto, unidade, fator, destino, nome_produto):
    conexao().execute(
        "INSERT INTO fatores (produto, unidade, fator, unidade_destino, nome_produto) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(produto, unidade) DO UPDATE SET fator = excluded.fator, "
        "unidade_destino = excluded.unidade_destino", (produto, unidade, fator, destino, nome_produto))
    conexao().commit()


def remover_fator(produto, unidade):
    conexao().execute("DELETE FROM fatores WHERE produto = ? AND unidade = ?", (produto, unidade))
    conexao().commit()


def gravar_analise(motivo, data_referencia, fotografia: dict):
    conexao().execute("INSERT INTO analises (motivo, data_referencia, alertas) VALUES (?, ?, ?)",
                      (motivo, data_referencia, json.dumps(fotografia, ensure_ascii=False)))
    conexao().commit()


def ultimas_analises(n=2):
    linhas = conexao().execute("SELECT * FROM analises ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [dict(l, alertas=json.loads(l["alertas"])) for l in linhas]
