---
name: analyze-retrocards
description: Analisa retrocards.csv e actions.csv e complementa o report.md com análise qualitativa
allowed-tools: Read, Edit, Glob
---

# Analisar Retrocards

## Responsabilidade

Lê `retrocards.csv` e `actions.csv` de um diretório de retrospectiva e complementa o `report.md` existente com análise qualitativa, conquistas, desafios e ações definidas.

## Uso

```
/analyze-retrocards [time]/[YYYY-QN]/[YYYY-MM-DD]/
```

**Exemplo:** `/analyze-retrocards financeiro/2026-Q1/2026-01-30/`

## Pré-requisitos

✅ `report.md` já gerado (via `/analyze-retro`)
✅ `retrocards.csv` presente no diretório
⚪ `actions.csv` presente no diretório (opcional)

## Workflow

### 1. Validar Arquivos

Verificar que `report.md` e `retrocards.csv` existem no diretório informado.
Se `report.md` ou `retrocards.csv` não existirem: **FINALIZAR com erro**.

### 2. Ler e Parsear retrocards.csv

Formato CSV (com header de 2 linhas — a primeira é um título, a segunda são os nomes das colunas):

```
# Retrospectiva ... ideas

            Topic,Group,Ideas,Votes,Actions,Comments
Começar,Grupo,"ideia1, ideia2",N,"ação1, ação2","comentário"
```

- **Topic:** Começar / Continuar / Parar
- **Group:** Nome da categoria (pode estar vazio)
- **Ideas:** Ideias separadas por vírgula (conter " - Anonymous" em cada uma, que deve ser removido)
- **Votes:** Número de votos
- **Actions:** Ações definidas (separadas por vírgula)
- **Comments:** Comentários

Ao parsear:
- Remover sufixo " - Anonymous" das ideias
- Separar ideias por vírgula, unindo-as com "; " para exibição na tabela
- Agrupar por Topic, depois ordenar por Votes (decrescente) dentro de cada grupo

### 3. Ler e Parsear actions.csv (se existir)

Formato CSV (com header de 2 linhas):

```
# TEAM Actions • período

            Team,Team Tags,Action,Assigned To,Priority,Created,Due,Completed,Comments,Inspired By,Meeting,Meeting Date
```

Campos relevantes:
- **Action:** Descrição da ação
- **Assigned To:** Responsável
- **Created:** Data de criação (YYYY-MM-DD)
- **Completed:** Data de conclusão (vazio se pendente)
- **Inspired By:** Origem (ex: "Começar • Validação e Testes")
- **Meeting Date:** Data da reunião que gerou a ação

Classificar ações:
- **Novas (desta retro):** Meeting Date igual à data mais recente no arquivo
- **Pendentes (retros anteriores):** Meeting Date anterior E sem data de Completed

### 4. Ler report.md para Contexto Quantitativo

Ler o `report.md` existente e extrair insights das métricas para cruzamento:
- Taxa de bugs e incidentes (do Resumo Executivo)
- Tendência do throughput
- Lead time (p50, p90, variações)
- Alertas existentes
- Pontos positivos e de atenção da seção "Insights e Recomendações"

### 5. Gerar Seção "Retrospectiva Qualitativa"

Para cada Topic (Começar, Continuar, Parar), gerar:

```markdown
## Retrospectiva Qualitativa

### Começar (N tópicos — N votos)

| Grupo | Ideias | Votos |
|-------|--------|-------|
| **Nome do Grupo** | ideia1; ideia2; ideia3 | **N** |

> **Destaque:** Análise cruzada com métricas do report.md
```

Regras:
- Título do Topic com total de tópicos e total de votos
- Tabela ordenada por votos (decrescente)
- Se Group vazio, usar "*(sem grupo)*" em itálico
- Destaque analítico: cruzar o tema mais votado com dados quantitativos do report.md
  - Ex: "Validação e Testes" (5 votos) + taxa de bugs 22.2% = conexão direta

### 6. Gerar Seção "Principais Conquistas"

Cruzar retrocards do tipo "Continuar" (o que o time quer manter) com métricas positivas do report:

```markdown
## Principais Conquistas

1. **Título**: descrição cruzando retrocards com métricas
```

Fontes:
- Retrocards "Continuar" com mais votos
- Pontos positivos de "Insights e Recomendações"
- Métricas com tendência positiva (throughput crescente, lead time melhorando)

### 7. Gerar Seção "Principais Desafios"

Cruzar retrocards dos tipos "Começar" e "Parar" com alertas e pontos de atenção:

```markdown
## Principais Desafios

1. **Título**: descrição cruzando retrocards com métricas
```

Fontes:
- Retrocards "Começar" e "Parar" com mais votos
- Alertas de "Insights e Recomendações" (bugs altos, itens sem épico, etc.)
- Métricas com tendência negativa

### 8. Gerar Seção "Ações Definidas"

```markdown
## Ações Definidas

### Novas (desta retro — DD/MM/AAAA)

| # | Ação | Origem |
|---|------|--------|
| 1 | Descrição da ação | Topic · Grupo |

### Pendentes (retros anteriores)

| # | Ação | Responsável | Criada em | Origem |
|---|------|-------------|-----------|--------|
| 1 | Descrição da ação | Nome | DD/MM/AAAA | Topic · Grupo |
```

Regras:
- Data no título "Novas" = Meeting Date das ações novas (formato DD/MM/AAAA)
- Origem extraída do campo "Inspired By" do CSV
- Se não houver actions.csv, gerar ações a partir do campo "Actions" do retrocards.csv
  - Cada ação listada no campo Actions → uma linha na tabela "Novas"
  - Origem = "Topic · Group" do retrocard que gerou a ação
- Se não houver ações pendentes, omitir a subseção "Pendentes"
- Ações com Completed preenchido devem ser **ignoradas** (já foram concluídas)

### 9. Inserir/Substituir Seções no report.md

Usar a tool Edit para inserir ou substituir as seções no report.md:

**Se as seções já existirem** (contêm "## Retrospectiva Qualitativa", "## Principais Conquistas", etc.):
- Substituir o conteúdo existente

**Se as seções não existirem** (contêm `{{A preencher manualmente}}`):
- Substituir os placeholders

**Posição:** As seções devem ficar após "## Insights e Recomendações" (e suas subseções), nesta ordem:
1. Retrospectiva Qualitativa
2. Principais Conquistas
3. Principais Desafios
4. Ações Definidas

## Limitações

❌ Não gera report.md do zero (use `/analyze-retro` antes)
❌ Não gera gráficos ou métricas quantitativas
