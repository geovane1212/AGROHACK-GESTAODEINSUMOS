# Apresentação — SNCT, 29/10/2026

Duração planejada: **6 minutos** (ajustar quando a organização divulgar o tempo). Falas divididas entre os
4 integrantes. Os nomes ao lado de cada bloco são sugestões; troquem conforme a divisão real das frentes.

## 1. Roteiro (6 min)

| Tempo | Quem | Bloco | Fala (resumo) | Tela |
| --- | --- | --- | --- | --- |
| 0:00–0:50 | Integrante 1 | Problema | "Na fazenda, o estoque costuma estar numa planilha ou num caderno. O dado existe, mas ninguém tem tempo de analisar. O resultado: diesel que acaba na colheita, inoculante que vence na prateleira, compra 40% mais cara sem ninguém perceber." | Slide 1–2 |
| 0:50–1:30 | Integrante 1 | Solução | "Não fizemos mais um cadastro. Fizemos um sistema que lê as entradas e saídas e diz **o que merece atenção primeiro, e por quê**." | Slide 3 |
| 1:30–3:30 | Integrante 2 | Demonstração | Painel → data de referência → "O que merece atenção imediata" → abrir "Por que este alerta?" no Diesel → página do produto com o gráfico. **Demo ao vivo** (seção 2). | Sistema |
| 3:30–4:30 | Integrante 3 | Alertas e critérios | "São 7 regras, todas explicáveis: cobertura = saldo ÷ consumo médio; vencimento por lote com FEFO; retirada fora do padrão pela mediana e MAD... Cada estimativa diz a própria confiança." Mostrar qualidade dos dados: sugestão de unificação da Ureia e o fator 1 sc = 50 kg. | Sistema / Slide 4 |
| 4:30–5:20 | Integrante 4 | Como o produtor usaria | "De manhã, pelo celular: abre o painel, vê os críticos, registra a retirada do dia. Quando a base oficial chegar, importa a planilha e confere as colunas, sem mudar o código." Mostrar o painel no celular. | Celular / Slide 5 |
| 5:20–6:00 | Integrante 4 | Validação e limites | "106 testes; o sistema encontrou os 20 problemas que plantamos nos dados simulados. Limites: supõe consumo parecido com o recente, depende de lotes bem registrados, e ainda não teve avaliação de um produtor." | Slide 6 |

## 2. Script da demo ao vivo (reanálise)

Antes de começar: **Importar planilha → Restaurar base de demonstração** (estado conhecido).

1. Painel: "Óleo hidráulico" **não** aparece nos alertas.
2. Menu **Registrar movimentação**:
   - Tipo: Saída · Produto: **Óleo hidráulico** · Quantidade: **60** · Unidade: **L**
   - Data: **30/09/2026** (já vem preenchida) · Destino: Trator 1 · Responsável: Tratorista A
3. **Salvar e reanalisar** → o painel abre com "🔄 O que mudou":
   - 🆕 ⛔ Estoque crítico — Óleo hidráulico
   - 🆕 ⚠️ Retirada fora do padrão — Óleo hidráulico
4. Abrir o alerta de retirada: "60 L em 30/09/2026 (destino: Trator 1; responsável: Tratorista A), 16,2× a
   retirada típica (mediana de 3,7 L)…".
5. (Se houver tempo) **Qualidade dos dados** → confirmar "Ureia" + "UREIA 45%" → cadastrar Ureia 1 sc = 50 kg →
   "O que mudou" mostra os alertas falsos da Ureia **resolvidos**.

> Esse roteiro é testado automaticamente em `tests/test_web.py::test_retirada_grande_gera_alerta_na_reanalise`.

## 3. Plano B (se o link online falhar)

1. Levar um notebook com o projeto clonado e as dependências **já instaladas** (testar na véspera, sem internet).
2. Rodar: `.venv\Scripts\activate` e `flask --app app run` → http://127.0.0.1:5000. O Chart.js está em
   `app/static/`, então os gráficos funcionam sem internet.
3. Se o notebook falhar: capturas de tela de cada passo da demo numa pasta (e no último slide) + o vídeo
   demonstrativo baixado no celular.
4. Celular como segunda tela: na mesma rede Wi-Fi, `flask --app app run --host 0.0.0.0` (sem `--debug`) e abrir
   `http://IP-DO-NOTEBOOK:5000`.

## 4. Slides (enxutos, 6 slides)

1. **Título:** Gestão Inteligente de Insumos · equipe · IFRO Ariquemes.
2. **Problema:** 3 situações reais (diesel acabando, lote vencendo, compra cara) + "o dado existe, falta análise".
3. **Solução:** print do painel com "O que merece atenção imediata" destacado.
4. **Como decidimos:** tabela das 7 regras (copiar da seção 5 do README) + "cada alerta mostra números, regra e limite".
5. **Como o produtor usa:** print no celular + fluxo registrar → reanálise → "o que mudou".
6. **Validação e limites:** 106 testes · 20/20 problemas plantados encontrados · limitações principais · próximos passos (base oficial, feedback de produtor).

