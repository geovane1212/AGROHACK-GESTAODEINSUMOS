from datetime import date, timedelta

import pandas as pd
import pytest

from app import create_app

REF = date(2026, 9, 30)


def mov(produto, tipo, qtd, dia, unidade="kg", **extra):
    """Uma movimentação. `dia` pode ser date ou nº de dias antes da data de referência."""
    if isinstance(dia, int):
        dia = REF - timedelta(days=dia)
    return {"produto": produto, "tipo": tipo, "quantidade": qtd, "data": pd.Timestamp(dia),
            "unidade": unidade, **extra}


def tabela(*linhas):
    return pd.DataFrame(list(linhas))


def saidas_regulares(produto, qtd, a_cada, dias=90, unidade="kg", **extra):
    """Saídas iguais a cada `a_cada` dias nos últimos `dias` dias (a mais recente na data de referência)."""
    return [mov(produto, "saida", qtd, d, unidade, **extra) for d in range(0, dias, a_cada)]


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'teste.db'}",
                       "SEED_DEMO": True, "SECRET_KEY": "teste"})


@pytest.fixture
def cliente(app):
    return app.test_client()
