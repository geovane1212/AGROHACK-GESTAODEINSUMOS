# Como contribuir

Fluxo de trabalho da equipe. Siga sempre estes passos.

## 1. Primeira vez

```bash
git clone https://github.com/geovane1212/AGROHACK-GESTAODEINSUMOS.git
cd AGROHACK-GESTAODEINSUMOS
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
pytest                      # tudo deve passar
flask --app app run         # http://127.0.0.1:5000
```

## 2. Antes de começar o dia

```bash
git checkout main
git pull
git checkout feat/<sua-tarefa>
git merge main              # traz o que os colegas já integraram
```

## 3. Uma branch por tarefa

Nunca trabalhe direto na `main`.

```bash
git checkout -b feat/<tarefa>     # ex.: feat/motor-alertas, feat/painel, docs/readme
```

## 4. Commits pequenos, em português

Padrão `tipo: descrição`:

- `feat:` nova funcionalidade (`feat: alerta de risco de vencimento por lote`)
- `fix:` correção (`fix: cobertura não divide por zero sem saídas`)
- `docs:` documentação
- `test:` testes
- `chore:` configuração, dependências, estrutura

## 5. Enviar e abrir Pull Request

```bash
pytest                            # rode os testes ANTES de abrir o PR
git push -u origin feat/<tarefa>
```

Abra um Pull Request para a `main` no GitHub. **Outro integrante revisa antes do merge.**
Se usou IA na tarefa, registre em `AI_USAGE.md` no mesmo PR.

## 6. Nunca versionar

- `.env` (segredos)
- bancos `.db` / `.sqlite3`
- a base oficial (`data/oficial/`)

## 7. Versão de entrega

A versão avaliada será marcada com a tag `v1.0-entrega`.