## 5. Roteiro do vídeo demonstrativo (até 3 min)

| Cena | Duração | Conteúdo |
| --- | --- | --- |
| 1 | 0:15 | Título e equipe; aviso "dados simulados". |
| 2 | 0:30 | Painel: data de referência, contadores, atenção imediata. |
| 3 | 0:30 | Abrir um alerta crítico e o "Por que este alerta?"; página do produto com gráfico e lotes. |
| 4 | 0:40 | Demo de reanálise (seção 2, passos 1–4). |
| 5 | 0:30 | Qualidade dos dados: unificar Ureia e cadastrar o fator; alertas resolvidos. |
| 6 | 0:20 | Importar uma planilha com outros nomes de coluna (tela de mapeamento). |
| 7 | 0:15 | Como funciona (critérios) e encerramento. |

Gravar a tela em 1280×720 com narração; mostrar uma cena no celular (ou modo responsivo do navegador).

## 6. Perguntas prováveis da banca

1. **Por que não usaram IA ou um modelo de previsão mais complexo?**
   Porque o produtor precisa confiar no alerta e conferir a conta. Média recente, mediana e MAD são simples,
   funcionam com pouco histórico e cada número aparece na justificativa. Um modelo complexo com poucos dados
   daria uma precisão falsa. O edital não exige IA.
2. **Como lidam com poucos dados?**
   Cada estimativa tem um nível de confiança pelo nº de saídas em 60 dias (alta ≥ 10, média 5–9, baixa 2–4).
   Com menos de 2 saídas, não estimamos cobertura. Baixa confiança aparece no texto e reduz a prioridade.
3. **Como evitam unificar produtos diferentes?**
   O sistema nunca unifica sozinho: só sugere, e o usuário confirma. Antes de sugerir, ele bloqueia nomes com
   números diferentes (NPK 04-14-08 x 04-30-16) ou com palavras que especificam o produto diferentes de cada
   lado (filtro de óleo x filtro de ar). Isso tem teste automático.
4. **E se as unidades forem diferentes?**
   g/kg/t e mL/L convertem sempre. Saco, unidade, galão etc. só convertem com fator por produto (1 sc = 50 kg
   de ureia). Sem fator, a movimentação fica fora do cálculo e aparece um aviso: nunca somamos coisas diferentes.
5. **Por que existe uma "data de referência"?**
   Para os alertas não mudarem sozinhos com o passar dos dias. Ela é a data da última movimentação, pode ser
   alterada no topo e permite refazer a análise para qualquer data.
6. **Como definem o que é mais importante?**
   Pela prioridade: severidade (100/50/10) + urgência (dias até o problema) + valor envolvido − incerteza.
   Cada alerta mostra a própria conta.
7. **O que acontece com dado ausente, como preço em branco?**
   Fica ausente (NULL), nunca zero. O produto sai só do cálculo afetado e o painel avisa: "valor calculado sem
   1 produto sem preço".
8. **Como sabem que funciona?**
   106 testes automatizados, um para cada regra e casos de borda. Plantamos 20 problemas nos dados simulados e o
   sistema encontrou todos, sem alertas extras. Mas essa validação foi feita com dados criados por nós, e
   ainda não tivemos um produtor testando.
9. **Como a retirada "fora do padrão" é calculada?**
   Comparamos a retirada com a mediana das outras retiradas dos últimos 90 dias. Usamos a MAD (desvio típico
   pela mediana) porque, ao contrário da média, ela não é puxada pelo próprio pico.
10. **E o vencimento quando a saída não diz o lote?**
    Supomos FEFO: sai primeiro o lote que vence primeiro. É a prática recomendada, mas se a fazenda usou o lote
    novo antes, o alerta pode errar. Isso está escrito no próprio alerta.
11. **Como vão usar a base oficial?**
    Importar planilha → o sistema reconhece as colunas por sinônimos → conferimos o mapeamento → importamos
    substituindo os dados simulados. As unificações e os fatores já confirmados são reaproveitados.
12. **Funciona no celular? E sem internet?**
    A interface é responsiva. Rodando localmente, funciona sem internet (o Chart.js vem junto do projeto). A
    versão online precisa de internet.
13. **Qual regra é mais frágil?**
    Consumo crescente: com poucas saídas por mês, a variação natural pode parecer tendência. Está registrado em
    VALIDACAO.md, com a melhoria que faríamos.
14. **Como a equipe usou IA?**
    Declaramos no AI_USAGE.md: quais ferramentas, em que partes e quem revisou o quê. Todo código foi lido e
    testado por um integrante, e cada um sabe explicar a parte que revisou.
15. **O que fariam com mais tempo?**
    Testar com um produtor real, parâmetros ajustáveis na interface, notificação (e-mail ou Telegram),
    relatório em PDF e uma previsão com intervalo de confiança para produtos com bastante histórico.
