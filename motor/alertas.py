"""Regras de alerta.

Cada regra recebe o resumo de um produto (`prod`, montado em analise.py) e devolve
uma lista de Alerta. Todo alerta traz: severidade, justificativa com os números
usados, a regra aplicada, o limite da estimativa e um score de prioridade explicável.
"""

from dataclasses import dataclass, field

import pandas as pd

from . import texto as t
from .consumo import soma_periodo

CRITICO, ATENCAO, INFORMATIVO = "Crítico", "Atenção", "Informativo"
ORDEM_SEVERIDADE = {CRITICO: 0, ATENCAO: 1, INFORMATIVO: 2}
PESO_SEVERIDADE = {CRITICO: 100, ATENCAO: 50, INFORMATIVO: 10}


@dataclass
class Alerta:
    tipo: str
    titulo: str
    severidade: str
    produto: str
    chave_produto: str
    categoria: str
    mensagem: str
    regra: str
    limite: str
    confianca: str | None = None
    score: int = 0
    score_partes: list = field(default_factory=list)
    dados: dict = field(default_factory=dict)

    @property
    def chave(self) -> str:
        return f"{self.tipo}|{self.chave_produto}"


def prioridade(severidade, dias=None, valor=None, confianca=None):
    """Score = peso da severidade + urgência + valor envolvido − incerteza."""
    score = PESO_SEVERIDADE[severidade]
    partes = [f"{score} pela severidade ({severidade})"]
    if dias is not None:
        urgencia = max(0, 30 - round(max(dias, 0)))
        if urgencia:
            score += urgencia
            partes.append(f"+{urgencia} pela urgência ({t.dias(max(dias, 0))})")
    if valor:
        financeiro = min(20, round(valor / 500))
        if financeiro:
            score += financeiro
            partes.append(f"+{financeiro} pelo valor envolvido ({t.moeda(valor)})")
    if confianca == "baixa":
        score -= 10
        partes.append("−10 por baixa confiança da estimativa")
    return score, partes


def texto_confianca(consumo: dict) -> str:
    n = consumo["n_saidas_60"]
    nivel = consumo["confianca"]
    if nivel is None:
        return f"Sem estimativa de consumo: só {n} saída(s) nos últimos 60 dias (mínimo 2)."
    if nivel == "baixa":
        return f"Baixa confiança: só {n} saídas registradas nos últimos 60 dias."
    return f"Confiança {nivel}: {n} saídas nos últimos 60 dias."


def _novo(prod, tipo, titulo, severidade, mensagem, regra, limite, dias=None, valor=None,
          confianca=None, dados=None):
    score, partes = prioridade(severidade, dias, valor, confianca)
    return Alerta(tipo=tipo, titulo=titulo, severidade=severidade, produto=prod["nome"],
                  chave_produto=prod["chave"], categoria=prod["categoria"], mensagem=mensagem,
                  regra=regra, limite=limite, confianca=confianca, score=score,
                  score_partes=partes, dados=dados or {})


def _frase_consumo(prod):
    c = prod["consumo"]
    return (f"{t.num(c['consumo_diario'], 2 if c['consumo_diario'] < 10 else None)} "
            f"{prod['unidade']}/dia nos últimos {c['janela']} dias")


