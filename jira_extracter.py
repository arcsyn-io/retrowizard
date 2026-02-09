#!/usr/bin/env python3
"""
Extrai CFD, Throughput, Lead Time e Tickets do Jira usando a mesma API que o Scope360.

Uso:
    python jira_extracter.py [--days N] [--output-dir DIR] [--board BOARD_ID]

Exemplos:
    python jira_extracter.py --days 14 --output-dir .
    python jira_extracter.py --days 30 --board 191 --output-dir financeiro/2026-Q1/2026-01-16

Arquivos gerados:
    - cfd.csv: Cumulative Flow Diagram (snapshots diários)
    - throughput.csv: Itens concluídos por semana
    - leadtime.csv: Distribuição de lead time em dias
    - tickets.csv: Detalhes dos tickets concluídos

Autenticação (via variáveis de ambiente ou arquivo .env):
    - JIRA_EMAIL: Email da conta Atlassian
    - JIRA_API_TOKEN: Token de API (criar em https://id.atlassian.com/manage-profile/security/api-tokens)
    - JIRA_SITE: Site do Jira (ex: seusite.atlassian.net)

Configuração de Boards (opcional):
    - JIRA_BOARD_FINANCEIRO=191
    - JIRA_BOARD_PRODUTO=123
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Erro: módulo 'requests' não encontrado.")
    print("   Instale com: pip install requests")
    sys.exit(1)


def load_env_file():
    """Carrega variáveis do arquivo .env se existir."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Não sobrescreve variáveis já definidas
                    if key not in os.environ:
                        os.environ[key] = value


# Carrega .env antes de tudo
load_env_file()


# =============================================================================
# CONFIGURAÇÃO PADRÃO (pode ser sobrescrita via argumentos ou env vars)
# =============================================================================
DEFAULT_SITE = os.environ.get("JIRA_SITE", "")
DEFAULT_BOARD_ID = int(os.environ.get("JIRA_BOARD_FINANCEIRO", "0"))

# Configuração específica do board FFC (financeiro)
BOARD_CONFIG = {
    191: {
        "swimlane_ids": [252, 253],
        "column_ids": [796, 794, 793, 797, 798, 795],
    }
}

# Ordem das colunas no CSV (igual ao Scope360)
CFD_COLUMNS = ["DONE", "TESTING", "READY TO TEST", "CODE REVIEW", "IN PROGRESS", "READY TO DEV"]


def get_auth():
    """Obtém credenciais das variáveis de ambiente."""
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")

    if not email or not token:
        print("❌ Erro: Credenciais não configuradas.")
        print()
        print("Configure as variáveis de ambiente:")
        print("  export JIRA_EMAIL='seu-email@empresa.com'")
        print("  export JIRA_API_TOKEN='seu-token-aqui'")
        print()
        print("Crie um token em: https://id.atlassian.com/manage-profile/security/api-tokens")
        sys.exit(1)

    return (email, token)


def fetch_cfd_data(site, board_id):
    """
    Busca dados do CFD usando a API nativa do Jira (mesma que o Scope360 usa).

    Endpoint: /rest/greenhopper/1.0/rapid/charts/cumulativeflowdiagram.json
    """
    auth = get_auth()

    jira_base = f"https://{site}"
    url = f"{jira_base}/rest/greenhopper/1.0/rapid/charts/cumulativeflowdiagram.json"

    # Monta parâmetros
    params = [("rapidViewId", board_id)]

    # Usa configuração específica do board se disponível
    if board_id in BOARD_CONFIG:
        config = BOARD_CONFIG[board_id]
        for sid in config.get("swimlane_ids", []):
            params.append(("swimlaneId", sid))
        for cid in config.get("column_ids", []):
            params.append(("columnId", cid))

    print(f"📊 Buscando CFD do board {board_id}...")
    print(f"   Site: {site}")
    print(f"   URL: {url}")

    response = requests.get(url, params=params, auth=auth)

    if response.status_code == 401:
        print("❌ Erro 401: Não autorizado. Verifique suas credenciais.")
        sys.exit(1)
    elif response.status_code == 403:
        print("❌ Erro 403: Acesso negado. Verifique permissões do token.")
        sys.exit(1)
    elif response.status_code != 200:
        print(f"❌ Erro {response.status_code}: {response.text}")
        sys.exit(1)

    return response.json()


