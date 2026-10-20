"""Testes de fumaça: garantem que a estrutura básica funciona."""

import subprocess
import sys


def test_motor_nao_depende_de_flask():
    # Processo separado: aqui o Flask já foi importado pelo próprio teste.
    codigo = "import sys, motor.analise; print('flask' in sys.modules)"
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, check=True)
    assert saida.stdout.strip() == "False"


def test_todas_as_paginas_abrem(cliente):
    for url in ["/", "/alertas", "/alertas.csv", "/produtos", "/produtos?ordem=cobertura",
                "/produto/ureia", "/registrar", "/importar", "/qualidade", "/movimentacoes",
                "/como-funciona"]:
        assert cliente.get(url).status_code == 200, url


def test_pagina_inicial_mostra_aviso_de_dados_simulados(cliente):
    html = cliente.get("/").get_data(as_text=True)
    assert "SIMULADOS" in html
    assert "Data de referência" in html and "30/09/2026" in html
    assert "O que merece atenção imediata" in html
