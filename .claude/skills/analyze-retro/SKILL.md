---
name: analyze-retro
description: Analisa retrospectiva e gera report.md. Requer PNGs já gerados.
allowed-tools: Read, Write, Glob
---

# Analisar Retrospectiva

## Responsabilidade

Analisa CSVs e gera report.md usando Template.md como base.

## Pré-requisitos

✅ PNGs já gerados (cfd.png, throughput.png, leadtime.png, tickets.png)
✅ CSVs presentes (cfd.csv, throughput.csv, leadtime.csv, tickets.csv)

Para gerar PNGs: `python3 generate_metrics_charts.py [caminho]`

## Workflow

### 1. Validar Arquivos
Verificar CSVs e PNGs. Se PNGs faltarem: **FINALIZAR**.

### 2. Buscar Ciclo Anterior (se existir)
- Usar Glob para listar diretórios de retrospectivas do mesmo time
- Ordenar por data e identificar o ciclo imediatamente anterior
- Se existir, ler `leadtime.csv` e `throughput.csv` do ciclo anterior para comparação
- Se não existir ciclo anterior, **pular comparações**

### 3. Calcular Métricas

**CFD:** WIP médio, período
**Throughput:**
- Média e desvio padrão
- CV (Coeficiente de Variação) = (desvio padrão / média) × 100%
- Previsibilidade: Alta (<25%), Média (25-50%), Baixa (>50%)
- Capacidade (intervalo de confiança 85%): [média - 1.44×DP, média + 1.44×DP]
- Tendência: calcular usando regressão linear simples nos valores semanais
  - Crescente: coeficiente angular > 0.5
  - Decrescente: coeficiente angular < -0.5
  - Estável: coeficiente angular entre -0.5 e 0.5

**Lead Time:** p50, p90, desvio padrão, categorias (≤5d, 6-10d, >10d)
**Tickets:**
- % por tipo, alertas se bugs >15% ou incidentes >10%
- Agrupamento por épico: usar campo "Parent summary" do CSV
  - Contar itens por épico
  - Calcular % de cada épico em relação ao total
  - Ordenar por quantidade (decrescente)
  - Para itens sem épico (Parent summary vazio): detalhar por tipo (Bugs, Incidentes, Tarefas)

### 4. Comparar com Ciclo Anterior (se existir)

Se o ciclo anterior foi encontrado no passo 2:

**Throughput:**
- Variação da média: ((atual - anterior) / anterior) × 100%
- Tendência: 📈 melhora (>5%), 📉 piora (<-5%), ➡️ estável (±5%)

**Lead Time:**
- Variação p50, p90 e desvio padrão: ((atual - anterior) / anterior) × 100%
- Tendência: 📈 melhora (redução >10%), 📉 piora (aumento >10%), ➡️ estável (±10%)

### 5. Gerar report.md

Usar Template.md como base:
- Identificação, Resumo Executivo
- Análises com PNGs: `![CFD](./cfd.png)`
- Se houver ciclo anterior, incluir tabelas de comparação em Throughput e Lead Time
- Seções qualitativas: `[A preencher manualmente]`

### 6. Insights

Incluir alertas e recomendações baseadas em:
- Bugs/incidentes altos
- Baixa previsibilidade
- Outliers de lead time
- Tendências negativas vs ciclo anterior (se houver)

### 7. Salvar

Salvar `report.md` no diretório da retrospectiva.

## Formato CSVs

- **CFD:** `Date,TESTING,READY TO TEST,CODE REVIEW,IN PROGRESS`
- **Throughput:** `Period,Throughput`
- **Lead Time:** `Leadtime,item count`
- **Tickets:** `Tipo de item,...`

## Limitações

❌ Não gera PNGs
❌ Não preenche seções qualitativas
