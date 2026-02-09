# analyze-quarter

Gera análise consolidada de retrospectivas de um quarter completo com gráficos comparativos entre sprints.

## Uso

```
analyze-quarter [nome-do-time] [YYYY-QN]
```

## Parâmetros

- `nome-do-time`: Nome do time (ex: financeiro, produto)
- `YYYY-QN`: Quarter no formato ano-trimestre (ex: 2025-Q4)

## Exemplo

```
analyze-quarter financeiro 2025-Q4
```

## O que faz

Esta skill analisa todos os dados CSV das retrospectivas de um quarter e gera 4 gráficos estratégicos:

1. **Evolução do Throughput** - Linha temporal mostrando throughput semanal com identificação de períodos de crise e recuperação
2. **Melhoria na Previsibilidade** - Redução da variabilidade do throughput ao longo do quarter com zonas de referência
3. **Lead Time: Velocidade e Consistência** - Comparação de P90 (consistência) e mediana (velocidade) por semana
4. **Totais por Épico** - Ranking dos top 10 épicos com mais entregas no quarter

## Pré-requisitos

- As retrospectivas devem ter os arquivos CSV:
  - `throughput.csv` - Para gráficos 1 e 2
  - `leadtime.csv` - Para gráfico 3
  - `tickets.csv` - Para gráfico 4

## Saída

Os seguintes arquivos são gerados na pasta do quarter:

### Gráficos (PNG)
- `01_throughput_evolution.png` - Evolução do throughput com análise de tendências
- `02_variability_improvement.png` - Redução da variabilidade e melhoria na previsibilidade
- `03_leadtime_velocity.png` - Velocidade e consistência de entrega
- `04_epic_totals.png` - Ranking de épicos por total de entregas

### Relatório (Markdown)
- `report-quarterly.md` - Relatório consolidado com:
  - Sumário executivo com destaques do quarter
  - Análise detalhada de cada gráfico
  - Insights automáticos baseados nas métricas
  - Avaliação de qualidade e trabalho reativo
  - Recomendações para o próximo quarter
  - Conclusão com diagnóstico geral

## Notas

- A skill detecta automaticamente todas as pastas de retrospectiva dentro do quarter
- O relatório inclui insights inteligentes baseados em thresholds de qualidade
- Recomendações são geradas automaticamente com base nas métricas
- Sprints são identificadas por pastas com formato de data `YYYY-MM-DD`
- Gráficos são gerados em alta resolução (300 DPI)
