# Dados SIMULADOS

Os arquivos desta pasta são **simulados** (fictícios), gerados por script com semente fixa para serem
reproduzíveis. Não representam nenhuma propriedade real.

- `movimentacoes_simulado.csv`: 1.722 movimentações de 02/03/2026 a 30/09/2026 (40 produtos).
- Script gerador: `scripts/gerar_simulado.py` (`python scripts/gerar_simulado.py` recria o mesmo arquivo).
- Problemas plantados de propósito: [`GABARITO_SIMULADO.md`](GABARITO_SIMULADO.md).

O sistema carrega este arquivo automaticamente quando o banco está vazio (variável `SEED_DEMO=1`) e
mostra o aviso "Dados SIMULADOS" no topo de todas as páginas enquanto houver dados simulados.