def parse_cfd_response(data, days_back=None):
    """
    Parseia a resposta da API do Jira e converte para formato CSV.

    A resposta tem formato:
    {
        "columns": [
            {"name": "READY TO DEV"},
            {"name": "IN PROGRESS"},
            ...
        ],
        "columnChanges": {
            "timestamp_ms": [
                {"key": "FFC-123", "columnTo": 0, "statusTo": "10029"},
                ...
            ],
            ...
        }
    }

    Cada mudança indica que uma issue moveu para uma coluna (columnTo é o índice).
    Precisamos reconstruir o estado do board para cada dia.
    """
    # Extrai nomes das colunas por índice
    columns = data.get("columns", [])
    column_names = [col["name"].upper() for col in columns]

    print(f"\n📋 Colunas encontradas:")
    for i, name in enumerate(column_names):
        print(f"   {i}: {name}")

    # Extrai todas as mudanças e ordena por timestamp
    column_changes = data.get("columnChanges", {})
    all_changes = []

    for timestamp_str, changes_list in column_changes.items():
        timestamp = int(timestamp_str)
        for change in changes_list:
            # columnTo = issue entrou na coluna
            # columnFrom (sem columnTo) = issue saiu do board
            if "columnTo" in change:
                all_changes.append({
                    "timestamp": timestamp,
                    "date": datetime.fromtimestamp(timestamp / 1000).date(),
                    "key": change["key"],
                    "column_idx": change["columnTo"],
                    "action": "enter",
                })
            elif "columnFrom" in change:
                # Issue saiu do board (foi para Backlog, Done externo, etc.)
                all_changes.append({
                    "timestamp": timestamp,
                    "date": datetime.fromtimestamp(timestamp / 1000).date(),
                    "key": change["key"],
                    "column_idx": None,  # Saiu do board
                    "action": "exit",
                })

    # Ordena por timestamp
    all_changes.sort(key=lambda x: x["timestamp"])

    if not all_changes:
        print("⚠️ Nenhuma mudança encontrada.")
        return []

    # Encontra o range de datas
    first_date = all_changes[0]["date"]
    last_date = all_changes[-1]["date"]

    # Filtra por período se especificado
    if days_back:
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        first_date = max(first_date, cutoff_date)

    print(f"\n📅 Período: {first_date} a {last_date}")

    # Reconstrói o estado do board para cada dia
    # issue_state[key] = column_idx (ou None se removida)
    issue_state = {}

    # Agrupa mudanças por data
    changes_by_date = {}
    for change in all_changes:
        d = change["date"]
        if d not in changes_by_date:
            changes_by_date[d] = []
        changes_by_date[d].append(change)

    # Gera dados do CFD para cada dia no range
    cfd_data = []
    current_date = first_date

    # Primeiro, aplica todas as mudanças antes do período
    for change in all_changes:
        if change["date"] < first_date:
            issue_state[change["key"]] = change["column_idx"]
        else:
            break

    while current_date <= last_date:
        # Aplica mudanças do dia
        if current_date in changes_by_date:
            for change in changes_by_date[current_date]:
                issue_state[change["key"]] = change["column_idx"]

        # Conta issues em cada coluna
        counts = [0] * len(column_names)
        for key, col_idx in issue_state.items():
            if col_idx is not None and 0 <= col_idx < len(counts):
                counts[col_idx] += 1

        # Monta row com nomes de colunas
        row = {"Date": current_date.strftime("%Y-%m-%d")}
        for i, name in enumerate(column_names):
            # Mapeia para o nome padrão no CFD_COLUMNS
            if name in CFD_COLUMNS:
                row[name] = counts[i]

        # Garante todas as colunas
        for col in CFD_COLUMNS:
            if col not in row:
                row[col] = 0

        cfd_data.append(row)
        current_date += timedelta(days=1)

    print(f"\n📊 {len(cfd_data)} dias de dados processados")
    return cfd_data


