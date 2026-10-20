# Validação

Situação em **19/10/2026**. Tudo o que está aqui foi executado de fato; nada foi estimado ou inventado.

## 1. Testes automatizados

Comando: `pytest` · Resultado: **106 testes, 106 passaram** (≈ 35 s, Python 3.14, Windows 11).

| Arquivo | Testes | O que cobre |
| --- | ---: | --- |
| `tests/test_alertas.py` | 22 | Cada regra de alerta, com casos que devem e que **não** devem disparar: cobertura crítica e baixa, abaixo do mínimo, baixa confiança, lote a vencer, lote vencido, lote consumido a tempo, validade ausente, excesso, retirada fora do padrão, variação normal, poucas saídas, consumo crescente e estável, pico isolado que não é tendência, preço por unidade base, alto valor parado, item sem preço, ordenação por prioridade |
| `tests/test_saldos_consumo.py` | 15 | Saldo, FEFO com e sem lote informado, saldo negativo, níveis de confiança, consumo zero, histórico curto, janela de 30/60 dias, preço ausente ≠ zero, validade ausente, unidades mistas com e sem fator, g + kg, apelidos, data de referência |
| `tests/test_nomes_unidades.py` | 14 | Normalização, sugestões corretas (Ureia/UREIA 45%/ureia granulada, Luva/Luvas), bloqueios (NPK 04-14-08 x 04-30-16, Filtro de óleo x de ar, Óleo de motor x hidráulico, Semente de milho x soja), par rejeitado, conversões e sinônimos de unidade |
| `tests/test_importacao.py` | 9 | Sinônimos de cabeçalho, CSV com `;` e Latin-1, XLSX, números brasileiros, linha inválida recusada com motivo, preço/validade ausentes, preço zero, coluna obrigatória faltando |
| `tests/test_web.py` | 9 | Retirada grande gera alerta na reanálise (roteiro da demo), registro inválido, unificação, fator de unidade, rejeição de sugestão, importação com outros nomes de coluna, substituição da base, data de referência, restauração da demo |
| `tests/test_gabarito.py` | 34 | Ponta a ponta contra o gabarito (seção 2) |
| `tests/test_estrutura.py` | 3 | Motor não depende do Flask; todas as páginas abrem; aviso de dados simulados |

## 2. Teste de ponta a ponta contra o gabarito

O CSV simulado é importado pelo mesmo caminho do usuário (mapeamento automático de colunas) e os
resultados são comparados com [`data/simulado/GABARITO_SIMULADO.md`](data/simulado/GABARITO_SIMULADO.md).

| ID | Problema plantado | Encontrado? | Como apareceu |
| --- | --- | --- | --- |
| G01 | Diesel S10 crítico | ✅ | ⛔ Estoque crítico: ~6 dias de cobertura, confiança alta |
| G02 | Glifosato abaixo do mínimo | ✅ | ⛔ Estoque crítico: 80 L, mínimo 120 L |
| G03 | Fungicida com consumo crescente | ✅ | ⚠️ Consumo crescente: 48,8 → 73 → 94 L (+93%) |
| G04 | Graxa em excesso | ✅ | ⚠️ Excesso: ~611 dias de cobertura |
| G05 | Retirada de 60 L de óleo de motor | ✅ | ⚠️ Fora do padrão: 12,5× a mediana, com destino e responsável |
| G06 | KCl mais caro | ✅ | ⚠️ Variação de preço: 43% acima da mediana |
| G07 | Inoculante vencendo | ✅ | ⛔ Risco de vencimento: ~20 L podem vencer em 20 dias |
| G08 | Trichoderma vencido | ✅ | ⛔ Lote vencido: 6 kg desde 15/09 |
| G09 | Semente de feijão vencendo | ✅ | ⚠️ Risco de vencimento: ~326 kg de sobra em 71 dias |
| G10 | Inseticida caro parado | ✅ | ⚠️ Alto valor parado: R$ 15.300, sem saída há 133 dias |
| G11 | Correia cara parada | ✅ | ⚠️ Alto valor parado: R$ 11.200, nenhuma saída |
| G12 | Ureia com 3 grafias | ✅ | 3 sugestões de unificação |
| G13 | Luva/Luvas | ✅ | 1 sugestão (similaridade 93%) |
| G14 | Óleo hidráulico com acentos diferentes | ✅ | 1 produto + aviso "grafias equivalentes" |
| G15 | NPK e filtros diferentes | ✅ | Nenhuma sugestão (bloqueados) |
| G16 | Ureia em sc e kg | ✅ | Aviso "unidade inconsistente" |
| G17 | Adjuvante em L e mL | ✅ | Convertido sem aviso |
| G18 | Preço ausente | ✅ | Avisos + "valor calculado sem 1 produto sem preço" |
| G19 | Validade ausente | ✅ | Avisos em Atrazina e Semente de soja |
| G20 | Bico com saldo negativo | ✅ | Aviso de saldo negativo + estoque crítico |

