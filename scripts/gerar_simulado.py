"""Gera a base SIMULADA de movimentações (dados fictícios, reproduzíveis).

Uso:  python scripts/gerar_simulado.py
Saída: data/simulado/movimentacoes_simulado.csv

A semente é fixa (42): rodar de novo gera exatamente o mesmo arquivo.
Os problemas plantados de propósito estão descritos em data/simulado/GABARITO_SIMULADO.md.
Responsáveis e fornecedores são genéricos (funções e nomes fictícios), sem dados pessoais.
"""

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEMENTE = 42
INICIO = date(2026, 3, 2)
FIM = date(2026, 9, 30)          # última movimentação = data de referência padrão
SAIDA = Path(__file__).resolve().parent.parent / "data" / "simulado" / "movimentacoes_simulado.csv"

COLUNAS = ["produto", "categoria", "unidade", "quantidade", "estoque_minimo", "tipo", "data",
           "preco_unitario", "lote", "validade", "fornecedor", "destino", "responsavel"]
FORNECEDORES = ["Agro Fornecedor A", "Distribuidora Rural B", "Cooperativa C"]
RESPONSAVEIS = ["Encarregado", "Tratorista A", "Tratorista B", "Operador de pulverização", "Almoxarife"]
DESTINOS = ["Talhão 1", "Talhão 2", "Talhão 3", "Talhão 4", "Talhão 5", "Pivô 1"]
DESTINOS_MAQ = ["Trator 1", "Trator 2", "Colheitadeira", "Pulverizador", "Oficina"]

rng = random.Random(SEMENTE)
linhas = []


def dias(inicio=INICIO, fim=FIM):
    d = inicio
    while d <= fim:
        yield d
        d += timedelta(days=1)


def arred(q, unidade):
    if unidade in ("un", "par", "sc"):
        return max(1, round(q))
    if unidade == "t":
        return round(q, 2)
    if unidade == "mL":
        return max(50, round(q / 50) * 50)
    return round(q, 1)


def registrar(produto, categoria, unidade, quantidade, tipo, dia, minimo=None, preco=None, lote=None,
              validade=None, fornecedor=None, destino=None, responsavel=None):
    linhas.append({
        "produto": produto, "categoria": categoria, "unidade": unidade, "quantidade": quantidade,
        "estoque_minimo": "" if minimo is None else minimo, "tipo": tipo, "data": dia.isoformat(),
        "preco_unitario": "" if preco is None else round(preco, 2), "lote": lote or "",
        "validade": validade.isoformat() if validade else "", "fornecedor": fornecedor or "",
        "destino": destino or "", "responsavel": responsavel or rng.choice(RESPONSAVEIS),
    })


def simular(nome, categoria, unidade, consumo_dia, preco, freq=3, validade_dias=None,
            minimo_dias=10, repor_dias=35, comprar_dias=60, multiplicador=None, parar_compras=None,
            eventos=None, destinos=None, unidade_saida=None, fator_saida=1.0, compras_sem_preco=(),
            compras_sem_validade=(), inicio=INICIO, estoque_inicial_dias=60, sem_preco=False):
    """Simula o dia a dia de um produto: retiradas a cada ~`freq` dias e compras quando o estoque baixa.

    `compras_sem_preco` / `compras_sem_validade`: números das compras (1 = primeira) lançadas sem o dado.
    """
    multiplicador = multiplicador or (lambda d: 1.0)
    eventos = eventos or {}
    destinos = destinos or DESTINOS
    minimo = arred(consumo_dia * minimo_dias, unidade) if minimo_dias else None
    estoque = 0.0
    n_lote = 0

    def comprar(dia, quantidade):
        nonlocal estoque, n_lote
        n_lote += 1
        q = arred(quantidade, unidade)
        validade = dia + timedelta(days=validade_dias) if validade_dias else None
        if n_lote in compras_sem_validade:
            validade = None
        p = None if sem_preco or n_lote in compras_sem_preco else preco * (1 + rng.gauss(0, 0.03))
        prefixo = "".join(c for c in nome.upper() if c.isalpha())[:3]
        registrar(nome, categoria, unidade, q, "entrada", dia, minimo, p,
                  f"{prefixo}-{dia:%y%m}-{n_lote}", validade, rng.choice(FORNECEDORES))
        estoque += q

    comprar(inicio, consumo_dia * estoque_inicial_dias)
    proxima = inicio + timedelta(days=max(1, round(rng.uniform(0.5, 1.5) * freq)))
    for dia in dias(inicio + timedelta(days=1)):
        m = multiplicador(dia)
        quantidades = []
        if dia in eventos:
            quantidades.append(eventos[dia])
        elif dia >= proxima:
            quantidades.append(consumo_dia * freq * m * math.exp(rng.gauss(0, 0.15)))
            proxima = dia + timedelta(days=max(1, round(freq + rng.gauss(0, freq * 0.2))))
        for q in quantidades:
            q = min(arred(q, unidade), estoque)
            if q <= 0:
                continue
            estoque -= q
            u, qs = unidade, q
            if unidade_saida:
                u, qs = unidade_saida, arred(q * fator_saida, unidade_saida)
            registrar(nome, categoria, u, qs, "saída", dia, minimo, destino=rng.choice(destinos))
        pode_comprar = parar_compras is None or dia < parar_compras
        if pode_comprar and estoque < consumo_dia * m * repor_dias:
            comprar(dia, consumo_dia * m * comprar_dias)
    return estoque