def calculate_throughput_and_leadtime(data, days_back=None, throughput_weeks=4):
    """
    Calcula throughput semanal e lead time a partir dos dados da API do CFD.

    O throughput é calculado contando issues que entram na coluna DONE por semana.
    O lead time é calculado como dias entre primeira entrada em IN PROGRESS e entrada em DONE.

    Args:
        data: Dados da API do Jira
        days_back: Período para filtrar lead time (padrão: None = todos)
        throughput_weeks: Número de semanas para throughput (padrão: 4)

    Retorna:
        throughput_data: Lista de dicts com {"period": "YYYY-MM-DD", "throughput": N}
        leadtime_data: Lista de dicts com {"leadtime": N, "count": M}
    """
    columns = data.get("columns", [])
    column_names = [col["name"].upper() for col in columns]

    # Encontra índices das colunas relevantes
    done_idx = None
    in_progress_idx = None

    for i, name in enumerate(column_names):
        if name == "DONE":
            done_idx = i
        elif name == "IN PROGRESS":
            in_progress_idx = i

    if done_idx is None:
        print("⚠️  Coluna DONE não encontrada. Não é possível calcular throughput/leadtime.")
        return [], []

    if in_progress_idx is None:
        print("⚠️  Coluna IN PROGRESS não encontrada. Usando primeira coluna para lead time.")
        in_progress_idx = 0

    print(f"\n📊 Calculando throughput e lead time...")
    print(f"   DONE index: {done_idx}")
    print(f"   IN PROGRESS index: {in_progress_idx}")

    # Extrai todas as mudanças
    column_changes = data.get("columnChanges", {})
    all_changes = []

    for timestamp_str, changes_list in column_changes.items():
        timestamp = int(timestamp_str)
        dt = datetime.fromtimestamp(timestamp / 1000)
        for change in changes_list:
            if "columnTo" in change:
                all_changes.append({
                    "timestamp": timestamp,
                    "datetime": dt,
                    "date": dt.date(),
                    "key": change["key"],
                    "column_idx": change["columnTo"],
                })

    # Ordena por timestamp
    all_changes.sort(key=lambda x: x["timestamp"])

    if not all_changes:
        return [], []

    # Filtra por período se especificado
    cutoff_date = None
    if days_back:
        cutoff_date = datetime.now().date() - timedelta(days=days_back)

    # Rastreia histórico de cada issue
    # issue_history[key] = {"first_in_progress": datetime, "done": datetime}
    issue_history = {}

    for change in all_changes:
        key = change["key"]
        col_idx = change["column_idx"]
        dt = change["datetime"]

        if key not in issue_history:
            issue_history[key] = {"first_in_progress": None, "done": None}

        # Primeira entrada em IN PROGRESS (ou coluna posterior que indica início do trabalho)
        if col_idx >= in_progress_idx and col_idx < done_idx:
            if issue_history[key]["first_in_progress"] is None:
                issue_history[key]["first_in_progress"] = dt

        # Entrada em DONE (apenas primeira vez)
        if col_idx == done_idx:
            if issue_history[key]["done"] is None:
                issue_history[key]["done"] = dt
                # Se não passou por IN PROGRESS, usa a data de DONE como início
                if issue_history[key]["first_in_progress"] is None:
                    issue_history[key]["first_in_progress"] = dt

    # Calcula cutoff separado para throughput (últimas N semanas)
    throughput_cutoff = datetime.now().date() - timedelta(weeks=throughput_weeks)

    # Calcula throughput por semana (início da semana = segunda-feira)
    done_by_week = defaultdict(int)
    leadtimes = []

    for key, history in issue_history.items():
        if history["done"] is None:
            continue

        done_date = history["done"].date()

        # Throughput: usa cutoff de semanas (sempre últimas 4 semanas)
        if done_date >= throughput_cutoff:
            # Calcula o início da semana (segunda-feira)
            week_start = done_date - timedelta(days=done_date.weekday())
            done_by_week[week_start] += 1

        # Lead time: usa cutoff de dias (se especificado)
        if cutoff_date is None or done_date >= cutoff_date:
            if history["first_in_progress"]:
                start_date = history["first_in_progress"].date()
                lead_time_days = (done_date - start_date).days + 1  # +1 para incluir o dia de início
                if lead_time_days > 0:
                    leadtimes.append(lead_time_days)

    # Formata throughput (últimas N semanas completas)
    throughput_data = []
    for week_start in sorted(done_by_week.keys()):
        throughput_data.append({
            "period": week_start.strftime("%Y-%m-%d"),
            "throughput": done_by_week[week_start]
        })

    # Formata lead time (contagem por valor)
    leadtime_counts = defaultdict(int)
    for lt in leadtimes:
        leadtime_counts[lt] += 1

    leadtime_data = []
    for lt in sorted(leadtime_counts.keys()):
        leadtime_data.append({
            "leadtime": lt,
            "count": leadtime_counts[lt]
        })

    print(f"   {len(throughput_data)} semanas de throughput")
    print(f"   {len(leadtimes)} issues com lead time calculado")
    if leadtimes:
        print(f"   Lead time: min={min(leadtimes)}d, max={max(leadtimes)}d, mediana={sorted(leadtimes)[len(leadtimes)//2]}d")

    return throughput_data, leadtime_data


