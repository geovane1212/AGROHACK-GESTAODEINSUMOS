# Gestão Inteligente de Insumos Rurais — AGROHACK 2026/2

> Sistema web que transforma o registro de entradas e saídas do almoxarifado de uma propriedade rural em
> **alertas priorizados e explicados**: o que vai acabar, o que vai vencer, onde há dinheiro parado e o que
> está fora do padrão.
>
> ⚠️ Até a divulgação da base oficial, o sistema usa **dados SIMULADOS** ([`data/simulado/`](data/simulado/)).

## 1. Hype Stack

| Nome | Curso | Função no projeto |
| --- | --- | --- |
| Igor Malher | ADS – IFRO Campus Ariquemes | Desenvolvimento & IA |
| Geovane Alencar | ADS – IFRO Campus Ariquemes | Desenvolvimento & IA |
| João Paulo da Costa | ADS – IFRO Campus Ariquemes | Gravação do Vídeo Explicativo |
| Edson Henrique | ADS – IFRO Campus Ariquemes | Apresentação do Pitch |

Responsável pela inscrição/contato com a organização: João Paulo.
Sugestão de divisão das frentes: [`docs/PLANO.md`](docs/PLANO.md).

## 2. Problema e público

**Questão do desafio:** como transformar dados de estoque de uma propriedade rural em informações que
permitam identificar problemas, antecipar necessidades e apoiar decisões de forma simples e eficiente?

**Público:** o responsável pela propriedade (produtor, gerente ou almoxarife), que consulta o sistema muitas
vezes pelo celular, no campo. Ele não precisa de mais um cadastro: precisa saber **o que fazer primeiro**.
Exemplos do que dá errado sem isso: o diesel acaba no meio da colheita, um inoculante vence na prateleira,
uma compra sai 40% mais cara sem ninguém perceber, uma retirada grande passa sem conferência.

## 3. Solução

Um sistema web (Python + Flask) com um **motor de análise** separado da interface:

- **Painel** com a data de referência no topo, contadores por severidade, valor em estoque e
  **"O que merece atenção imediata"** (os alertas de maior prioridade).
- **7 tipos de alerta automáticos:** estoque crítico/baixo, risco de vencimento por lote (FEFO), excesso,
  retirada fora do padrão, consumo crescente, variação de preço e alto valor parado (curva ABC).
- **Cada alerta explica a si mesmo:** números usados, regra aplicada, quando pode errar e a conta da
  prioridade. Exemplo real do sistema:
  > Estoque crítico: mantendo o consumo médio recente (174 L/dia nos últimos 30 dias), o saldo atual
  > (1.000 L) poderá ser suficiente por aproximadamente 6 dias. O estoque mínimo cadastrado é 1.920 L.
  > Confiança alta: 55 saídas nos últimos 60 dias.
- **Reanálise:** ao registrar uma movimentação, importar uma planilha, unificar nomes ou cadastrar um fator,
  tudo é recalculado e o painel mostra **o que mudou** (alertas novos, resolvidos e que mudaram de severidade).
- **Qualidade dos dados:** nomes duplicados (só sugestão, o usuário confirma), unidades inconsistentes,
  preço/validade ausentes, saldo negativo.
- **Importação CSV/XLSX** com reconhecimento de cabeçalhos por sinônimos e tela de mapeamento manual, pronta
  para a base oficial.

Arquitetura:

```
motor/      análise em Python puro (sem Flask), testável isoladamente
  config.py       todos os parâmetros das regras
  preparar.py     data de referência, nomes, unidades
  saldos.py       saldo por produto e lote (FEFO)
  consumo.py      consumo médio, confiança, série semanal
  alertas.py      regras de alerta, severidade e prioridade
  qualidade.py    avisos de qualidade dos dados
  nomes.py        normalização e sugestão de unificação (rapidfuzz)
  unidades.py     conversão de unidades
  importacao.py   leitura de CSV/XLSX e mapeamento de colunas
  analise.py      junta tudo: movimentações → resultado
app/        camada web (Flask + Jinja2 + Chart.js) e banco SQLite
scripts/    gerador da base simulada
tests/      pytest (106 testes)
```

## 4. Como testar

**Link online:** https://agrohack-gestaodeinsumos.vercel.app/