def regra_estoque_critico(prod, p):
    saldo, minimo, cob = prod["saldo"], prod["minimo"], prod["cobertura"]
    c, u = prod["consumo"], prod["unidade"]
    tem_consumo = c["consumo_diario"] is not None and c["consumo_diario"] > 0
    severidade = None
    frases = []

    if saldo <= 0 and (tem_consumo or minimo):
        severidade = CRITICO
        frases.append(f"o saldo calculado é {t.qtd(saldo, u)} (sem estoque).")
    elif tem_consumo and cob is not None and cob <= p.cobertura_atencao_dias:
        severidade = CRITICO if cob <= p.cobertura_critica_dias else ATENCAO
        frases.append(f"mantendo o consumo médio recente ({_frase_consumo(prod)}), o saldo atual "
                      f"({t.qtd(saldo, u)}) poderá ser suficiente por aproximadamente {t.dias(cob)}.")
    if minimo and saldo <= minimo:
        severidade = CRITICO
        if not frases:
            frases.append(f"o saldo atual ({t.qtd(saldo, u)}) está "
                          f"{'abaixo do' if saldo < minimo else 'igual ao'} estoque mínimo "
                          f"({t.qtd(minimo, u)}).")
            if tem_consumo and cob is not None:
                frases.append(f"Com o consumo médio recente ({_frase_consumo(prod)}), deve durar "
                              f"cerca de {t.dias(cob)}.")
        else:
            frases.append(f"O estoque mínimo cadastrado é {t.qtd(minimo, u)}.")
    if severidade is None:
        return []

    titulo = "Estoque crítico" if severidade == CRITICO else "Estoque baixo"
    mensagem = f"{titulo}: " + " ".join(frases) + " " + texto_confianca(c)
    return [_novo(
        prod, "estoque_critico", titulo, severidade, mensagem,
        regra=(f"Crítico se o saldo ≤ estoque mínimo ou se a cobertura ≤ {p.cobertura_critica_dias} "
               f"dias; Atenção se a cobertura ≤ {p.cobertura_atencao_dias} dias. "
               "Cobertura = saldo ÷ consumo médio diário recente."),
        limite=("Supõe que o consumo futuro será igual ao recente. Não considera compras feitas e "
                "ainda não registradas nem mudanças de fase da safra."),
        dias=0 if saldo <= 0 else cob, confianca=c["confianca"],
        dados={"saldo": saldo, "minimo": minimo, "cobertura_dias": cob,
               "consumo_diario": c["consumo_diario"]},
    )]


def regra_vencimento(prod, p, data_ref):
    lotes = sorted([l for l in prod["lotes"] if pd.notna(l["validade"])], key=lambda l: l["validade"])
    if not lotes:
        return []
    c = prod["consumo"]["consumo_diario"] or 0.0
    u, custo = prod["unidade"], prod["custo_medio"]
    consumido = 0.0
    em_risco = []
    for lote in lotes:
        dias = (lote["validade"] - data_ref).days
        if dias < 0:
            em_risco.append({**lote, "dias": dias, "usado": 0.0, "sobra": lote["qtd"], "sev": CRITICO})
            continue
        # FEFO: o consumo previsto até a validade vai primeiro para os lotes que vencem antes.
        usado = min(lote["qtd"], max(0.0, c * dias - consumido))
        consumido += usado
        sobra = lote["qtd"] - usado
        if sobra <= 1e-6 or dias > p.vencimento_info_dias:
            continue
        if dias <= p.vencimento_critico_dias:
            sev = CRITICO
        elif dias <= p.vencimento_atencao_dias:
            sev = ATENCAO
        else:
            sev = INFORMATIVO
        em_risco.append({**lote, "dias": dias, "usado": usado, "sobra": sobra, "sev": sev})
    if not em_risco:
        return []

    em_risco.sort(key=lambda l: (ORDEM_SEVERIDADE[l["sev"]], l["dias"]))
    severidade = em_risco[0]["sev"]
    frases = []
    for l in em_risco[:3]:
        nome = f"Lote {l['lote']}" if l["lote"] else "Entrada sem lote"
        valor = f" (≈ {t.moeda(l['sobra'] * custo)})" if custo is not None else ""
        if l["dias"] < 0:
            frases.append(f"{nome}: {t.qtd(l['qtd'], u)} venceram em {t.data(l['validade'])}{valor} — "
                          "não use; separe para devolução ou descarte correto.")
        elif c > 0:
            frases.append(f"{nome}: {t.qtd(l['qtd'], u)} vencem em {t.dias(l['dias'])} "
                          f"({t.data(l['validade'])}). Com o consumo recente ({_frase_consumo(prod)}), "
                          f"devem ser usados cerca de {t.qtd(l['usado'], u)} até lá; sobram "
                          f"≈ {t.qtd(l['sobra'], u)} que podem vencer sem uso{valor}.")
        else:
            frases.append(f"{nome}: {t.qtd(l['qtd'], u)} vencem em {t.dias(l['dias'])} "
                          f"({t.data(l['validade'])}). Não há saídas recentes suficientes para prever o "
                          f"uso, então todo o lote pode vencer{valor}.")
    if len(em_risco) > 3:
        frases.append(f"E mais {len(em_risco) - 3} lote(s) em risco.")
    vencido = any(l["dias"] < 0 for l in em_risco)
    titulo = "Lote vencido" if vencido else "Risco de vencimento"
    total_sobra = sum(l["sobra"] for l in em_risco)
    valor_total = total_sobra * custo if custo is not None else None
    return [_novo(
        prod, "vencimento", titulo, severidade, " ".join(frases),
        regra=(f"Para cada lote com validade: Crítico se já venceu ou se vence em ≤ "
               f"{p.vencimento_critico_dias} dias com sobra prevista; Atenção até "
               f"{p.vencimento_atencao_dias} dias; Informativo até {p.vencimento_info_dias} dias. "
               "Sobra = quantidade do lote − consumo previsto até a validade."),
        limite=("Quando a saída não informa o lote, supõe-se que saiu o que vence primeiro (FEFO). "
                "Lotes sem validade não entram nesta regra (aparecem na qualidade dos dados)."),
        dias=max(0, em_risco[0]["dias"]), valor=valor_total,
        dados={"lotes": [{"lote": l["lote"], "validade": t.data(l["validade"]), "qtd": l["qtd"],
                          "sobra": l["sobra"], "dias": l["dias"]} for l in em_risco]},
    )]