**Resultado: 20 de 20 problemas plantados encontrados.** Os 3 alertas de consequência (C1–C3) aparecem e
**somem** depois de confirmar as unificações e cadastrar o fator 1 sc = 50 kg (teste
`test_correcoes_resolvem_as_consequencias`). Nenhum alerta apareceu nos 20 produtos sem problema
plantado (teste `test_nenhum_alerta_fora_do_gabarito`).

> Atenção à leitura deste resultado: o gerador e as regras foram feitos pela mesma equipe. Acertar o próprio
> gabarito mostra que as regras fazem o que prometem, mas **não prova** que funcionam bem em dados reais.
> Isso só vai ser verificado com a base oficial.

## 3. Verificações manuais

- Todas as páginas foram abertas no navegador (servidor local) e capturadas em 1280 px e 375 px de largura
  (Edge em modo headless). No celular, o menu rola na horizontal e as tabelas rolam dentro do próprio bloco.
- A severidade aparece sempre com **ícone + texto + cor** (⛔ Crítico, ⚠️ Atenção, ℹ️ Informativo).
- O gerador de dados é reproduzível: duas execuções produziram arquivos idênticos (mesmo hash MD5).
- A análise completa da base simulada (1.722 linhas) leva cerca de 1 segundo; depois fica em cache até
  a próxima mudança.

## 4. O que funciona

Importação CSV/XLSX com mapeamento de colunas; cadastro manual com validação; saldo por produto e lote;
os 7 tipos de alerta com severidade, prioridade explicável e justificativa com números; reanálise com
"o que mudou"; sugestão e confirmação de unificação de nomes com tabela de apelidos; fatores de conversão
por produto; página de qualidade dos dados; data de referência configurável; exportação dos alertas em CSV;
página "Como funciona" gerada a partir dos parâmetros reais.

## 5. Limitações conhecidas e o que precisa melhorar

1. **Consumo crescente é sensível a ruído.** Com poucas saídas por mês, a variação natural pode formar três
   meses seguidos de alta. Aconteceu na primeira versão do gerador (veja o gabarito). Melhoria possível:
   exigir mais saídas por bloco ou usar uma regressão com teste de significância.
2. **Retirada fora do padrão x tendência.** Em produtos com consumo subindo, uma retirada grande pode ser
   apenas o novo normal. Reduzimos o histórico de comparação para 90 dias, mas o risco continua. No sentido
   inverso, um pico isolado não vira "consumo crescente": retiradas fora do padrão ficam fora da conta da
   tendência (encontramos esse problema testando a demo e corrigimos, com teste).
3. **A cobertura supõe consumo constante** e não conhece compras feitas e ainda não lançadas, nem o
   calendário da safra.
4. **FEFO é uma suposição:** se na prática o lote novo foi usado primeiro, o alerta de vencimento erra.
5. **Fatores de unidade são manuais:** o sistema não adivinha quantos kg tem um saco.
6. **Equivalência automática de grafias:** nomes que só diferem em maiúsculas, acentos ou espaços são juntados
   sem perguntar. Achamos o risco muito baixo, mas é uma decisão nossa e está documentada.
7. **Curva ABC e valor parado só usam itens com preço.**
8. **Sem login e sem multiusuário:** pensado para uma propriedade, uma pessoa por vez.
9. **Dockerfile não foi testado localmente** (o Docker não estava instalado na máquina de desenvolvimento).
10. **Deploy online ainda não feito.** Em planos gratuitos com disco temporário, o banco volta para os dados
    simulados a cada reinício (comportamento documentado no README).

## 6. Feedback de usuários

**Até 19/10/2026 não houve feedback de produtor rural nem de alguém de Agronomia.** Se conseguirmos antes da
apresentação, registraremos aqui quem avaliou (sem dados pessoais), o que foi testado e o que foi dito.