### 4.1 Execução local (Windows, Linux ou Mac, Python 3.11+)

```bash
git clone https://github.com/geovane1212/AGROHACK-GESTAODEINSUMOS.git
cd AGROHACK-GESTAODEINSUMOS
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
flask --app app run            # abra http://127.0.0.1:5000
pytest                         # 106 testes
```

Na primeira execução o banco (`instance/agrohack.db`) é criado e carregado com a base simulada. Para
voltar ao estado inicial a qualquer momento: **Importar planilha → Restaurar base de demonstração**.
O arquivo `.env` é opcional (copie de `.env.example` se quiser fixar `SECRET_KEY`, `DATA_REFERENCIA` etc.).

### 4.2 Roteiro rápido de avaliação (5 minutos)

1. **Painel:** veja a data de referência (30/09/2026), os contadores e os alertas do topo.
2. Abra **"Por que este alerta?"** em qualquer alerta: regra, limite e conta da prioridade.
3. **Registrar movimentação:** saída de **60 L de Óleo hidráulico**, data 30/09/2026 → o painel mostra em
   "O que mudou" dois alertas novos (retirada fora do padrão e estoque crítico).
4. **Qualidade dos dados:** confirme "Ureia" + "UREIA 45%" e cadastre **Ureia: 1 sc = 50 kg** → os alertas
   falsos da Ureia somem.
5. **Importar planilha:** envie um CSV com outros nomes de coluna e confira o mapeamento.
6. Mude a **data de referência** no topo (ex.: 31/08/2026) e veja a análise "voltar no tempo".

### 4.3 Deploy

- **Docker:** `docker build -t insumos . && docker run -p 8000:8000 insumos` → http://localhost:8000
  (o Dockerfile ainda não foi testado localmente; veja `VALIDACAO.md`).
- **Render (plano gratuito):** New → Blueprint → este repositório (usa `render.yaml`). Confira as condições
  atuais do plano gratuito antes de escolher.
- **Disco temporário:** em planos gratuitos sem disco persistente, o SQLite é apagado a cada reinício. O
  sistema recria a base simulada ao iniciar (`SEED_DEMO=1`); o que for cadastrado na versão online se perde
  quando o serviço reinicia. Para a apresentação, o plano B é rodar localmente
  ([`docs/APRESENTACAO.md`](docs/APRESENTACAO.md)).

## 5. Dados e critérios

**Dados:** [`data/simulado/movimentacoes_simulado.csv`](data/simulado/movimentacoes_simulado.csv), 1.722
movimentações fictícias (02/03 a 30/09/2026), geradas por [`scripts/gerar_simulado.py`](scripts/gerar_simulado.py)
com semente fixa. Os problemas plantados estão em
[`GABARITO_SIMULADO.md`](data/simulado/GABARITO_SIMULADO.md). A base oficial vai em `data/oficial/`, que não é
versionada até a organização autorizar.

**Tratamentos:**
- **Data de referência** configurável (padrão: última movimentação); nada usa o relógio do servidor.
- **Unidades:** g/kg/t → kg e mL/L → L automaticamente; sc, un, rolo etc. só com fator por produto. Sem fator,
  a movimentação fica fora do cálculo, com aviso.
- **Dados ausentes:** preço e validade em branco ficam ausentes (NULL), nunca zero; o item sai só do cálculo
  afetado e a interface avisa.
- **Nomes:** grafias idênticas após normalizar maiúsculas/acentos/espaços contam como o mesmo produto. Outras
  diferenças só geram **sugestão** (rapidfuzz ≥ 85%), bloqueada quando números ou especificações diferem.
  Unificações confirmadas ficam na tabela de apelidos e valem para a base oficial.
- **Lotes:** saída sem lote consome o lote que vence primeiro (FEFO).
- **Saldo negativo** vira aviso de qualidade.

**Critérios de alerta** (parâmetros em [`motor/config.py`](motor/config.py); a página **Como funciona** do
sistema mostra os valores em uso):