def regra_excesso(prod, p):
    saldo, minimo, cob = prod["saldo"], prod["minimo"], prod["cobertura"]
    c, u, valor = prod["consumo"], prod["unidade"], prod["valor_estoque"]
    valor_txt = f" Valor parado: {t.moeda(valor)}." if valor else ""
    if cob is not None and cob > p.excesso_cobertura_dias:
        msg = (f"Excesso de estoque: com o consumo médio recente ({_frase_consumo(prod)}), o saldo "
               f"({t.qtd(saldo, u)}) dura cerca de {t.dias(cob)} (≈ {t.num(cob / 30)} meses), acima do "
               f"limite de {p.excesso_cobertura_dias} dias.{valor_txt} {texto_confianca(c)}")
        return [_novo(prod, "excesso", "Excesso de estoque", ATENCAO, msg,
                      regra=f"Atenção se a cobertura estimada passar de {p.excesso_cobertura_dias} dias.",
                      limite=("Insumos comprados antecipadamente para a próxima safra podem parecer "
                              "excesso agora."),
                      valor=valor, confianca=c["confianca"], dados={"cobertura_dias": cob})]
    sem_consumo = not c["consumo_diario"]
    if sem_consumo and minimo and saldo > p.excesso_multiplo_minimo * minimo:
        msg = (f"Saldo acima do necessário: {t.qtd(saldo, u)} equivalem a {t.num(saldo / minimo)} vezes o "
               f"estoque mínimo ({t.qtd(minimo, u)}), e não há saídas recentes suficientes para estimar "
               f"a duração.{valor_txt}")
        return [_novo(prod, "excesso", "Saldo acima do necessário", INFORMATIVO, msg,
                      regra=(f"Informativo se não há consumo estimável e o saldo passa de "
                             f"{t.num(p.excesso_multiplo_minimo)} vezes o estoque mínimo."),
                      limite="O estoque mínimo cadastrado pode estar desatualizado.",
                      valor=valor, dados={"multiplo_minimo": saldo / minimo})]
    return []


def retiradas_atipicas(saidas, p, data_ref) -> list:
    """Saídas recentes muito acima do habitual: lista de (linha, mediana, limite), da maior para a menor."""
    idade = (data_ref - saidas["data"]).dt.days
    historico = saidas[idade < p.outlier_historico_dias]
    if len(historico) < p.outlier_min_saidas:
        return []
    recentes = historico[(data_ref - historico["data"]).dt.days < p.outlier_janela_dias]
    achados = []
    for idx, linha in recentes.sort_values("qtd_base", ascending=False).iterrows():
        outras = historico.drop(index=idx)["qtd_base"]
        mediana = float(outras.median())
        mad = float((outras - mediana).abs().median()) * 1.4826
        limite = mediana + p.outlier_k * mad if mad > 0 else 3 * mediana
        if linha["qtd_base"] > limite and linha["qtd_base"] > 2 * mediana:
            achados.append((linha, mediana, limite))
    return achados


