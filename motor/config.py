"""Parâmetros de todas as regras de análise.

Ficam num só lugar para que a página "Como funciona" e a documentação mostrem
exatamente os valores usados no cálculo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametros:
    # Consumo médio diário: usa os últimos 30 dias se houver saídas suficientes, senão 60.
    janela_curta_dias: int = 30
    janela_longa_dias: int = 60
    min_saidas_janela_curta: int = 5

    # Confiança da estimativa, pelo nº de saídas nos últimos 60 dias.
    confianca_alta: int = 10      # >= 10 saídas
    confianca_media: int = 5      # 5 a 9 saídas
    confianca_minima: int = 2     # 2 a 4 = baixa; < 2 = sem estimativa

    # Estoque crítico (cobertura = saldo ÷ consumo médio diário).
    cobertura_critica_dias: int = 7
    cobertura_atencao_dias: int = 15

    # Risco de vencimento (dias até a validade do lote).
    vencimento_critico_dias: int = 30
    vencimento_atencao_dias: int = 90
    vencimento_info_dias: int = 180

    # Excesso.
    excesso_cobertura_dias: int = 180
    excesso_multiplo_minimo: float = 4.0

    # Retirada fora do padrão: mediana + k × MAD.
    outlier_k: float = 3.5
    outlier_min_saidas: int = 6
    outlier_janela_dias: int = 30
    outlier_historico_dias: int = 90

    # Consumo crescente: três blocos consecutivos de 30 dias.
    tendencia_bloco_dias: int = 30
    tendencia_aumento_min: float = 0.30
    tendencia_min_saidas_bloco: int = 2

    # Variação de preço: última compra x mediana das compras anteriores.
    preco_variacao_min: float = 0.20
    preco_min_compras_anteriores: int = 2
    preco_janela_dias: int = 60

    # Curva ABC e alto valor parado.
    abc_corte_a: float = 0.80
    abc_corte_b: float = 0.95
    parado_dias_sem_saida: int = 60
    parado_giro_dias: int = 90
    parado_giro_max: float = 0.10

    # Categorias em que a validade é esperada (ausência vira aviso de qualidade).
    categorias_com_validade: tuple = ("Sementes", "Defensivos e biológicos")


PADRAO = Parametros()
