"""Rotas do sistema."""

import csv
import io
import uuid
from pathlib import Path

import pandas as pd
from flask import (Blueprint, Response, abort, current_app, flash, redirect, render_template, request,
                   url_for)

from motor import texto
from motor.alertas import ORDEM_SEVERIDADE
from motor.config import PADRAO
from motor.importacao import CAMPOS, aplicar_mapeamento, ler_arquivo, sugerir_mapeamento
from motor.nomes import normalizar_texto
from motor.unidades import GRANDEZA, normalizar_unidade

from . import db, servicos

bp = Blueprint("web", __name__)

CATEGORIAS = ["Fertilizantes", "Corretivos", "Sementes", "Defensivos e biológicos",
              "Combustíveis e lubrificantes", "Peças e manutenção", "Irrigação", "EPI e diversos"]
ICONES = {"Crítico": "⛔", "Atenção": "⚠️", "Informativo": "ℹ️"}
CLASSES = {"Crítico": "critico", "Atenção": "atencao", "Informativo": "informativo"}


@bp.app_context_processor
def contexto_global():
    resultado = servicos.analise_atual()
    return {
        "res": resultado,
        "data_ref_manual": servicos.data_referencia_configurada() is not None,
        "dados_simulados": db.contar_movimentacoes("simulado") > 0,
        "ICONES": ICONES, "CLASSES": CLASSES,
    }


# ------------------------------------------------------------------ painel e alertas
@bp.route("/")
def painel():
    res = servicos.analise_atual()
    mudancas = servicos.ultima_mudanca()
    por_categoria = {}
    for p in res.produtos:
        if p["valor_estoque"]:
            por_categoria[p["categoria"]] = por_categoria.get(p["categoria"], 0) + p["valor_estoque"]
    por_categoria = dict(sorted(por_categoria.items(), key=lambda x: -x[1]))
    cobertura = sorted([p for p in res.produtos if p["cobertura"] is not None],
                       key=lambda p: p["cobertura"])[:10]
    return render_template("painel.html", mudancas=mudancas, por_categoria=por_categoria,
                           cobertura=cobertura, a_vencer=_lotes_a_vencer(res)[:8])


def _lotes_a_vencer(res):
    lotes = []
    for p in res.produtos:
        for l in p["lotes"]:
            if pd.notna(l["validade"]):
                dias = (l["validade"] - res.data_referencia).days
                if dias <= PADRAO.vencimento_info_dias:
                    lotes.append({"produto": p["nome"], "chave": p["chave"], "lote": l["lote"],
                                  "validade": l["validade"], "dias": dias, "qtd": l["qtd"],
                                  "unidade": p["unidade"]})
    return sorted(lotes, key=lambda l: l["dias"])


def _filtrar_alertas(res, args):
    alertas = res.alertas
    if args.get("severidade"):
        alertas = [a for a in alertas if a.severidade == args["severidade"]]
    if args.get("categoria"):
        alertas = [a for a in alertas if a.categoria == args["categoria"]]
    if args.get("tipo"):
        alertas = [a for a in alertas if a.tipo == args["tipo"]]
    return alertas


@bp.route("/alertas")
def alertas():
    res = servicos.analise_atual()
    categorias = sorted({a.categoria for a in res.alertas})
    tipos = sorted({(a.tipo, a.titulo) for a in res.alertas}, key=lambda x: x[1])
    tipos = list({t: n for t, n in tipos}.items())
    return render_template("alertas.html", alertas=_filtrar_alertas(res, request.args),
                           categorias=categorias, tipos=tipos, filtros=request.args)


@bp.route("/alertas.csv")
def alertas_csv():
    res = servicos.analise_atual()
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["prioridade", "severidade", "alerta", "produto", "categoria", "justificativa",
                       "regra", "limite"])
    for a in _filtrar_alertas(res, request.args):
        escritor.writerow([a.score, a.severidade, a.titulo, a.produto, a.categoria, a.mensagem,
                           a.regra, a.limite])
    nome = f"alertas_{res.data_referencia:%Y-%m-%d}.csv"
    return Response("﻿" + saida.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nome}"})