def ajustar_estoque_final(nome, alvo):
    """Ajusta a última compra para o produto terminar com o saldo `alvo` (problema plantado)."""
    movs = [l for l in linhas if l["produto"] == nome]
    saldo = sum(l["quantidade"] * (1 if l["tipo"] == "entrada" else -1) for l in movs)
    ultima = [l for l in movs if l["tipo"] == "entrada"][-1]
    ultima["quantidade"] = round(ultima["quantidade"] + alvo - saldo, 1)
    assert ultima["quantidade"] > 0, nome


# ---------------------------------------------------------------- produtos sem problema plantado
simular("NPK 04-14-08", "Fertilizantes", "kg", 80, 3.2, freq=4)
simular("NPK 04-30-16", "Fertilizantes", "kg", 50, 4.1, freq=4)
simular("MAP", "Fertilizantes", "kg", 30, 4.8, freq=5)
simular("Sulfato de amônio", "Fertilizantes", "kg", 25, 2.6, freq=5)
simular("FTE BR-12", "Fertilizantes", "kg", 3, 7.5, freq=7)
simular("Gesso agrícola", "Corretivos", "t", 0.3, 160, freq=7)
simular("Calcário dolomítico", "Corretivos", "t", 0.5, 210, freq=7)
simular("Semente de milho", "Sementes", "sc", 0.8, 980, freq=4, validade_dias=540)
simular("Braquiária", "Sementes", "kg", 2, 28, freq=6, validade_dias=540)
simular("Herbicida 2,4-D", "Defensivos e biológicos", "L", 2, 32, freq=4, validade_dias=720)
simular("Azospirillum", "Defensivos e biológicos", "L", 0.2, 55, freq=10, validade_dias=360)
simular("Filtro de óleo", "Peças e manutenção", "un", 0.1, 85, freq=10, destinos=DESTINOS_MAQ)
simular("Filtro de ar", "Peças e manutenção", "un", 0.07, 140, freq=14, destinos=DESTINOS_MAQ)
simular("Rolamento 6205", "Peças e manutenção", "un", 0.05, 120, freq=20, destinos=DESTINOS_MAQ)
simular("Mangueira de gotejamento", "Irrigação", "m", 20, 1.2, freq=7, destinos=["Pivô 1"])
simular("Conector de irrigação", "Irrigação", "un", 1, 3.5, freq=7, destinos=["Pivô 1"])
simular("Respirador PFF2", "EPI e diversos", "un", 0.5, 9, freq=4, destinos=["Almoxarifado"])
simular("Bota de borracha", "EPI e diversos", "par", 0.05, 65, freq=20, destinos=["Almoxarifado"])

# Unidades da mesma grandeza (convertidas automaticamente): entra em L, sai em mL.
simular("Adjuvante", "Defensivos e biológicos", "L", 0.4, 30, freq=4, validade_dias=720,
        unidade_saida="mL", fator_saida=1000)

# ---------------------------------------------------------------- problemas plantados
# P1 Estoque crítico por cobertura: diesel para de ser reposto e termina com ~6 dias de consumo.
simular("Diesel S10", "Combustíveis e lubrificantes", "L", 160, 6.2, freq=1.2, repor_dias=12,
        comprar_dias=25, minimo_dias=12, parar_compras=date(2026, 9, 10), destinos=DESTINOS_MAQ,
        eventos={FIM: 150})
ajustar_estoque_final("Diesel S10", 1000)

# P2 Estoque abaixo do mínimo: herbicida termina com 80 L e mínimo de 120 L.
simular("Glifosato 480", "Defensivos e biológicos", "L", 3, 28, freq=4, validade_dias=730,
        minimo_dias=40, parar_compras=date(2026, 9, 1))
ajustar_estoque_final("Glifosato 480", 80)

