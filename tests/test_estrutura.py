"""Testes de fumaça: garantem que a estrutura básica funciona."""

import subprocess
import sys

from app import create_app


def test_motor_nao_depende_de_flask():
    # Processo separado: aqui o Flask já foi importado pelo próprio teste.
    codigo = "import sys, motor; print('flask' in sys.modules)"
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, check=True)
    assert saida.stdout.strip() == "False"


def test_pagina_inicial_mostra_aviso_de_dados_simulados():
    cliente = create_app({"TESTING": True}).test_client()
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "SIMULADOS" in resposta.get_data(as_text=True)