# ------------------------------------------------------------------ produtos
@bp.route("/produtos")
def produtos():
    res = servicos.analise_atual()
    lista = res.produtos
    if request.args.get("categoria"):
        lista = [p for p in lista if p["categoria"] == request.args["categoria"]]
    ordem = request.args.get("ordem", "nome")
    if ordem == "cobertura":
        lista = sorted(lista, key=lambda p: (p["cobertura"] is None, p["cobertura"] or 0))
    elif ordem == "valor":
        lista = sorted(lista, key=lambda p: -(p["valor_estoque"] or 0))
    contagem = {}
    for a in res.alertas:
        atual = contagem.get(a.chave_produto)
        if atual is None or ORDEM_SEVERIDADE[a.severidade] < ORDEM_SEVERIDADE[atual]:
            contagem[a.chave_produto] = a.severidade
    categorias = sorted({p["categoria"] for p in res.produtos})
    return render_template("produtos.html", produtos=lista, ordem=ordem, pior=contagem,
                           categorias=categorias, filtros=request.args)


@bp.route("/produto/<path:chave>")
def produto(chave):
    res = servicos.analise_atual()
    prod = res.produto(chave)
    if prod is None:
        abort(404)
    alertas = [a for a in res.alertas if a.chave_produto == chave]
    movs = db.carregar_movimentacoes()
    movs = movs[movs["produto"].map(normalizar_texto).isin(
        {normalizar_texto(g) for g in prod.get("grafias", [prod["nome"]])})]
    movs = movs.sort_values(["data", "id"], ascending=False).head(40).to_dict("records")
    qualidade = [q for q in res.qualidade if q.get("chave_produto") == chave]
    return render_template("produto.html", p=prod, alertas=alertas, movs=movs, qualidade=qualidade)


@bp.route("/movimentacoes")
def movimentacoes():
    movs = db.carregar_movimentacoes().sort_values(["data", "id"], ascending=False)
    busca = request.args.get("q", "").strip()
    if busca:
        movs = movs[movs["produto"].map(normalizar_texto).str.contains(normalizar_texto(busca), regex=False)]
    return render_template("movimentacoes.html", movs=movs.head(300).to_dict("records"), total=len(movs),
                           busca=busca)


# ------------------------------------------------------------------ cadastro manual
@bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    res = servicos.analise_atual()
    if request.method == "POST":
        form = {c: request.form.get(c, "").strip() for c in CAMPOS}
        linha = pd.DataFrame([form])
        validas, erros, avisos = aplicar_mapeamento(linha, {c: c for c in CAMPOS})
        if erros:
            for e in erros:
                flash(e.replace("Linha 2: ", "Não foi possível salvar: "), "erro")
            return render_template("registrar.html", form=form, categorias=CATEGORIAS), 400
        db.inserir_movimentacoes(validas, "manual")
        for a in avisos:
            flash(a.replace("Linha 2: ", ""), "aviso")
        tipo = "Entrada" if validas.iloc[0]["tipo"] == "entrada" else "Saída"
        motivo = f"{tipo} registrada: {texto.num(validas.iloc[0]['quantidade'])} {validas.iloc[0]['unidade']} " \
                 f"de {validas.iloc[0]['produto']}"
        servicos.reanalisar(motivo)
        flash(f"{motivo}. Alertas recalculados.", "ok")
        return redirect(url_for("web.painel"))
    data_padrao = res.data_referencia.strftime("%Y-%m-%d") if res.data_referencia is not None else ""
    form = {"data": data_padrao, "tipo": "saida", "produto": request.args.get("produto", "")}
    prod = next((p for p in res.produtos if p["nome"] == form["produto"]), None)
    if prod:
        form.update(unidade=prod["unidade"], categoria=prod["categoria"])
    return render_template("registrar.html", form=form, categorias=CATEGORIAS)


