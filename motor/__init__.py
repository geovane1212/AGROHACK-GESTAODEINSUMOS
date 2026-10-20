"""Motor de análise de estoque.

Funções puras em Python (sem Flask): recebem dados (DataFrames/listas) e uma data de
referência, e devolvem saldos, alertas e justificativas. Por isso podem ser testadas
isoladamente com pytest e reaproveitadas por qualquer interface.
"""

__version__ = "0.1.0"