def regra_fora_do_padrao(prod, p, data_ref):
    achados = retiradas_atipicas(prod["saidas"], p, data_ref)
    if not achados:
        return []
    u = prod["unidade"]

    linha, mediana, limite = achados[0]
    q = linha["qtd_base"]
    extras = []
    if pd.notna(linha.get("destino")) and str(linha.get("destino")).strip():
        extras.append(f"destino: {linha['destino']}")
    if pd.notna(linha.get("responsavel")) and str(linha.get("responsavel")).strip():
        extras.append(f"responsável: {linha['responsavel']}")
    extras_txt = f" ({'; '.join(extras)})" if extras else ""
    mais = f" Há mais {len(achados) - 1} retirada(s) fora do padrão nos últimos 30 dias." if len(achados) > 1 else ""
    msg = (f"Retirada fora do padrão: {t.qtd(q, u)} em {t.data(linha['data'])}{extras_txt}, "
           f"{t.num(q / mediana)}× a retirada típica (mediana de {t.qtd(mediana, u)}). O limite para "
           f"considerar normal é {t.qtd(limite, u)}.{mais} Confira se o registro está correto (erro de "
           "digitação, unidade trocada) ou se houve uso excepcional, perda ou desvio.")
    return [_novo(
        prod, "fora_do_padrao", "Retirada fora do padrão", ATENCAO, msg,
        regra=(f"Cada saída dos últimos {p.outlier_janela_dias} dias é comparada com as demais saídas do "
               f"produto nos últimos {p.outlier_historico_dias} dias. Fora do padrão se for maior que "
               f"mediana + {t.num(p.outlier_k)} × MAD e maior que 2× a mediana (se MAD = 0, limite = "
               f"3× a mediana). Exige pelo menos {p.outlier_min_saidas} saídas."),
        limite=("Produtos de uso naturalmente irregular (aplicações por talhão, manutenção corretiva) "
                "podem gerar avisos que são normais."),
        dados={"quantidade": q, "mediana": mediana, "limite": limite, "data": t.data(linha["data"])},
    )]


def regra_consumo_crescente(prod, p, data_ref):
    u, b = prod["unidade"], p.tendencia_bloco_dias
    # Um pico isolado (retirada fora do padrão) não é tendência: fica fora desta conta.
    atipicas = [linha.name for linha, _, _ in retiradas_atipicas(prod["saidas"], p, data_ref)]
    saidas = prod["saidas"].drop(index=atipicas)
    s3, n3 = soma_periodo(saidas, data_ref, 0, b)
    s2, n2 = soma_periodo(saidas, data_ref, b, 2 * b)
    s1, n1 = soma_periodo(saidas, data_ref, 2 * b, 3 * b)
    if min(n1, n2, n3) < p.tendencia_min_saidas_bloco:
        return []
    if not (s1 < s2 < s3 and s3 >= s1 * (1 + p.tendencia_aumento_min)):
        return []
    alta = (s3 / s1 - 1) * 100
    cob = prod["cobertura"]
    cob_txt = f" (cobertura atual estimada: {t.dias(cob)})" if cob is not None else ""
    msg = (f"Consumo crescente: as retiradas subiram de {t.qtd(s1, u)} ({2 * b + 1} a {3 * b} dias atrás) "
           f"para {t.qtd(s2, u)} ({b + 1} a {2 * b} dias atrás) e {t.qtd(s3, u)} nos últimos {b} dias, "
           f"alta de {t.num(alta, 0)}%. Se a tendência continuar, o estoque vai durar menos do que a "
           f"média indica{cob_txt}.")
    return [_novo(
        prod, "consumo_crescente", "Consumo crescente", ATENCAO, msg,
        regra=(f"Três blocos seguidos de {b} dias com consumo sempre maior, alta total de pelo menos "
               f"{t.num(p.tendencia_aumento_min * 100, 0)}% e no mínimo {p.tendencia_min_saidas_bloco} "
               "saídas em cada bloco. Retiradas fora do padrão não entram na conta."),
        limite="Três meses podem refletir a fase da safra (plantio, colheita), não uma tendência permanente.",
        dados={"blocos": [s1, s2, s3], "alta_percentual": alta},
    )]