# P3 Consumo crescente: fungicida com retiradas cada vez maiores nos últimos 90 dias.
def mult_fungicida(d):
    idade = (FIM - d).days
    return 1.0 if idade >= 60 else (1.5 if idade >= 30 else 2.3)


simular("Fungicida azoxistrobina", "Defensivos e biológicos", "L", 1.5, 120, freq=3,
        validade_dias=720, multiplicador=mult_fungicida)

# P4 Excesso: compra grande de graxa, consumo pequeno, sem reposição (dura anos).
simular("Graxa", "Combustíveis e lubrificantes", "kg", 0.15, 24, freq=6, minimo_dias=30,
        estoque_inicial_dias=800, parar_compras=INICIO, destinos=DESTINOS_MAQ)

# P5 Retirada fora do padrão: óleo de motor, uma retirada de 60 L em 20/09.
simular("Óleo de motor 15W40", "Combustíveis e lubrificantes", "L", 1, 21, freq=5,
        comprar_dias=100, destinos=DESTINOS_MAQ, eventos={date(2026, 9, 20): 60})
for l in linhas:
    if l["produto"] == "Óleo de motor 15W40" and l["data"] == "2026-09-20" and l["tipo"] == "saída":
        l["destino"], l["responsavel"] = "Trator 2", "Tratorista B"

# P6 Variação de preço: cloreto de potássio, última compra ~38% mais cara.
simular("Cloreto de potássio (KCl)", "Fertilizantes", "kg", 60, 3.1, freq=5, comprar_dias=45)
ultima_kcl = [l for l in linhas if l["produto"] == "Cloreto de potássio (KCl)" and l["tipo"] == "entrada"][-1]
assert ultima_kcl["data"] >= "2026-08-15", ultima_kcl
ultima_kcl["preco_unitario"], ultima_kcl["fornecedor"] = round(3.1 * 1.38, 2), "Distribuidora Rural B"

# P7 Nomes diferentes para o mesmo produto + unidades mistas (sc x kg) sem fator.
#    "Ureia": compras em sacos de 50 kg (sc) e retiradas em kg.
for d, sacos in [(INICIO, 60), (date(2026, 5, 4), 50), (date(2026, 7, 6), 50), (date(2026, 8, 31), 40)]:
    registrar("Ureia", "Fertilizantes", "sc", sacos, "entrada", d, 1000, 160 * (1 + rng.gauss(0, 0.03)),
              f"URE-{d:%y%m}", None, rng.choice(FORNECEDORES))
for d in dias(INICIO + timedelta(days=1)):
    if rng.random() < 1 / 3:
        registrar("Ureia", "Fertilizantes", "kg", round(100 * math.exp(rng.gauss(0, 0.15)), 1), "saída", d,
                  1000, destino=rng.choice(DESTINOS))
registrar("UREIA 45%", "Fertilizantes", "sc", 20, "entrada", date(2026, 6, 15), None, 165, "U45-01",
          None, "Cooperativa C")
registrar("UREIA 45%", "Fertilizantes", "sc", 20, "entrada", date(2026, 8, 17), None, 168, "U45-02",
          None, "Cooperativa C")
registrar("ureia granulada", "Fertilizantes", "kg", 1000, "entrada", date(2026, 7, 20), None, 3.4,
          "UGR-01", None, "Agro Fornecedor A")
for d, q in [(date(2026, 7, 27), 150), (date(2026, 8, 10), 120), (date(2026, 9, 8), 140)]:
    registrar("ureia granulada", "Fertilizantes", "kg", q, "saída", d, destino="Talhão 2")

#    "Luva nitrílica" x "Luvas nitrilicas": parte das retiradas lançada com outro nome.
simular("Luva nitrílica", "EPI e diversos", "par", 2, 4.5, freq=2, destinos=["Almoxarifado"])
for l in linhas:
    if l["produto"] == "Luva nitrílica" and l["tipo"] == "saída" and l["data"] >= "2026-08-01" \
            and rng.random() < 0.4:
        l["produto"] = "Luvas nitrilicas"

#    Grafias que diferem só em acento/maiúsculas (tratadas como o mesmo produto, com aviso).
simular("Óleo hidráulico", "Combustíveis e lubrificantes", "L", 0.8, 22, freq=5, destinos=DESTINOS_MAQ)
for l in linhas:
    if l["produto"] == "Óleo hidráulico" and rng.random() < 0.3:
        l["produto"] = rng.choice(["Oleo hidraulico", "ÓLEO HIDRÁULICO"])

#    Formulações parecidas que NÃO podem ser unificadas: NPK 04-14-08 x NPK 04-30-16 e
#    Filtro de óleo x Filtro de ar (já gerados acima).