| Alerta | Regra | Severidade |
| --- | --- | --- |
| Estoque crítico / baixo | saldo ≤ mínimo ou cobertura ≤ 7 dias / ≤ 15 dias | ⛔ / ⚠️ |
| Risco de vencimento | lote com sobra prevista (quantidade − consumo até a validade) que vence em ≤ 30 / 90 / 180 dias; lote vencido com saldo | ⛔ / ⚠️ / ℹ️ |
| Excesso | cobertura > 180 dias; ou sem consumo e saldo > 4× o mínimo | ⚠️ / ℹ️ |
| Retirada fora do padrão | saída dos últimos 30 dias > mediana + 3,5 × MAD e > 2× mediana (histórico de 90 dias, mín. 6 saídas) | ⚠️ |
| Consumo crescente | 3 blocos de 30 dias sempre maiores, alta ≥ 30%, ≥ 2 saídas por bloco (sem contar retiradas fora do padrão) | ⚠️ |
| Variação de preço | última compra ≥ 20% acima/abaixo da mediana das anteriores (por unidade base) | ⚠️ / ℹ️ |
| Alto valor parado | classe A da curva ABC e sem saída há ≥ 60 dias ou giro de 90 dias ≤ 10% | ⚠️ |

**Consumo e confiança:** consumo médio diário dos últimos 30 dias (60 se houver menos de 5 saídas em 30
dias). Confiança pelo nº de saídas em 60 dias: **alta ≥ 10, média 5–9, baixa 2–4, sem estimativa < 2**.

**Prioridade:** Crítico 100 / Atenção 50 / Informativo 10 + urgência (30 − dias, se houver prazo) + valor
envolvido (1 ponto a cada R$ 500, máx. 20) − 10 se a confiança for baixa.

**Limites das estimativas:** veja a coluna "quando pode errar" na página Como funciona e a seção 5 de
[`VALIDACAO.md`](VALIDACAO.md).

## 6. Demonstração

- Roteiro da apresentação, script da demo ao vivo, perguntas da banca e plano B:
  [`docs/APRESENTACAO.md`](docs/APRESENTACAO.md).
- **Atualização e reanálise:** ver passo 3 da seção 4.2 (também automatizado em
  `tests/test_web.py::test_retirada_grande_gera_alerta_na_reanalise`).
- Vídeo demonstrativo: [EM DESENVOLVIMENTO]. Slides: [preencher link].

## 7. Validação

**106 testes automatizados passando**, incluindo um teste de ponta a ponta que encontra **20 de 20 problemas
plantados** na base simulada, sem alertas extras. Detalhes, limitações conhecidas e o que precisa melhorar:
[`VALIDACAO.md`](VALIDACAO.md). Até agora **não houve** feedback de produtor ou de Agronomia.

## 8. Tecnologias e IA

| Tecnologia | Uso | Licença |
| --- | --- | --- |
| Python 3 | linguagem | PSF |
| Flask 3 | camada web | BSD-3-Clause |
| SQLite (sqlite3) | banco de dados | domínio público |
| pandas, numpy | análise | BSD-3-Clause |
| rapidfuzz | similaridade de nomes | MIT |
| openpyxl | leitura de XLSX | MIT |
| python-dotenv | variáveis de ambiente | BSD-3-Clause |
| Chart.js 4.4.1 (em `app/static/`) | gráficos | MIT |
| pytest | testes | MIT |
| gunicorn | servidor em produção (Linux) | MIT |
| Ícones Lucide 0.460.0 (sprite em `app/static/img/icones.svg`) | ícones da interface | ISC ([licença](app/static/img/LICENSE-lucide.txt)) |
| Fonte Inter 4 (arquivos em `app/static/fonts/`, via @fontsource-variable/inter 5.1.0) | tipografia | SIL OFL 1.1 ([licença](app/static/fonts/LICENSE-inter.txt)) |

Uso de IA declarado em [`AI_USAGE.md`](AI_USAGE.md) (ferramentas, partes apoiadas e revisão humana).
Os ícones são do projeto Lucide (licença ISC) e a fonte é a Inter (licença OFL), ambos guardados no próprio projeto; não há outras imagens de terceiros.

## 9. Autoria e licença

Código sob licença [MIT](LICENSE) © 2026 Igor Malher, Geovane Alencar, João Paulo da Costa e Edson Henrique.
Dados simulados criados pela equipe. Contribuição: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 10. Versão de entrega

A versão avaliada será marcada com a tag **`v1.0-entrega`**. [preencher link da tag]
