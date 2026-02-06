# Retrospectives

Repositório para gerenciamento de retrospectivas de sprint.

## Propósito

- Templates e retrospectivas organizadas por time e data
- Ferramentas Python para gerar gráficos a partir de dados do Jira
- Rastreamento de métricas (throughput, lead time, CFD)

## Estrutura de Diretórios

```
/
├── .env                           # Configuração do Jira (não versionado)
├── .venv/                         # Ambiente virtual Python (automático)
├── retro-wizard.py                # Wizard interativo
├── jira_extracter.py              # Extração de dados do Jira
├── generate_metrics_charts.py     # Geração de gráficos PNG
├── .claude/skills/                # Skills do Claude Code
│   └── analyze-retro/             # Skill de análise
│       ├── SKILL.md
│       └── Template.md
└── [time]/                        # Pasta de cada time
    └── YYYY-QN/                   # Pastas trimestrais
        └── YYYY-MM-DD/            # Retrospectivas datadas
            ├── cfd.csv/png
            ├── throughput.csv/png
            ├── leadtime.csv/png
            ├── tickets.csv/png
            ├── retrocards.md
            └── report.md
```

## Início Rápido

### Wizard Interativo (Recomendado)

```bash
./retro-wizard.py
```

Opções disponíveis:
1. **Fluxo Completo** - Cria estrutura + Extrai Jira + Gera gráficos + Analisa
2. **Criar Estrutura** - Apenas cria diretórios
3. **Extrair Dados do Jira** - Apenas extração automática
4. **Gerar Gráficos** - Apenas geração de PNGs
5. **Analisar com Claude** - Apenas análise e report.md

### Configuração do Jira

Crie um arquivo `.env` na raiz:

```bash
JIRA_EMAIL=seu-email@empresa.com
JIRA_API_TOKEN=seu-token-aqui
JIRA_SITE=seusite.atlassian.net
JIRA_BOARD_<TIME>=<board-id>
```

Crie um token em: https://id.atlassian.com/manage-profile/security/api-tokens

## Comandos Manuais

### Extrair Dados do Jira

```bash
python3 jira_extracter.py --days 14 --output-dir [time]/[YYYY-QN]/[YYYY-MM-DD]
```

Arquivos gerados:
- `cfd.csv` - Cumulative Flow Diagram
- `throughput.csv` - Throughput semanal
- `leadtime.csv` - Distribuição de lead time
- `tickets.csv` - Detalhes dos tickets

### Gerar Gráficos

```bash
# Todos os gráficos de uma retrospectiva
python3 generate_metrics_charts.py [time]/[YYYY-QN]/[YYYY-MM-DD]/

# Apenas gráfico de tickets de um CSV
python3 generate_metrics_charts.py tickets.csv [saida.png]
```

Gráficos gerados:
- `cfd.png` - Cumulative Flow Diagram
- `throughput.png` - Vazão semanal com médias
- `leadtime.png` - Distribuição com percentis
- `tickets.png` - Distribuição de tipos de itens

## Formatos de Dados

### CFD (`cfd.csv`)
- Colunas: `Date`, `TESTING`, `READY TO TEST`, `CODE REVIEW`, `IN PROGRESS`
- Snapshots diários do trabalho em cada coluna

### Throughput (`throughput.csv`)
- Colunas: `Period`, `Throughput`
- Agregação semanal no formato `YYYY-MM-DD`

### Lead Time (`leadtime.csv`)
- Colunas: `Leadtime`, `item count`
- Lead time em dias

### Tickets (`tickets.csv`)
- Deve conter a coluna: `Tipo de item`
- Exportação do Jira

## Estrutura da Retrospectiva

O `report.md` segue o template em `.claude/skills/analyze-retro/Template.md`:

1. **Identificação do Ciclo** - Período, time, facilitador
2. **Resumo Executivo** - Métricas chave
3. **Conquistas/Desafios**
4. **Análise de Métricas** - CFD, throughput, lead time
5. **Retrospectiva Qualitativa** - "Mandamos bem" / "Precisamos melhorar"
6. **Ações Definidas** - Itens de ação

### Cards de Retrospectiva (`retrocards.md`)

- Itens com `(+N)` indicam múltiplos votos
- Organizados em: Mandamos bem, Precisamos melhorar, Ações

## Ambiente Python

O ambiente virtual é gerenciado automaticamente. Para operações manuais:

```bash
source .venv/bin/activate
pip install pandas matplotlib requests
```

## Times Ativos

Configurados via variável de ambiente `JIRA_BOARD_<TIME>` no `.env`.
