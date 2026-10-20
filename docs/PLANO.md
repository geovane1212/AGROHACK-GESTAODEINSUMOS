# Plano de trabalho (19/10 a 29/10/2026)

Prioridade de esforço segundo os critérios de avaliação: **análise/alertas (20)** e
**funcionamento com os dados (20)** primeiro.

## Situação em 19/10/2026

A primeira versão completa (P0 + P1) já está no repositório e funcionando localmente: motor de alertas,
importação, painel, qualidade dos dados, reanálise, dados simulados com gabarito e 106 testes. A partir de
agora, o trabalho principal da equipe é **entender, revisar e defender** cada parte (todos serão questionados
pela banca), fazer o deploy, preparar vídeo e slides e adaptar o sistema à base oficial quando ela sair.

## Divisão sugerida das frentes

Todos programam, todos apresentam a própria frente e todos revisam a frente de outro colega.

| Integrante | Frente principal | Arquivos para dominar | Revisa |
| --- | --- | --- | --- |
| Igor Malher | Motor de alertas e priorização | `motor/alertas.py`, `motor/consumo.py`, `motor/saldos.py`, `motor/config.py` | Dados/testes |
| Geovane Alencar | Dados de entrada e qualidade | `motor/importacao.py`, `motor/nomes.py`, `motor/unidades.py`, `motor/qualidade.py`, `app/db.py` | Motor |
| João Paulo da Costa | Painel, reanálise e deploy | `app/views.py`, `app/servicos.py`, `app/templates/`, `Dockerfile`, `render.yaml` | Importação |
| Edson Henrique | Dados simulados, testes, validação e apresentação | `scripts/gerar_simulado.py`, `data/simulado/`, `tests/`, `VALIDACAO.md`, `docs/APRESENTACAO.md` | Painel |

## Cronograma restante

| Dia | Data | Tarefa | Responsável sugerido |
| --- | --- | --- | --- |
| 2 | 20/10 | Cada um roda o projeto, lê os arquivos da sua frente e preenche a revisão no `AI_USAGE.md` | Todos |
| 3 | 21/10 | Preencher funções no README; ajustar o que acharem estranho (via Pull Request) | Todos |
| 4 | 22/10 | Deploy no Render (ou similar) e link no README | João Paulo |
| 5 | 23/10 | Mostrar o sistema para alguém de Agronomia ou um produtor; registrar em `VALIDACAO.md` | Edson + quem tiver contato |
| 6 | 24/10 | Base oficial (se divulgada): importar, conferir mapeamento e apelidos, reexecutar testes | Geovane + Igor |
| 7 | 25/10 | Slides (estrutura em `docs/APRESENTACAO.md`) | Edson |
| 8 | 26/10 | Vídeo demonstrativo | João Paulo + Edson |
| 9 | 27/10 | Ensaio cronometrado com perguntas da banca (cada um responde as da sua frente) | Todos |
| 10 | 28/10 | Ensaio final, plano B testado sem internet, tag `v1.0-entrega` | Todos |
| — | 29/10 | Apresentação na SNCT | Todos |

Ao fim de cada etapa: commit + push, atualização do `AI_USAGE.md` e instruções de teste.