def fetch_tickets_details(site, issue_keys):
    """
    Busca detalhes dos tickets via API REST do Jira.

    Retorna lista de dicts com informações de cada ticket.
    """
    if not issue_keys:
        return []

    auth = get_auth()
    jira_base = f"https://{site}"

    print(f"\n🎫 Buscando detalhes de {len(issue_keys)} tickets...")

    tickets = []

    # Busca cada issue individualmente (API search retorna 410)
    for i, key in enumerate(issue_keys):
        url = f"{jira_base}/rest/api/2/issue/{key}"
        params = {
            "fields": "issuetype,summary,parent,status,resolution,updated"
        }

        response = requests.get(url, params=params, auth=auth)

        if response.status_code != 200:
            print(f"⚠️  Erro ao buscar {key}: {response.status_code}")
            continue

        issue = response.json()
        fields = issue.get("fields", {})
        parent = fields.get("parent", {})

        # Formata data de atualização
        updated = fields.get("updated", "")
        if updated:
            # Converte ISO para formato DD/MMM/YY HH:MM AM/PM
            try:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                # Meses em português abreviado
                months_pt = ["jan", "fev", "mar", "abr", "mai", "jun",
                             "jul", "ago", "set", "out", "nov", "dez"]
                month_pt = months_pt[dt.month - 1]
                hour = dt.hour
                ampm = "AM" if hour < 12 else "PM"
                if hour > 12:
                    hour -= 12
                elif hour == 0:
                    hour = 12
                updated = f"{dt.day:02d}/{month_pt}/{dt.year % 100} {hour}:{dt.minute:02d} {ampm}"
            except:
                pass

        ticket = {
            "tipo": fields.get("issuetype", {}).get("name", ""),
            "chave": issue.get("key", ""),
            "id": issue.get("id", ""),
            "resumo": fields.get("summary", ""),
            "pai_id": parent.get("id", "") if parent else "",
            "pai_chave": parent.get("key", "") if parent else "",
            "pai_resumo": parent.get("fields", {}).get("summary", "") if parent and parent.get("fields") else "",
            "status": fields.get("status", {}).get("name", ""),
            "resolucao": fields.get("resolution", {}).get("name", "") if fields.get("resolution") else "",
            "atualizado": updated
        }
        tickets.append(ticket)

        # Mostra progresso a cada 10 tickets
        if (i + 1) % 10 == 0:
            print(f"   {i + 1}/{len(issue_keys)} tickets processados...")

    print(f"   {len(tickets)} tickets encontrados")
    return tickets


