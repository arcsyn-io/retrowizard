# 🔮 Retro Wizard - Assistente de Retrospectivas

Programa interativo em Python para gerenciar o fluxo completo de criação, extração e análise de retrospectivas.

## 🚀 Uso Rápido

```bash
# Executar o wizard
./retro-wizard.py

# Ou
python3 retro-wizard.py
```

## 📋 Funcionalidades

O wizard oferece 5 modos de operação:

### 1. 🚀 Fluxo Completo
Executa todas as etapas em sequência:
1. Cria estrutura de diretórios
2. Extrai dados do Jira (CFD, Throughput, Lead Time, Tickets)
3. Gera gráficos PNG
4. Invoca GitHub Copilot para análise e geração do report.md

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

### 5. 🤖 Apenas Analisar com Copilot
Invoca GitHub Copilot CLI para análise dos dados e geração do `report.md`.

**Ideal para:** Já tem CSVs e PNGs, quer apenas o relatório completo.

**Requer:** GitHub Copilot CLI instalado (`gh copilot`).

## 📦 Pré-requisitos

### Python 3
O wizard roda com Python 3 padrão. As dependências dos scripts (pandas, matplotlib) são gerenciadas automaticamente pelos scripts individuais.

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

### GitHub Copilot CLI (opcional, para análise)
Instale a extensão do Copilot CLI:

```bash
gh extension install github/gh-copilot
```

**Nota:** Se não tiver o Copilot CLI instalado, você pode pular a etapa de análise ou invocar o copilot manualmente.

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
#    - Invocação do Copilot para análise

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

## 🔧 Opções Avançadas

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

## 🎨 Interface

O wizard usa cores ANSI para melhor legibilidade:
- 🟢 Verde: Sucesso
- 🔴 Vermelho: Erro
- 🟡 Amarelo: Avisos
- 🔵 Azul: Informações

## 🐛 Troubleshooting

### Erro: "GitHub Copilot CLI não está instalado"
**Solução:** Instale a extensão:
```bash
gh extension install github/gh-copilot
```

Ou escolha opção diferente de "Analisar com Copilot".

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
| Analisar | `gh copilot` | Análise e geração do report.md |

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

### Cenário 4: Análise após ajustes manuais
```bash
./retro-wizard.py
# Escolher opção 5 (Analisar com Copilot)
# Copilot regenera report.md com novos insights
```

## ⚙️ Automação

O wizard pode ser usado em scripts automatizados:

```bash
# Criar estrutura para várias retrospectivas
echo -e "2\nfinanceiro\n16/01/2026\n2026-Q1\ns\nn" | ./retro-wizard.py
```

Embora seja mais recomendado usar o modo interativo para evitar erros.
