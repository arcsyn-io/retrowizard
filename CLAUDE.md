# CLAUDE.md

Orientações para o Claude Code ao trabalhar neste repositório de retrospectivas.

## Estrutura

```
[time]/[YYYY-QN]/[YYYY-MM-DD]/
├── cfd.csv/png           # Cumulative Flow Diagram
├── throughput.csv/png    # Vazão semanal
├── leadtime.csv/png      # Distribuição de lead time
├── tickets.csv/png       # Tipos de itens
├── retrocards.md         # Feedback do time
└── report.md             # Relatório final

[time]/status-report-semanal/
└── status_report-{ANO}_W{SEMANA}.md  # Status report semanal
```

## Skills Disponíveis

### /analyze-retro

Analisa uma retrospectiva e gera o `report.md`.

```
/analyze-retro [time]/[YYYY-QN]/[YYYY-MM-DD]/
```

**Pré-requisitos**: PNGs já gerados (cfd.png, throughput.png, leadtime.png, tickets.png)

**Template**: `.claude/skills/analyze-retro/Template.md`

### /status-report

Gera status report semanal para stakeholders e liderança de engenharia.

```
/status-report [time]
```

**Exemplo**: `/status-report financeiro`

**Fluxo**:
1. Busca tickets do Jira (últimas 2 semanas)
2. Pergunta sobre contexto da semana anterior
3. Pergunta sobre foco da semana atual
4. Pergunta sobre pedidos/necessidades
5. Gera `status_report-{ANO}_W{SEMANA}.md`

**Template**: `.claude/skills/status-report/Template.md`

## Comandos Úteis

```bash
# Wizard interativo (recomendado)
./retro-wizard.py

# Extrair dados do Jira
python3 jira_extracter.py --days 14 --output-dir [time]/[YYYY-QN]/[YYYY-MM-DD]

# Gerar gráficos
python3 generate_metrics_charts.py [time]/[YYYY-QN]/[YYYY-MM-DD]/
```

## Idioma

Todo conteúdo em **Português (Brasil)**.