# ------------------------------------------------------------------ importação
def _pasta_uploads() -> Path:
    pasta = db.caminho_banco().parent / "uploads"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


@bp.route("/importar", methods=["GET", "POST"])
def importar():
    if request.method == "GET":
        return render_template("importar.html", campos=CAMPOS)
    arquivo = request.files.get("arquivo")
    if not arquivo or not arquivo.filename:
        flash("Escolha um arquivo CSV ou XLSX.", "erro")
        return redirect(url_for("web.importar"))
    extensao = Path(arquivo.filename).suffix.lower()
    if extensao not in (".csv", ".xlsx", ".xlsm", ".txt"):
        flash("Formato não suportado. Use CSV ou XLSX.", "erro")
        return redirect(url_for("web.importar"))
    token = uuid.uuid4().hex + extensao
    caminho = _pasta_uploads() / token
    arquivo.save(caminho)
    try:
        bruto = ler_arquivo(caminho.read_bytes(), caminho.name)
    except Exception as erro:  # arquivo corrompido ou em formato inesperado
        caminho.unlink(missing_ok=True)
        flash(f"Não foi possível ler o arquivo: {erro}", "erro")
        return redirect(url_for("web.importar"))
    return render_template("mapear.html", token=token, nome=arquivo.filename, colunas=list(bruto.columns),
                           mapa=sugerir_mapeamento(bruto.columns), campos=CAMPOS,
                           previa=bruto.head(5).fillna("").to_dict("records"), total=len(bruto))


@bp.route("/importar/confirmar", methods=["POST"])
def importar_confirmar():
    token = Path(request.form.get("token", "")).name
    caminho = _pasta_uploads() / token
    if not token or not caminho.exists():
        flash("O arquivo enviado expirou. Envie de novo.", "erro")
        return redirect(url_for("web.importar"))
    mapa = {c: request.form.get(f"campo_{c}") or None for c in CAMPOS}
    substituir = request.form.get("substituir") == "1"
    bruto = ler_arquivo(caminho.read_bytes(), caminho.name)
    n, erros, avisos = servicos.importar_dataframe(bruto, "importacao", substituir, mapa)
    if n == 0:
        for e in erros[:10]:
            flash(e, "erro")
        return render_template("mapear.html", token=token, nome=request.form.get("nome"),
                               colunas=list(bruto.columns), mapa=mapa, campos=CAMPOS,
                               previa=bruto.head(5).fillna("").to_dict("records"), total=len(bruto)), 400
    caminho.unlink(missing_ok=True)
    motivo = f"Importação de {request.form.get('nome')}: {n} movimentação(ões)" + \
             (" (dados anteriores substituídos)" if substituir else "")
    mudancas = servicos.reanalisar(motivo)
    return render_template("importado.html", n=n, erros=erros, avisos=avisos, motivo=motivo,
                           mudancas=mudancas)


# ------------------------------------------------------------------ qualidade dos dados
@bp.route("/qualidade")
def qualidade():
    res = servicos.analise_atual()
    grupos = {}
    for q in res.qualidade:
        grupos.setdefault(q["titulo"], []).append(q)
    inconsistentes = [q for q in res.qualidade if q["tipo"] == "unidade_inconsistente"]
    return render_template("qualidade.html", grupos=grupos, sugestoes=res.sugestoes,
                           apelidos=db.listar_apelidos(), fatores=db.listar_fatores(),
                           inconsistentes=inconsistentes, unidades_base=sorted(set(GRANDEZA) | {"un"}))


@bp.route("/qualidade/unificar", methods=["POST"])
def unificar():
    res = servicos.analise_atual()
    canonico = request.form["canonico"]
    outro = request.form["outro"]
    p_canon, p_outro = res.produto(canonico), res.produto(outro)
    if not p_canon or not p_outro or canonico == outro:
        flash("Produtos não encontrados. Atualize a página.", "erro")
        return redirect(url_for("web.qualidade"))
    db.gravar_apelido(outro, canonico, p_outro["nome"], p_canon["nome"])
    motivo = f"Unificação confirmada: '{p_outro['nome']}' passa a ser '{p_canon['nome']}'"
    servicos.reanalisar(motivo)
    flash(motivo + ". Alertas recalculados.", "ok")
    return redirect(url_for("web.qualidade"))