def extract_done_issues(data, days_back=None):
    """
    Extrai lista de issue keys que foram para DONE no período.
    """
    columns = data.get("columns", [])
    column_names = [col["name"].upper() for col in columns]

    done_idx = None
    for i, name in enumerate(column_names):
        if name == "DONE":
            done_idx = i
            break

    if done_idx is None:
        return []

    column_changes = data.get("columnChanges", {})
    done_issues = {}  # key -> primeira data de DONE

    cutoff_date = None
    if days_back:
        cutoff_date = datetime.now().date() - timedelta(days=days_back)

    for timestamp_str, changes_list in column_changes.items():
        timestamp = int(timestamp_str)
        dt = datetime.fromtimestamp(timestamp / 1000)

        for change in changes_list:
            if "columnTo" in change and change["columnTo"] == done_idx:
                key = change["key"]
                if key not in done_issues:
                    if cutoff_date is None or dt.date() >= cutoff_date:
                        done_issues[key] = dt

    return list(done_issues.keys())


def save_tickets_csv(tickets, filename):
    """Salva tickets em CSV no formato de exportação do Jira."""
    with open(filename, 'w', encoding='utf-8') as f:
        # Header
        f.write("Tipo de item,Chave da item,ID da item,Resumo,Pai,Chave pai,Parent summary,Status,Resolução,Atualizado(a)\n")

        for t in tickets:
            # Escapa campos com vírgula ou aspas
            resumo = t["resumo"].replace('"', '""')
            if "," in resumo or '"' in resumo:
                resumo = f'"{resumo}"'

            pai_resumo = t["pai_resumo"].replace('"', '""')
            if "," in pai_resumo or '"' in pai_resumo:
                pai_resumo = f'"{pai_resumo}"'

            f.write(f'{t["tipo"]},{t["chave"]},{t["id"]},{resumo},{t["pai_id"]},{t["pai_chave"]},{pai_resumo},{t["status"]},{t["resolucao"]},{t["atualizado"]}\n')

    print(f"✅ Tickets salvo em: {filename}")


def save_cfd_csv(data, filename):
    """Salva dados do CFD em CSV no formato Scope360."""
    with open(filename, 'w') as f:
        # Header com aspas (igual ao Scope360)
        header = ",".join([f'"{col}"' for col in ["Date"] + CFD_COLUMNS])
        f.write(header + "\n")

        # Data rows com aspas
        for row in data:
            values = [f'"{row["Date"]}"']
            for col in CFD_COLUMNS:
                values.append(f'"{row.get(col, 0)}"')
            f.write(",".join(values) + "\n")

    print(f"✅ CFD salvo em: {filename}")


def save_throughput_csv(data, filename):
    """Salva dados de throughput em CSV."""
    with open(filename, 'w') as f:
        f.write('"Period","Throughput"\n')
        for row in data:
            f.write(f'"{row["period"]}","{row["throughput"]}"\n')

    print(f"✅ Throughput salvo em: {filename}")


def save_leadtime_csv(data, filename):
    """Salva dados de lead time em CSV."""
    with open(filename, 'w') as f:
        f.write('"Leadtime","item count"\n')
        for row in data:
            f.write(f'"{row["leadtime"]}","{row["count"]}"\n')

    print(f"✅ Lead time salvo em: {filename}")


def print_cfd(data):
    """Imprime o CFD formatado."""
    print("\n" + "=" * 90)
    print("CFD Data:")
    print("=" * 90)

    header = f"{'Date':<12}"
    for col in CFD_COLUMNS:
        header += f" {col:>14}"
    print(header)
    print("-" * 90)

    for row in data:
        line = f"{row['Date']:<12}"
        for col in CFD_COLUMNS:
            line += f" {row.get(col, 0):>14}"
        print(line)


