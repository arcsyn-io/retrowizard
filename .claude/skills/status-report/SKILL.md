---
name: status-report
description: Gera status report semanal para stakeholders e liderança de engenharia
allowed-tools: Read, Write, Glob, Bash, AskUserQuestion
---

# Status Report Semanal

## Responsabilidade

Gera status report semanal do squad para stakeholders e liderança de engenharia.

## Uso

```
/status-report [time]
```

**Exemplo:** `/status-report financeiro`

## Workflow

### 1. Identificar Semana e Diretório

- Calcular semana atual (ISO week) e ano
- Criar diretório: `[time]/status-report-semanal/` (se não existir)
- Arquivo de saída: `status_report-{ANO}_W{SEMANA}.md`

### 2. Buscar Dados do Jira

Executar extração de dados dos últimos 7 dias (semana anterior):

```bash
python3 jira_extracter.py --days 7 --output-dir /tmp/status-report-data
```

Isso gera:
- `tickets.csv` - Tickets concluídos na semana anterior (DONE)
- `cfd.csv` - Estado do board (para itens em andamento)
- `throughput.csv` - Vazão por semana

### 3. Processar Tickets

**Semana anterior (entregas):**
- Do `tickets.csv`, extrair tickets concluídos (status DONE)
- Agrupar por épico (campo "Parent summary") para identificar frentes de trabalho

**Semana atual (em andamento):**
- Do `cfd.csv`, extrair estado atual do board (última linha)
- Itens em IN PROGRESS, CODE REVIEW, TESTING = em andamento
- Itens em READY TO DEV = backlog da semana

### 4. Calcular Indicadores

Do Jira, calcular:
- Tickets concluídos (DONE)
- Tickets em andamento (IN PROGRESS, CODE REVIEW, TESTING)
- Tickets bloqueados (se houver label ou status específico)
- Bugs e incidentes por tipo

### 5. Gerar Resumos Automáticos (pré-preenchidos)

**IMPORTANTE:** Antes de perguntar ao usuário, gerar resumos baseados nos dados do Jira:

#### 5.1 Resumo da Semana Anterior (sugestão automática)
Analisar tickets concluídos na semana anterior e gerar:
- Principais épicos/frentes trabalhadas (baseado no agrupamento por Parent summary)
- Quantidade de entregas por tipo (features, bugs, tasks)
- Destaques: tickets com maior relevância (épicos com mais entregas)

Formato da sugestão:
```
Com base no Jira, na semana anterior (W{N-1}) foram concluídos {X} tickets:
- {Épico 1}: {N} itens
- {Épico 2}: {N} itens
- Bugs corrigidos: {N}
- Outros: {N}
```

#### 5.2 Foco da Semana Atual (sugestão automática)
Analisar tickets em andamento e gerar:
- Épicos/frentes com trabalho em progresso
- Tickets em CODE REVIEW ou TESTING (próximos de conclusão)

Formato da sugestão:
```
Com base no Jira, o foco desta semana (W{N}) parece ser:
- {Épico 1}: {N} itens em andamento
- {Épico 2}: {N} itens em andamento
- Próximos de conclusão: {N} itens em review/testing
```

### 6. Coletar Informações Qualitativas

**OBRIGATÓRIO:** Apresentar os resumos automáticos e perguntar ao usuário para validar/complementar:

**Pergunta 1 - Contexto da semana anterior:**
Mostrar o resumo automático gerado e perguntar:
"Este é o resumo da semana anterior baseado no Jira. Algo a adicionar ou corrigir? (impedimentos, mudanças de escopo, eventos relevantes como incidentes ou alinhamentos)"

**Pergunta 2 - Foco desta semana:**
Mostrar o resumo automático gerado e perguntar:
"Este é o foco identificado para esta semana. Algo a adicionar ou corrigir? (outras prioridades, dependências externas, decisões técnicas pendentes)"

**Pergunta 3 - Pedidos/Necessidades:**
"Quais os pedidos ou necessidades para outras áreas? (solicitações para produto, upstream, parceiros, etc.)"

### 7. Gerar Status Report

Usar `Template.md` como base e preencher:
- Semana/Ano automaticamente
- Indicadores do Jira
- Entregas concluídas com links
- Em andamento com links
- Informações qualitativas coletadas (resumos automáticos + complementos do usuário)

### 8. Salvar

Salvar em `[time]/status-report-semanal/status_report-{ANO}_W{SEMANA}.md`

## Formato de Links Jira

Para cada ticket, usar formato (usar JIRA_SITE do .env):
```
[FFC-123](https://{JIRA_SITE}/browse/FFC-123)
```

## Limitações

- Não identifica automaticamente tickets bloqueados (requer input manual)
- Seções qualitativas dependem de input do usuário
- Bugs e incidentes precisam ser contados manualmente do período