@bp.route("/qualidade/rejeitar", methods=["POST"])
def rejeitar():
    db.gravar_rejeicao(request.form["a"], request.form["b"])
    motivo = "Sugestão de unificação rejeitada"
    servicos.reanalisar(motivo)
    flash("Sugestão rejeitada: esses nomes continuam como produtos diferentes.", "ok")
    return redirect(url_for("web.qualidade"))


@bp.route("/qualidade/apelido/remover", methods=["POST"])
def remover_apelido():
    db.remover_apelido(request.form["apelido"])
    motivo = "Unificação desfeita"
    servicos.reanalisar(motivo)
    flash("Unificação desfeita.", "ok")
    return redirect(url_for("web.qualidade"))


@bp.route("/qualidade/fator", methods=["POST"])
def gravar_fator():
    res = servicos.analise_atual()
    chave = request.form.get("produto", "")
    prod = res.produto(chave)
    unidade = normalizar_unidade(request.form.get("unidade", ""))
    destino = normalizar_unidade(request.form.get("destino", ""))
    try:
        fator = float(request.form.get("fator", "").replace(",", "."))
    except ValueError:
        fator = 0
    if not prod or fator <= 0 or not unidade or not destino or unidade == destino:
        flash("Informe produto, unidade, fator maior que zero e unidade de destino diferente.", "erro")
        return redirect(url_for("web.qualidade"))
    db.gravar_fator(chave, unidade, fator, destino, prod["nome"])
    motivo = f"Fator cadastrado: {prod['nome']}, 1 {unidade} = {texto.num(fator)} {destino}"
    servicos.reanalisar(motivo)
    flash(motivo + ". Alertas recalculados.", "ok")
    return redirect(url_for("web.qualidade"))


@bp.route("/qualidade/fator/remover", methods=["POST"])
def remover_fator():
    db.remover_fator(request.form["produto"], request.form["unidade"])
    motivo = "Fator de conversão removido"
    servicos.reanalisar(motivo)
    flash(motivo + ".", "ok")
    return redirect(url_for("web.qualidade"))


# ------------------------------------------------------------------ configuração
@bp.route("/data-referencia", methods=["POST"])
def data_referencia():
    valor = request.form.get("data_referencia", "").strip()
    if request.form.get("acao") == "automatica" or not valor:
        db.gravar_config("data_referencia", None)
        motivo = "Data de referência voltou para a última movimentação"
    else:
        try:
            pd.Timestamp(valor)
        except ValueError:
            flash("Data inválida.", "erro")
            return redirect(request.referrer or url_for("web.painel"))
        db.gravar_config("data_referencia", valor)
        motivo = f"Data de referência alterada para {pd.Timestamp(valor):%d/%m/%Y}"
    servicos.reanalisar(motivo)
    flash(motivo + ".", "ok")
    return redirect(request.referrer or url_for("web.painel"))


@bp.route("/demo/restaurar", methods=["POST"])
def restaurar_demo():
    n = servicos.carregar_demo()
    flash(f"Base de demonstração restaurada: {n} movimentações simuladas.", "ok")
    return redirect(url_for("web.painel"))


@bp.route("/como-funciona")
def como_funciona():
    return render_template("como_funciona.html", p=PADRAO)


@bp.app_errorhandler(404)
def nao_encontrado(_erro):
    return render_template("erro.html", mensagem="Página não encontrada."), 404


@bp.app_errorhandler(413)
def muito_grande(_erro):
    current_app.logger.info("Arquivo acima do limite")
    return render_template("erro.html", mensagem="Arquivo muito grande (limite de 10 MB)."), 413