# P8 Lotes a vencer.
#    Inoculante: lote vence em 20/10/2026 e o consumo não dá conta de usar tudo.
registrar("Inoculante para soja", "Defensivos e biológicos", "L", 40, "entrada", date(2026, 4, 20), 5, 45,
          "INO-2604", date(2026, 10, 20), "Agro Fornecedor A")
for d in dias(date(2026, 5, 4)):
    if d.weekday() == 0:
        registrar("Inoculante para soja", "Defensivos e biológicos", "L", 0.8, "saída", d, 5,
                  destino=rng.choice(DESTINOS))
#    Trichoderma: lote antigo venceu em 15/09/2026 com saldo; as retiradas passaram a usar o lote novo.
registrar("Trichoderma", "Defensivos e biológicos", "kg", 10, "entrada", date(2026, 3, 10), 2, 60,
          "TRI-01", date(2026, 9, 15), "Cooperativa C")
for d in [date(2026, 3, 24), date(2026, 4, 14), date(2026, 5, 5), date(2026, 6, 2)]:
    registrar("Trichoderma", "Defensivos e biológicos", "kg", 1, "saída", d, 2, destino="Talhão 4")
registrar("Trichoderma", "Defensivos e biológicos", "kg", 20, "entrada", date(2026, 7, 1), 2, 62,
          "TRI-02", date(2027, 3, 1), "Cooperativa C")
for d in dias(date(2026, 7, 6)):
    if d.weekday() == 0:
        registrar("Trichoderma", "Defensivos e biológicos", "kg", 0.5, "saída", d, 2, lote="TRI-02",
                  destino=rng.choice(DESTINOS))
#    Semente de feijão: lote grande vence em 10/12/2026, consumo baixo.
registrar("Semente de feijão", "Sementes", "kg", 600, "entrada", date(2026, 6, 10), 50, 9,
          "FEI-2606", date(2026, 12, 10), "Cooperativa C")
for d in dias(date(2026, 6, 15)):
    if (d - date(2026, 6, 15)).days % 10 == 0:
        registrar("Semente de feijão", "Sementes", "kg", round(15 * math.exp(rng.gauss(0, 0.1))), "saída",
                  d, 50, destino=rng.choice(DESTINOS))

# P9 Itens de alto valor parados.
registrar("Inseticida clorantraniliprole", "Defensivos e biológicos", "L", 20, "entrada", date(2026, 4, 10),
          None, 850, "CLT-01", date(2028, 4, 1), "Distribuidora Rural B")
for d in [date(2026, 4, 25), date(2026, 5, 20)]:
    registrar("Inseticida clorantraniliprole", "Defensivos e biológicos", "L", 1, "saída", d,
              destino="Talhão 3")
registrar("Correia da colheitadeira", "Peças e manutenção", "un", 4, "entrada", date(2026, 3, 16), 1, 2800,
          "COR-01", None, "Agro Fornecedor A")

# P10 Dados ausentes.
#    Atrazina: algumas compras sem preço e sem validade.
simular("Atrazina", "Defensivos e biológicos", "L", 1.5, 38, freq=4, validade_dias=720,
        compras_sem_preco=(2, 4), compras_sem_validade=(3,))
#    Semente de soja: compras sem validade.
simular("Semente de soja", "Sementes", "sc", 1, 380, freq=3, validade_dias=540, compras_sem_validade=(2, 3))
#    Estacas de eucalipto: nenhuma compra com preço.
simular("Estacas de eucalipto", "EPI e diversos", "un", 3, 0, freq=4, sem_preco=True,
        destinos=DESTINOS)

# P11 Saldo negativo: saídas de bico de pulverização sem a entrada correspondente.
registrar("Bico de pulverização", "Peças e manutenção", "un", 12, "entrada", date(2026, 3, 5), 4, 18,
          "BIC-01", None, "Agro Fornecedor A")
for d, q in [(date(2026, 4, 8), 2), (date(2026, 5, 13), 2), (date(2026, 6, 17), 2), (date(2026, 7, 22), 2),
             (date(2026, 8, 19), 2), (date(2026, 9, 9), 3), (date(2026, 9, 23), 2)]:
    registrar("Bico de pulverização", "Peças e manutenção", "un", q, "saída", d, 4, destino="Pulverizador")

linhas.sort(key=lambda l: (l["data"], l["tipo"] != "entrada", l["produto"]))
SAIDA.parent.mkdir(parents=True, exist_ok=True)
with SAIDA.open("w", newline="", encoding="utf-8") as f:
    escritor = csv.DictWriter(f, fieldnames=COLUNAS)
    escritor.writeheader()
    escritor.writerows(linhas)
print(f"{len(linhas)} movimentações SIMULADAS gravadas em {SAIDA}")