def main():
    parser = argparse.ArgumentParser(
        description="Extrai CFD, Throughput e Lead Time do Jira usando a mesma API que o Scope360.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python jira_extracter.py --days 14 --output-dir .
  python jira_extracter.py --days 30 --board 191 --output-dir financeiro/2026-Q1/2026-01-16

Arquivos gerados:
  cfd.csv        - Cumulative Flow Diagram (snapshots diários)
  throughput.csv - Itens concluídos por semana
  leadtime.csv   - Distribuição de lead time em dias

Autenticação (via .env ou variáveis de ambiente):
  JIRA_EMAIL='seu-email@empresa.com'
  JIRA_API_TOKEN='seu-token-aqui'
  JIRA_SITE='seusite.atlassian.net'

Crie um token em: https://id.atlassian.com/manage-profile/security/api-tokens
        """
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Número de dias para extrair (padrão: todos disponíveis)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Diretório de saída (padrão: diretório atual)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="(Legado) Arquivo de saída para CFD apenas. Use --output-dir para gerar todos os arquivos."
    )
    parser.add_argument(
        "--board", "-b",
        type=int,
        default=DEFAULT_BOARD_ID,
        help=f"ID do board no Jira (padrão: {DEFAULT_BOARD_ID})"
    )
    parser.add_argument(
        "--site", "-s",
        default=DEFAULT_SITE,
        help=f"Site do Jira (padrão: {DEFAULT_SITE})"
    )
    parser.add_argument(
        "--throughput-weeks",
        type=int,
        default=4,
        help="Número de semanas para throughput (padrão: 4)"
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Imprime dados no console"
    )
    parser.add_argument(
        "--cfd-only",
        action="store_true",
        help="Gera apenas o CFD (sem throughput e leadtime)"
    )

    args = parser.parse_args()

    if not args.site:
        print("❌ Erro: JIRA_SITE não configurado.")
        print("   Defina no .env ou passe via --site seusite.atlassian.net")
        sys.exit(1)

    # Busca dados da API
    raw_data = fetch_cfd_data(args.site, args.board)

    # Parseia resposta para CFD
    cfd_data = parse_cfd_response(raw_data, args.days)

    if not cfd_data:
        print("❌ Nenhum dado para salvar.")
        sys.exit(1)

    # Imprime se solicitado
    if args.print:
        print_cfd(cfd_data)

    # Determina diretório de saída
    if args.output:
        # Modo legado: apenas CFD
        output_dir = Path(args.output).parent
        cfd_file = args.output
        save_cfd_csv(cfd_data, cfd_file)
        print(f"\n📊 {len(cfd_data)} dias de CFD extraídos com sucesso!")
    else:
        # Modo novo: todos os arquivos
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Salva CFD
        cfd_file = output_dir / "cfd.csv"
        save_cfd_csv(cfd_data, cfd_file)

        if not args.cfd_only:
            # Calcula e salva throughput e leadtime
            # Throughput usa --throughput-weeks (padrão 4 semanas)
            # Lead time usa --days (mesmo período do CFD)
            throughput_data, leadtime_data = calculate_throughput_and_leadtime(
                raw_data, args.days, args.throughput_weeks
            )

            if throughput_data:
                throughput_file = output_dir / "throughput.csv"
                save_throughput_csv(throughput_data, throughput_file)

            if leadtime_data:
                leadtime_file = output_dir / "leadtime.csv"
                save_leadtime_csv(leadtime_data, leadtime_file)

            # Extrai e salva tickets
            done_keys = extract_done_issues(raw_data, args.days)
            if done_keys:
                tickets = fetch_tickets_details(args.site, done_keys)
                if tickets:
                    tickets_file = output_dir / "tickets.csv"
                    save_tickets_csv(tickets, tickets_file)

        print(f"\n📊 Extração concluída com sucesso!")
        print(f"   📁 Diretório: {output_dir}")
        print(f"   📅 CFD: {len(cfd_data)} dias")
        if not args.cfd_only and throughput_data:
            print(f"   📈 Throughput: {len(throughput_data)} semanas")
        if not args.cfd_only and leadtime_data:
            total_items = sum(row["count"] for row in leadtime_data)
            print(f"   ⏱️  Lead time: {total_items} itens")
        if not args.cfd_only and done_keys:
            print(f"   🎫 Tickets: {len(done_keys)} itens")


if __name__ == "__main__":
    main()
