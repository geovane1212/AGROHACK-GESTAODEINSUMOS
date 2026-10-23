# Declaração de uso de Inteligência Artificial

Conforme o edital do AGROHACK 2026/2, declaramos as ferramentas de IA usadas, suas finalidades,
as partes do projeto apoiadas e as revisões feitas pelos integrantes. Este arquivo é atualizado
ao fim de cada fase.

## Ferramentas

| Ferramenta | Modelo | Finalidade |
| --- | --- | --- |
| Claude (Anthropic), chat | [preencher modelo] | Análise do edital, escolha da proposta e revisão do prompt de trabalho |
| Claude Code (Anthropic), extensão do VS Code | Claude Opus 5.5 (`claude-opus-5-5`) | Geração de código, testes, dados simulados, documentação e configuração do repositório |

## Partes apoiadas por IA e revisão humana

Para cada linha, o integrante revisor preenche o próprio nome e o que conferiu (ex.: "li o código, rodei os
testes, conferi a regra com um exemplo à mão").

| Data | Parte / arquivos | Ferramenta | O que a IA fez | Revisado por | O que foi conferido |
| --- | --- | --- | --- | --- | --- |
| 19/10/2026 | `PROMPT_PROJETO_AGROHACK.md` (não versionado) | Claude (chat) | Análise do edital e revisão do prompt | [preencher] | [preencher] |
| 19/10/2026 | Estrutura inicial: `README.md`, `.gitignore`, `.env.example`, `CONTRIBUTING.md`, `LICENSE`, `docs/PLANO.md` | Claude Code | Gerou os arquivos e o primeiro commit | [preencher] | [preencher] |
| 19/10/2026 | Motor de análise: `motor/` (config, preparar, saldos, consumo, alertas, qualidade, nomes, unidades, importacao, analise, mudancas) | Claude Code | Escreveu o código das regras a partir dos critérios do edital | [preencher] | [preencher] |
| 19/10/2026 | Camada web: `app/` (rotas, banco, templates, CSS) | Claude Code | Escreveu as telas e a integração com o banco | [preencher] | [preencher] |
| 19/10/2026 | Dados simulados: `scripts/gerar_simulado.py`, `data/simulado/` | Claude Code | Escreveu o gerador e o gabarito; ajustou o gerador para reduzir ruído (registrado no gabarito) | [preencher] | [preencher] |
| 19/10/2026 | Testes: `tests/` (106 testes) | Claude Code | Escreveu os testes e rodou a suíte | [preencher] | [preencher] |
| 19/10/2026 | Documentação: `README.md`, `VALIDACAO.md`, `docs/APRESENTACAO.md` | Claude Code | Escreveu os textos com base nos resultados reais dos testes | [preencher] | [preencher] |
| 19/10/2026 | Deploy: `Dockerfile`, `render.yaml`, `wsgi.py` | Claude Code | Escreveu os arquivos (Dockerfile não testado localmente) | [preencher] | [preencher] |
| 19/10/2026 | v2 Fase 0–1: `docs/DIAGNOSTICO_V1.md`, navegação, componentes, `tests/test_navegacao.py` | Claude Code | Mediu a interface com Playwright, criou a navegação mobile-first e os testes de navegação | [preencher] | [preencher] |
| 20/10/2026 | Redesenho visual: `app/static/css/estilo.css`, `app/templates/` (todos), `_icones.html`, fonte Inter local | Claude Code | Reescreveu o CSS e os templates seguindo o prompt de redesenho, sem mudar rotas, motor ou banco; mediu contraste WCAG | [preencher] | [preencher] |
| 20/10/2026 | Roteiro resumido da apresentação (3–4 min) | Claude Code | Escreveu o roteiro, a colinha e as respostas da banca só com os fatos fornecidos (entregue no chat) | [preencher] | [preencher] |

## Compromissos da equipe

- Todo código gerado por IA é lido, entendido e testado por um integrante antes da entrega.
- Nenhum resultado de teste ou feedback de usuário é inventado.
- Nenhum dado pessoal de terceiros, credencial ou a base oficial é enviado a ferramentas de IA
  sem autorização.
