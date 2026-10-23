# Diagnóstico da interface v1 (Fase 0 da v2)

Feito em 19/10/2026 sobre a tag `v1.0-mvp`, com o servidor local e a base simulada.

**Como foi medido:** Microsoft Edge controlado pelo Playwright, em 360 × 800 (celular, com toque), 768 × 800
(tablet) e 1280 × 800 (computador). Para cada tela: captura da página inteira (cortada em 5.000 px), rolagem
horizontal, elementos clicáveis com menos de 48 × 48 px, textos com menos de 16 px, tempo de carregamento e
bytes transferidos. Capturas em [`docs/screenshots/v1/`](screenshots/v1/) e números em
[`metricas.json`](screenshots/v1/metricas.json).

> Os tempos são do servidor local de desenvolvimento, no mesmo computador; **não** representam internet
> fraca de verdade. Lighthouse ainda não foi rodado.

## 1. Números medidos (360 px)

| Tela | Rolagem horizontal | Altura da página | Clicáveis < 48 px | Textos < 16 px | Carregamento | Transferido |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Painel | não | 5.708 px | 35 de 42 | 68 | 185 ms | 226 KB |
| Alertas | não | 6.755 px | 41 de 48 | 170 | 38 ms | 23 KB |
| Estoque | não | 3.484 px | 56 de 56 | 35 | 25 ms | 19 KB |
| Produto (Diesel) | não | 4.613 px | 15 de 16 | 24 | 64 ms | 16 KB |
| Registrar | não | 1.926 px | 28 de 28 | 6 | 24 ms | 7 KB |
| Importar | não | 1.772 px | 17 de 17 | 6 | 22 ms | 5 KB |
| Conferir colunas | não | 2.349 px | 29 de 29 | 5 | 50 ms | 11 KB |
| Qualidade | não | 4.756 px | 39 de 43 | 15 | 33 ms | 12 KB |
| Histórico | não | **19.575 px** | 15 de 15 | 5 | 67 ms | 72 KB |
| Como funciona | não | 7.533 px | 13 de 13 | 5 | 32 ms | 10 KB |

Contraste (WCAG): todos os pares de texto passam do AA (o menor é o menu, branco sobre verde, 6,4:1). A borda
dos cartões (1,5:1) quase some sob luz forte.

## 2. Problemas encontrados

### Críticos para o produtor no celular
1. **O que resolver hoje fica longe.** No painel em 360 px, o primeiro alerta só aparece depois de ~1.000 px
   (cabeçalho + 5 contadores empilhados). É preciso rolar mais de uma tela para chegar ao principal.
2. **Topo pesado em todas as telas:** aviso + título + menu + formulário de data de referência ocupam
   ~290 px de 800 antes do conteúdo.
3. **Menu escondido:** no celular, o menu rola na horizontal e só "Painel, Alertas, Estoque" aparecem; Importar,
   Qualidade, Histórico e Como funciona ficam fora da tela, sem indicação.
4. **Registrar é lento:** 13 campos visíveis, produto e unidade digitados à mão, sem − / +, sem lembrar destino
   e responsável. Não existe atalho direto para "retirada" ou "entrada".
5. **Alvos de toque pequenos:** quase todos os links, botões e campos têm menos de 48 px de altura (ex.:
   itens do menu com ~40 px, botões "pequeno" com ~30 px, links de tabela com ~24 px).
6. **Tabelas ilegíveis no celular:** Estoque tem 10 colunas; no celular só se veem 2–3, o resto exige rolar
   a tabela para o lado. Histórico tem 300 linhas (19.575 px de altura).
7. **Alerta sem ação:** o texto diz o problema, mas não o que fazer ("comprar quanto?", "usar qual lote?").

### Importantes
8. **Jargão:** "cobertura", "confiança", "classe ABC", "Prioridade 131", "saldo calculado", "unidade base",
   "FEFO", "MAD" aparecem na tela principal.
9. **Textos de apoio < 16 px** (legendas, selos, tabelas da página Como funciona com 13,8 px).
10. **Busca de produto** só existe no Histórico; não há busca global com autocompletar.
11. **Painel carrega o Chart.js (200 KB)** mesmo para quem só quer ver os alertas; gráficos ficam pequenos no
    celular.
12. **Página do produto:** 6 cartões empilhados antes do gráfico; um único botão "Registrar movimentação".
13. **Sem lista de compras, sem relatório para imprimir, sem filtro de período nos gráficos.**
14. **Ícones são emojis:** a aparência muda de um celular para outro e alguns ficam pouco nítidos.

### Menores
15. Formulário de data de referência repetido no topo de toda página (devia ser um selo pequeno com link).
16. Datas da reanálise em formato técnico ("2026-10-19 21:45:52").
17. Botão de voltar só existe na página do produto.
18. Sem CSS de impressão, sem modo escuro, sem `aria-live` explícito no aviso de reanálise (as mensagens
    usam `role="status"`, que já anuncia, mas o aviso "o que mudou" não).

### O que já está bom
Sem rolagem horizontal em nenhuma tela; contraste do texto alto; severidade com ícone + texto + cor; páginas
leves (5–72 KB, exceto o Chart.js); funciona sem JavaScript, exceto os gráficos.

## 3. Plano proposto (por prioridade)

| Fase | O quê | Muda o motor? |
| --- | --- | --- |
| 1 | Sistema de design (tokens CSS, macros), ícones SVG, barra inferior no celular / menu lateral no computador, botão "+ Registrar" com atalhos, busca global com autocompletar, topo compacto, tabelas viram cards no celular, alvos ≥ 48 px | Não |
| 2 | Início "Hoje na fazenda", card de alerta com **ação sugerida**, página do produto, registrar em 3 toques (− / +, lembra destino e responsável, aviso de reanálise), Estoque com busca e filtros | Sim: campo `acao` no alerta (com testes) |
| 3 | Transições curtas, `prefers-reduced-motion`, filtros sem recarregar (com fallback), Chart.js só onde há gráfico, cache de estáticos, "ver como tabela", botão de fonte maior, linguagem simples, erros amigáveis, ajuda "?" | Não |
| 4 | Lista de compras (N dias, WhatsApp, impressão), relatório para imprimir, filtro de período, testes novos | Sim: função pura de lista de compras (com testes) |
| 5 | PWA, QR Code por produto, modo escuro, tela de Configurações | Talvez (parâmetros ajustáveis) |
