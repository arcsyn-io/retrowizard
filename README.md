# 🔮 Retro Wizard - Assistente de Retrospectivas

Repositório para gerenciamento de retrospectivas de sprint. Programa interativo em Python para gerenciar o fluxo completo de criação, extração e análise de retrospectivas.

## 🚀 Uso Rápido

```bash
# Executar o wizard
./retro-wizard.py

# Ou
python3 retro-wizard.py
```

## 📋 Funcionalidades

O wizard oferece 4 modos de operação:

### 1. 🚀 Fluxo Completo
Executa todas as etapas em sequência:
1. Cria estrutura de diretórios
2. Extrai dados do Jira (CFD, Throughput, Lead Time, Tickets)
3. Gera gráficos PNG

**Ideal para:** Nova retrospectiva do zero.

### 2. 📁 Apenas Criar Estrutura
Cria apenas a estrutura de diretórios:
```
[team]/[quarter]/[date]/
```

**Ideal para:** Preparar diretório para adicionar CSVs manualmente.

### 3. 📊 Apenas Extrair Dados do Jira
Extrai dados do Jira e salva 4 CSVs:
- `cfd.csv` - Cumulative Flow Diagram
- `throughput.csv` - Throughput semanal
- `leadtime.csv` - Distribuição de lead time
- `tickets.csv` - Detalhes dos tickets concluídos

**Ideal para:** Já tem estrutura criada e quer popular com dados do Jira.

**Requer:** Arquivo `.env` configurado (veja pré-requisitos abaixo).

### 4. 📈 Apenas Gerar Gráficos
Gera 4 gráficos PNG a partir dos CSVs existentes:
- `cfd.png`
- `throughput.png`
- `leadtime.png`
- `tickets.png`

**Ideal para:** Já tem CSVs e quer apenas visualizações.

## 📦 Pré-requisitos

### Python 3
O wizard roda com Python 3 padrão. As dependências dos scripts (pandas, matplotlib) são gerenciadas automaticamente pelos scripts individuais.

Para operações manuais:

```bash
source .venv/bin/activate
pip install pandas matplotlib requests
```

### Arquivo `.env` (para extração do Jira)
Crie um arquivo `.env` na raiz do projeto:

```bash
JIRA_EMAIL=seu-email@empresa.com
JIRA_API_TOKEN=seu-token-aqui
JIRA_SITE=seusite.atlassian.net

# Board IDs por time
JIRA_BOARD_FINANCEIRO=191
JIRA_BOARD_PRODUTO=123
# Adicione mais times conforme necessário
```

**Criar token:** https://id.atlassian.com/manage-profile/security/api-tokens

**⚡ Carregamento Automático**: O wizard carrega automaticamente as variáveis do `.env` para `os.environ` no início da execução e as passa para todos os subprocessos (scripts Python, comandos shell, etc.). Não é necessário usar `source .env` manualmente.

## 📂 Estrutura do Repositório

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

## 🎯 Fluxo de Uso Típico

### Exemplo: Nova Retrospectiva do Time Financeiro

```bash
# 1. Executar o wizard
./retro-wizard.py

# 2. Escolher opção 1 (Fluxo Completo)
Opção [1]: 1

# 3. Informar dados
Nome do time: financeiro
Data da retrospectiva: 16/01/2026
Quarter: 2026-Q1

# 4. Confirmar
Confirma as informações? (s/n) [s]: s

# 5. Aguardar execução automática de:
#    - Criação da estrutura
#    - Extração do Jira (14 dias de dados)
#    - Geração de 4 gráficos PNG

# 6. Resultado: financeiro/2026-Q1/2026-01-16/
#    ├── cfd.csv
#    ├── cfd.png
#    ├── throughput.csv
#    ├── throughput.png
#    ├── leadtime.csv
#    ├── leadtime.png
#    ├── tickets.csv
#    ├── tickets.png
#    └── report.md
```

## 🔧 Comandos Manuais

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

### Personalizar Período de Extração
Durante a etapa de extração do Jira, o wizard pergunta:
```
Número de dias para extrair [14]: 30
```