def regra_variacao_preco(prod, p, data_ref):
    compras = prod["entradas"].dropna(subset=["preco_base"])
    if len(compras) < p.preco_min_compras_anteriores + 1:
        return []
    ultima = compras.iloc[-1]
    if (data_ref - ultima["data"]).days >= p.preco_janela_dias:
        return []
    anteriores = compras.iloc[:-1]
    mediana = float(anteriores["preco_base"].median())
    variacao = ultima["preco_base"] / mediana - 1
    if abs(variacao) < p.preco_variacao_min:
        return []
    u = prod["unidade"]
    fornecedor = f", fornecedor {ultima['fornecedor']}" if pd.notna(ultima.get("fornecedor")) else ""
    acima = variacao > 0
    msg = (f"{'Compra mais cara' if acima else 'Compra mais barata'}: a compra de {t.data(ultima['data'])}"
           f"{fornecedor} saiu por {t.moeda(ultima['preco_base'])}/{u}, {t.num(abs(variacao) * 100, 0)}% "
           f"{'acima' if acima else 'abaixo'} da mediana das {len(anteriores)} compras anteriores "
           f"({t.moeda(mediana)}/{u}). "
           + ("Vale cotar outros fornecedores antes da próxima compra." if acima
              else "Pode ser um bom momento para negociar ou antecipar a reposição."))
    return [_novo(
        prod, "variacao_preco", "Variação de preço", ATENCAO if acima else INFORMATIVO, msg,
        regra=(f"Compara o preço por {u} da última compra (últimos {p.preco_janela_dias} dias) com a "
               f"mediana das compras anteriores; alerta se a diferença for ≥ "
               f"{t.num(p.preco_variacao_min * 100, 0)}%. Exige {p.preco_min_compras_anteriores} compras "
               "anteriores com preço."),
        limite="Não corrige inflação nem diferenças de frete, prazo de pagamento ou qualidade do produto.",
        dados={"preco": ultima["preco_base"], "mediana": mediana, "variacao": variacao},
    )]


def regra_alto_valor_parado(prod, p, data_ref):
    if prod["classe_abc"] != "A" or prod["saldo"] <= 0 or not prod["valor_estoque"]:
        return []
    saidas = prod["saidas"]
    ultima = saidas["data"].max() if not saidas.empty else None
    dias_sem = (data_ref - ultima).days if ultima is not None else None
    saidas_giro, _ = soma_periodo(saidas, data_ref, 0, p.parado_giro_dias)
    giro = saidas_giro / prod["saldo"]
    if not (dias_sem is None or dias_sem >= p.parado_dias_sem_saida or giro <= p.parado_giro_max):
        return []
    if dias_sem is None:
        mov_txt = "nenhuma saída registrada"
    else:
        mov_txt = (f"última saída há {t.dias(dias_sem)}; nos últimos {p.parado_giro_dias} dias saiu "
                   f"{t.num(giro * 100, 0)}% do saldo")
    msg = (f"Alto valor parado: {t.moeda(prod['valor_estoque'])} em estoque "
           f"({t.num(prod['participacao_valor'] * 100, 0)}% do valor total, classe A da curva ABC) e "
           f"{mov_txt}. Avalie usar, remanejar, devolver ao fornecedor ou suspender novas compras.")
    return [_novo(
        prod, "alto_valor_parado", "Alto valor parado", ATENCAO, msg,
        regra=(f"Curva ABC pelo valor em estoque (saldo × custo médio das compras com preço): classe A "
               f"são os itens que somam os primeiros {t.num(p.abc_corte_a * 100, 0)}% do valor. Parado: "
               f"sem saída há ≥ {p.parado_dias_sem_saida} dias ou saídas de {p.parado_giro_dias} dias ≤ "
               f"{t.num(p.parado_giro_max * 100, 0)}% do saldo."),
        limite=("Itens sem preço não entram na curva ABC. Peças de reposição para emergências podem "
                "ficar paradas de propósito."),
        valor=prod["valor_estoque"],
        dados={"valor": prod["valor_estoque"], "dias_sem_saida": dias_sem, "giro": giro},
    )]


def gerar_alertas(prod, p, data_ref) -> list:
    alertas = []
    alertas += regra_estoque_critico(prod, p)
    vencimento = regra_vencimento(prod, p, data_ref)
    alertas += vencimento
    parado = regra_alto_valor_parado(prod, p, data_ref)
    alertas += parado
    # Excesso não é repetido quando o mesmo saldo já aparece como vencimento ou valor parado.
    if not parado and not vencimento:
        alertas += regra_excesso(prod, p)
    alertas += regra_fora_do_padrao(prod, p, data_ref)
    alertas += regra_consumo_crescente(prod, p, data_ref)
    alertas += regra_variacao_preco(prod, p, data_ref)
    return alertas
