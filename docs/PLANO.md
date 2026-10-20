# Plano de trabalho (19/10 a 29/10/2026)

Prioridade de esforço segundo os critérios de avaliação: **análise/alertas (20)** e
**funcionamento com os dados (20)** primeiro.

## Divisão sugerida das frentes

Todos programam, todos apresentam a própria frente e todos revisam PRs de outra frente.

| Integrante | Frente principal | Revisa |
| --- | --- | --- |
| Igor Malher | Motor de alertas: saldo, cobertura e confiança, crítico, vencimento (FEFO), excesso, retirada fora do padrão, priorização e justificativas | Dados/testes |
| Geovane Alencar | Dados de entrada: importação CSV/XLSX, mapeamento de colunas, banco SQLite, unidades, unificação de nomes (apelidos), qualidade dos dados | Motor |
| João Paulo da Costa | Painel web: telas, gráficos (Chart.js), responsividade/acessibilidade, reanálise e "o que mudou", deploy | Importação |
| Edson Henrique | Dados simulados + gabarito, testes (pytest e ponta a ponta), `VALIDACAO.md`, documentação, slides e vídeo | Painel |

## Cronograma

| Dia | Data | Fase | Entregas |
| --- | --- | --- | --- |
| 1 | 19/10 | Estrutura | Repositório, esqueleto, gerador de dados simulados (semente fixa), `GABARITO_SIMULADO.md` |
| 2–4 | 20–22/10 | Motor P0 | Saldo por produto/lote, data de referência, cobertura + confiança, crítico, vencimento, excesso, fora do padrão, priorização, justificativas, testes |
| 4–6 | 22–24/10 | Painel e reanálise | Importação + mapeamento, cadastro manual, lista priorizada, gráficos, reanálise |
| 6 | 24/10 | P1 | Unificação de nomes, unidades, consumo crescente, preço, ABC, qualidade dos dados, "o que mudou", página de critérios |
| 7 | 25/10 | Deploy | Link público, Dockerfile, base de demonstração recriada ao iniciar |
| 8–9 | 26–27/10 | Documentação | README completo, `VALIDACAO.md`, teste contra o gabarito, vídeo, slides, perguntas da banca |
| 10 | 28/10 | Ensaio | Ensaio cronometrado, plano B local, tag `v1.0-entrega` |
| — | 29/10 | Apresentação | SNCT |

Ao fim de cada fase: commit + push, atualização do `AI_USAGE.md` e instruções de teste.
