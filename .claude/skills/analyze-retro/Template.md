# 📊 Retrospectiva {{Time}} — {{Data}}

## Identificação
- **Ciclo:** {{Sprint/Iteração}}
- **Período:** {{Início}} — {{Fim}}
- **Time:** {{Nome}}
- **Facilitador:** {{Nome}}

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Throughput médio | {{N}} itens/semana |
| Lead Time p90 | {{N}} dias |
| Bugs | {{N}} ({{%}}) |
| Incidentes | {{N}} ({{%}}) |

## Fluxo de Trabalho (CFD)

![CFD](./cfd.png)

**Análise:**
- WIP médio: {{N}} itens
- {{Observações}}

## Throughput

![Throughput](./throughput.png)

| Métrica | Valor |
|---------|-------|
| Média | {{N}} itens/semana |
| Desvio padrão | {{N}} itens/semana |
| CV | {{N}}% |
| Previsibilidade | {{Alta/Média/Baixa}} |
| Capacidade (85%) | {{N}} — {{N}} itens/semana |
| Tendência | {{Crescente 📈 / Estável ➡️ / Decrescente 📉}} |

{{#se houver ciclo anterior}}
**Comparação com ciclo anterior:**

| Métrica | Anterior | Atual | Variação |
|---------|----------|-------|----------|
| Média | {{N}} | {{N}} | {{+/-N%}} {{📈/📉/➡️}} |
{{/se houver ciclo anterior}}

**Análise:** {{Tendências e observações}}

## Lead Time

![Lead Time](./leadtime.png)

| Métrica | Valor |
|---------|-------|
| p50 | {{N}} dias |
| p90 | {{N}} dias |
| Desvio padrão | {{N}} dias |

{{#se houver ciclo anterior}}
**Comparação com ciclo anterior:**

| Métrica | Anterior | Atual | Variação |
|---------|----------|-------|----------|
| p50 | {{N}} dias | {{N}} dias | {{+/-N%}} {{📈/📉/➡️}} |
| p90 | {{N}} dias | {{N}} dias | {{+/-N%}} {{📈/📉/➡️}} |
| Desvio padrão | {{N}} dias | {{N}} dias | {{+/-N%}} {{📈/📉/➡️}} |
{{/se houver ciclo anterior}}

**Categorias:**
- Rápidos (≤5d): {{N}} ({{%}})
- Normais (6-10d): {{N}} ({{%}})
- Lentos (>10d): {{N}} ({{%}})

## Distribuição de Tipos

![Tickets](./tickets.png)

| Tipo | Quantidade | % |
|------|-----------|---|
| {{Tipo}} | {{N}} | {{%}} |

**Alertas:**
{{Lista de alertas se houver}}

### Distribuição por Épico

| Épico | Itens | % |
|-------|-------|---|
| {{Épico}} | {{N}} | {{%}} |

{{#se houver itens sem épico}}
**Detalhamento - Sem épico:**
- Bugs: {{N}} ({{%}})
- Incidentes: {{N}} ({{%}})
- Tarefas: {{N}} ({{%}})
{{/se houver itens sem épico}}

## Principais Conquistas

{{A preencher manualmente}}

## Principais Desafios

{{A preencher manualmente}}

## Ações Definidas

{{A preencher manualmente}}
