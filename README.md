# Gestão Inteligente de Insumos Rurais — AGROHACK 2026/2

> **Status:** em desenvolvimento (estrutura inicial). Apresentação: 29/10/2026, SNCT.
> Os dados usados até a divulgação da base oficial são **SIMULADOS** (ver `data/simulado/`).

## 1. Equipe

| Nome | Curso | Função no projeto |
| --- | --- | --- |
| Igor Malher | ADS – IFRO Campus Ariquemes | [preencher] |
| Geovane Alencar | ADS – IFRO Campus Ariquemes | [preencher] |
| João Paulo da Costa | ADS – IFRO Campus Ariquemes | [preencher] |
| Edson Henrique | ADS – IFRO Campus Ariquemes | [preencher] |

Responsável pela inscrição/contato com a organização: [preencher].

## 2. Problema e público

**Questão do desafio:** como transformar dados de estoque de uma propriedade rural em informações que
permitam identificar problemas, antecipar necessidades e apoiar decisões de forma simples e eficiente?

**Público:** o responsável pela propriedade (produtor, gerente ou encarregado do almoxarifado), que
consulta o sistema muitas vezes pelo celular, no campo, e precisa de respostas diretas: o que vai
acabar, o que vai vencer, onde há dinheiro parado e o que fazer primeiro.

## 3. Solução

Um sistema web que, além de registrar entradas e saídas, **analisa** o histórico e gera **alertas
priorizados e justificados** em linguagem simples, por exemplo:

> "Estoque crítico: mantendo o consumo médio recente, o saldo atual poderá ser suficiente por
> aproximadamente 8 dias."

Alertas previstos: estoque crítico, cobertura estimada (com nível de confiança), risco de vencimento
(por lote, FEFO), excesso, retirada fora do padrão, consumo crescente, variação de preço e itens de
alto valor parados. Inclui importação de CSV/XLSX com mapeamento de colunas, sugestão (nunca
automática) de unificação de nomes, página de qualidade dos dados e reanálise ao inserir registros.

Arquitetura: `motor/` (análise em Python puro, testável sem Flask) + `app/` (camada web Flask).

## 4. Como testar

**Link online:** [preencher após o deploy]

**Execução local** (Python 3.11+):

```bash
git clone https://github.com/geovane1212/AGROHACK-GESTAODEINSUMOS.git
cd AGROHACK-GESTAODEINSUMOS
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
flask --app app run         # abra http://127.0.0.1:5000
pytest                      # roda os testes
```

## 5. Dados e critérios

[preencher na fase 2] — origem dos dados, tratamentos (unidades, dados ausentes, nomes duplicados),
data de referência, regras de cada alerta, parâmetros, níveis de confiança e quando cada regra pode errar.

## 6. Demonstração

[preencher] — roteiro da demonstração de reanálise, link do vídeo e slides.

## 7. Validação

[preencher] — resumo dos testes e link para `VALIDACAO.md`.

## 8. Tecnologias e IA

- Python, Flask, SQLite, pandas, numpy, rapidfuzz, openpyxl, Chart.js, pytest.
- Uso de IA declarado em [`AI_USAGE.md`](AI_USAGE.md).

## 9. Autoria e licença

Código sob licença [MIT](LICENSE) © 2026 Igor Malher, Geovane Alencar, João Paulo da Costa e
Edson Henrique. Licenças das dependências: [preencher].

## 10. Versão de entrega

A versão avaliada será marcada com a tag `v1.0-entrega`. [preencher link da tag]
