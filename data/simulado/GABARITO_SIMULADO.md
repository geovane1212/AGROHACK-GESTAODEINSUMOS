# Gabarito da base SIMULADA

> Dados **fictícios**, gerados por `scripts/gerar_simulado.py` com semente fixa (42).
> Período: 02/03/2026 a 30/09/2026 · 1.722 movimentações · 40 produtos.
> Data de referência padrão: **30/09/2026** (última movimentação).

Este arquivo lista os problemas **plantados de propósito** para conferir se o sistema os encontra.
A conferência é automática em `tests/test_gabarito.py`; o resultado está em [`VALIDACAO.md`](../../VALIDACAO.md).

## Problemas plantados

| ID | Situação do edital | Produto | Como foi plantado | O sistema deve mostrar |
| --- | --- | --- | --- | --- |
| G01 | Estoque crítico (cobertura) | Diesel S10 | Compras param em 10/09; termina com 1.000 L e consumo de ~170 L/dia | Estoque crítico, ⛔ Crítico, ~6 dias de cobertura |
| G02 | Estoque crítico (mínimo) | Glifosato 480 | Termina com 80 L; mínimo de 120 L | Estoque crítico, ⛔ Crítico, "abaixo do estoque mínimo" |
| G03 | Consumo crescente | Fungicida azoxistrobina | Retiradas 1,5× maiores entre 31–60 dias atrás e 2,3× nos últimos 30 dias | Consumo crescente, ⚠️ Atenção |
| G04 | Excesso de estoque | Graxa | Compra inicial para ~800 dias de consumo e nenhuma reposição | Excesso de estoque, ⚠️ Atenção (cobertura > 180 dias) |
| G05 | Retirada fora do padrão | Óleo de motor 15W40 | Retiradas típicas de ~5 L; uma de 60 L em 20/09 (Trator 2, Tratorista B) | Retirada fora do padrão, ⚠️ Atenção |
| G06 | Variação relevante de preço | Cloreto de potássio (KCl) | Última compra a R$ 4,28/kg contra ~R$ 3,00/kg nas anteriores | Variação de preço, ⚠️ Atenção (~43% acima) |
| G07 | Risco de vencimento | Inoculante para soja | Lote INO-2604 vence em 20/10/2026 com 22 L e consumo de ~0,1 L/dia | Risco de vencimento, ⛔ Crítico |
| G08 | Risco de vencimento (vencido) | Trichoderma | Lote TRI-01 venceu em 15/09/2026 com 6 kg; as retiradas passaram a informar o lote novo | Lote vencido, ⛔ Crítico |
| G09 | Risco de vencimento | Semente de feijão | Lote de 600 kg vence em 10/12/2026; consumo de ~1,5 kg/dia | Risco de vencimento, ⚠️ Atenção |
| G10 | Alto valor com baixa movimentação | Inseticida clorantraniliprole | 18 L a R$ 850/L; última saída em 20/05 | Alto valor parado, ⚠️ Atenção |
| G11 | Alto valor com baixa movimentação | Correia da colheitadeira | 4 un a R$ 2.800; nenhuma saída | Alto valor parado, ⚠️ Atenção |
| G12 | Mesmo produto com nomes diferentes | "Ureia", "UREIA 45%", "ureia granulada" | Três grafias em compras e retiradas | 3 sugestões de unificação (nunca automáticas) |
| G13 | Mesmo produto com nomes diferentes | "Luva nitrílica" / "Luvas nitrilicas" | ~40% das retiradas desde agosto com o nome no plural | 1 sugestão de unificação |
| G14 | Grafias que diferem só em acento/maiúsculas | "Óleo hidráulico", "Oleo hidraulico", "ÓLEO HIDRÁULICO" | 30% das linhas com outra grafia | Tratados como 1 produto + aviso "grafias equivalentes" |
| G15 | Formulações parecidas que **não** são o mesmo produto | NPK 04-14-08 x NPK 04-30-16; Filtro de óleo x Filtro de ar | Produtos normais | **Nenhuma** sugestão de unificação |
| G16 | Unidades mistas sem fator | Ureia | Compras em sacos (sc), retiradas em kg | Aviso "unidade inconsistente" (compras em sc fora do cálculo) |
| G17 | Unidades da mesma grandeza | Adjuvante | Compras em L, retiradas em mL | Convertido automaticamente, sem aviso |
| G18 | Preço ausente | Atrazina (2 de 5 compras); Estacas de eucalipto (todas) | Preço em branco | Aviso "preço ausente"; valor em estoque "calculado sem 1 produto" |
| G19 | Validade ausente | Atrazina (1 compra); Semente de soja (2 compras) | Validade em branco | Aviso "validade ausente" |
| G20 | Saldo negativo | Bico de pulverização | 12 un compradas, 15 retiradas | Aviso "saldo negativo" + Estoque crítico (sem estoque) |

## Consequências esperadas (somem depois das correções)

Esses alertas aparecem **por causa** dos problemas G12, G13 e G16 e devem desaparecer quando o usuário
confirmar as unificações e cadastrar o fator **Ureia: 1 sc = 50 kg** na página de qualidade dos dados.

| ID | Alerta | Motivo |
| --- | --- | --- |
| C1 | Ureia: Estoque crítico + saldo negativo | As compras em sc ficam fora do saldo em kg até existir o fator |
| C2 | Luvas nitrilicas: Estoque crítico + saldo negativo | Retiradas lançadas com outro nome, sem entradas com esse nome |
| C3 | UREIA 45%: Alto valor parado | As retiradas desse produto foram lançadas como "Ureia" |

## Produtos sem problema plantado

NPK 04-14-08, NPK 04-30-16, MAP, Sulfato de amônio, FTE BR-12, Gesso agrícola, Calcário dolomítico,
Semente de milho, Braquiária, Herbicida 2,4-D, Azospirillum, Filtro de óleo, Filtro de ar, Rolamento 6205,
Mangueira de gotejamento, Conector de irrigação, Respirador PFF2, Bota de borracha, Adjuvante (só G17),
Óleo hidráulico (só G14). **Nenhum alerta é esperado para eles.**

## Honestidade sobre a geração

- As retiradas de rotina saem a cada ~N dias com variação aleatória de ±15% na quantidade; as compras
  acontecem quando o estoque cai abaixo de ~35 dias de consumo. Dados reais costumam ser mais irregulares.
- Numa primeira versão do gerador, as retiradas eram sorteadas dia a dia, e isso produziu "consumo crescente"
  por acaso em dois produtos (FTE BR-12 e Graxa). Passamos a usar intervalos mais regulares, que parecem mais
  com a rotina de uma fazenda. **A regra continua sensível a esse tipo de ruído**, o que está registrado como
  limitação em `VALIDACAO.md`.
- Responsáveis e fornecedores são genéricos ("Tratorista A", "Cooperativa C"), sem dados pessoais.