Você pode informar qualquer número de dias.

### Múltiplas Operações
Após completar uma operação, o wizard pergunta se deseja fazer outra:
```
Deseja realizar outra operação? (s/n) [n]:
```

Útil para processar várias retrospectivas em sequência.

## 📊 Formatos de Dados

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

## 📚 Estrutura da Retrospectiva

### Report (`report.md`)

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

## 📚 Estrutura de Saída

```
[time]/[quarter]/[date]/
├── cfd.csv              # Cumulative Flow Diagram (dados)
├── cfd.png              # CFD (visualização)
├── throughput.csv       # Throughput semanal (dados)
├── throughput.png       # Throughput (visualização)
├── leadtime.csv         # Lead time (dados)
├── leadtime.png         # Lead time (visualização)
├── tickets.csv          # Tickets do Jira (dados)
├── tickets.png          # Distribuição de tipos (visualização)
├── retrocards.md        # Feedback do time (manual)
└── report.md            # Relatório completo (gerado)
```

## 🔗 Integração com Scripts

O wizard invoca os seguintes scripts e comandos:

| Etapa | Script/Comando | Função |
|-------|----------------|--------|
| Criar estrutura | `mkdir -p` | Cria diretórios [time]/[quarter]/[data] |
| Extrair dados | `jira_extracter.py` | Extrai dados do Jira (CSVs) |
| Gerar gráficos | `generate_metrics_charts.py` | Gera gráficos PNG |
| Analisar | `claude` | Análise e geração do report.md |

## 🎨 Interface

O wizard usa cores ANSI para melhor legibilidade:
- 🟢 Verde: Sucesso
- 🔴 Vermelho: Erro
- 🟡 Amarelo: Avisos
- 🔵 Azul: Informações

## 🐛 Troubleshooting

### Erro: "Arquivo .env não encontrado"
**Solução:** Crie o arquivo `.env` na raiz do projeto com as credenciais do Jira.

### Erro: "Board ID não configurado"
**Solução:** Adicione a variável `JIRA_BOARD_[TIME]` no `.env`:
```bash
JIRA_BOARD_PRODUTO=123
```

### Gráficos não são gerados
**Solução:** Verifique se os CSVs estão no formato correto:
- `cfd.csv`: Date, TESTING, READY TO TEST, CODE REVIEW, IN PROGRESS
- `throughput.csv`: Period, Throughput
- `leadtime.csv`: Leadtime, item count
- `tickets.csv`: Tipo de item

## 🤝 Contribuindo

Para adicionar um novo time:

1. Adicione board ID no `.env`:
   ```bash
   JIRA_BOARD_NOVOTOME=456
   ```

2. Execute o wizard normalmente, informando o nome do novo time.

## 📝 Notas

- O wizard **não** preenche seções qualitativas do report.md (Conquistas, Desafios, Ações). Essas devem ser preenchidas manualmente ou a partir de `retrocards.md`.
- O wizard permite cancelar operações com `Ctrl+C` a qualquer momento.
- Cada operação pode ser executada individualmente, permitindo flexibilidade no fluxo de trabalho.

## 🎓 Exemplos de Uso

### Cenário 1: Retrospectiva completa automatizada
```bash
./retro-wizard.py
# Escolher opção 1
# Informar: financeiro, 16/01/2026, 2026-Q1
# Deixar o wizard executar tudo automaticamente
```

### Cenário 2: Apenas extrair dados novos
```bash
./retro-wizard.py
# Escolher opção 3 (Extrair Dados)
# Informar time/quarter/data
# CSVs são atualizados
```

### Cenário 3: Regenerar apenas gráficos após editar CSVs
```bash
./retro-wizard.py
# Escolher opção 4 (Gerar Gráficos)
# Informar time/quarter/data
# PNGs são regerados
```

## ⚙️ Automação

O wizard pode ser usado em scripts automatizados:

```bash
# Criar estrutura para várias retrospectivas
echo -e "2\nfinanceiro\n16/01/2026\n2026-Q1\ns\nn" | ./retro-wizard.py
```

Embora seja mais recomendado usar o modo interativo para evitar erros.
