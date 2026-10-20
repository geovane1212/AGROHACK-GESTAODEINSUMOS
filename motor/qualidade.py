"""Problemas de qualidade dos dados. Nada é escondido: tudo que afeta um cálculo aparece aqui."""

from . import texto as t


def problema(tipo, titulo, produto, descricao, chave_produto=None, extra=None):
    return {"tipo": tipo, "titulo": titulo, "produto": produto, "descricao": descricao,
            "chave_produto": chave_produto, "extra": extra or {}}


def verificar_produto(prod, grupo, p) -> list:
    """`grupo`: todas as movimentações do produto (incluídas ou não no cálculo)."""
    achados = []
    nome, chave = prod["nome"], prod["chave"]

    excluidas = grupo[~grupo["incluida"]]
    if not excluidas.empty:
        unidades = sorted(excluidas["unidade"].unique())
        achados.append(problema(
            "unidade_inconsistente", "Unidade inconsistente", nome,
            f"{len(excluidas)} movimentação(ões) em {', '.join(unidades)} não entraram no cálculo, porque "
            f"não há fator de conversão para {prod['unidade']}. Cadastre o fator deste produto "
            f"(ex.: 1 sc = 50 kg) para incluí-las.",
            chave, {"unidades": unidades, "unidade_base": prod["unidade"]}))

    if prod["negativo_em"] is not None:
        achados.append(problema(
            "saldo_negativo", "Saldo negativo", nome,
            f"O saldo ficou negativo em {t.data(prod['negativo_em'])} (menor saldo: "
            f"{t.qtd(prod['menor_saldo'], prod['unidade'])}). Há saídas sem a entrada correspondente "
            "registrada; confira se falta lançar alguma compra.", chave))

    entradas = grupo[grupo["tipo"] == "entrada"]
    sem_preco = int(entradas["preco_unitario"].isna().sum())
    if sem_preco:
        efeito = ("o valor em estoque deste produto não pode ser calculado"
                  if prod["custo_medio"] is None else "o custo médio usa só as entradas com preço")
        achados.append(problema(
            "preco_ausente", "Preço ausente", nome,
            f"{sem_preco} de {len(entradas)} entrada(s) sem preço; {efeito}.", chave))

    if prod["categoria"] in p.categorias_com_validade:
        sem_validade = int(entradas["validade"].isna().sum())
        if sem_validade:
            achados.append(problema(
                "validade_ausente", "Validade ausente", nome,
                f"{sem_validade} de {len(entradas)} entrada(s) sem validade; esses lotes ficam fora do "
                "alerta de vencimento.", chave))

    grafias = sorted(grupo["produto"].dropna().unique())
    originais = grupo.drop_duplicates("produto")
    automaticas = originais[originais["chave_original"] == chave]["produto"].tolist()
    if len(automaticas) > 1:
        achados.append(problema(
            "grafias_equivalentes", "Grafias equivalentes", nome,
            f"Registrado como {', '.join(repr(g) for g in sorted(automaticas))}. Diferem só em maiúsculas, "
            "acentos ou espaços e foram tratados como o mesmo produto.", chave))
    prod["grafias"] = grafias
    return achados
