#!/usr/bin/env python3
"""
Retro Wizard - Assistente Interativo para Retrospectivas
Gerencia o fluxo completo de criação, extração e análise de retrospectivas.
"""

import os
import sys
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path


class Colors:
    """Cores ANSI para terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Imprime cabeçalho colorido"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Imprime aviso"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Imprime informação"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def get_input(prompt, default=None):
    """Obtém entrada do usuário com valor padrão opcional"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(f"{Colors.BOLD}{prompt}{Colors.ENDC}").strip()
    return value if value else default


def validate_date(date_str):
    """Valida e converte data para formato YYYY-MM-DD"""
    try:
        # Tenta formato DD/MM/YYYY
        if '/' in date_str:
            day, month, year = date_str.split('/')
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        # Assume formato YYYY-MM-DD
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        return None


def validate_quarter(quarter_str):
    """Valida e converte quarter para formato YYYY-QN"""
    quarter_str = quarter_str.strip().upper()

    # Se já está no formato correto
    if '-Q' in quarter_str:
        parts = quarter_str.split('-Q')
        if len(parts) == 2 and parts[0].isdigit() and parts[1] in ['1', '2', '3', '4']:
            return quarter_str

    return None


def get_current_quarter():
    """Retorna o quarter atual baseado na data de hoje"""
    today = datetime.now()
    quarter = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{quarter}"


def get_last_retro_date(team, quarter):
    """Retorna a última data de retrospectiva para o time e quarter"""
    path = Path(team) / quarter
    if not path.exists():
        return None

    # Lista diretórios que parecem ser datas (YYYY-MM-DD)
    dates = []
    for item in path.iterdir():
        if item.is_dir():
            try:
                datetime.strptime(item.name, '%Y-%m-%d')
                dates.append(item.name)
            except ValueError:
                continue

    if dates:
        dates.sort()
        return dates[-1]
    return None


def get_existing_teams():
    """Retorna lista de times existentes (diretórios na raiz)"""
    teams = []
    for item in Path('.').iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Verifica se parece ser um time (tem subdiretórios de quarter)
            for sub in item.iterdir():
                if sub.is_dir() and '-Q' in sub.name:
                    teams.append(item.name)
                    break
    return sorted(teams)


def list_all_retrospectives():
    """Lista todas as retrospectivas existentes"""
    retros = []

    for team_dir in Path('.').iterdir():
        if not team_dir.is_dir() or team_dir.name.startswith('.'):
            continue

        for quarter_dir in team_dir.iterdir():
            if not quarter_dir.is_dir() or '-Q' not in quarter_dir.name:
                continue

            for date_dir in quarter_dir.iterdir():
                if not date_dir.is_dir():
                    continue

                # Verifica se parece ser uma data válida
                try:
                    datetime.strptime(date_dir.name, '%Y-%m-%d')
                except ValueError:
                    continue

                # Verifica se tem report.md
                report_path = date_dir / 'report.md'
                has_report = report_path.exists()

                # Verifica quais arquivos existem
                files = {
                    'cfd': (date_dir / 'cfd.png').exists(),
                    'throughput': (date_dir / 'throughput.png').exists(),
                    'leadtime': (date_dir / 'leadtime.png').exists(),
                    'tickets': (date_dir / 'tickets.png').exists(),
                    'retrocards': (date_dir / 'retrocards.csv').exists() or (date_dir / 'retrocards.md').exists(),
                }

                retros.append({
                    'team': team_dir.name,
                    'quarter': quarter_dir.name,
                    'date': date_dir.name,
                    'path': str(date_dir),
                    'has_report': has_report,
                    'files': files,
                })

    # Ordena por time, quarter e data
    retros.sort(key=lambda x: (x['team'], x['quarter'], x['date']))
    return retros


def show_retrospectives_list():
    """Exibe lista de todas as retrospectivas com seleção interativa"""
    print_header("📋 Lista de Retrospectivas")

    retros = list_all_retrospectives()

    if not retros:
        print_warning("Nenhuma retrospectiva encontrada.")
        return

    # Exibe lista numerada
    print(f"{Colors.BOLD}Selecione uma retrospectiva para abrir:{Colors.ENDC}\n")

    current_team = None
    current_quarter = None
    index = 1

    for retro in retros:
        # Cabeçalho do time
        if retro['team'] != current_team:
            current_team = retro['team']
            current_quarter = None
            print(f"\n{Colors.BOLD}{Colors.HEADER}📁 {current_team.upper()}{Colors.ENDC}")

        # Cabeçalho do quarter
        if retro['quarter'] != current_quarter:
            current_quarter = retro['quarter']
            print(f"  {Colors.OKCYAN}└── {current_quarter}{Colors.ENDC}")

        # Status do relatório
        if retro['has_report']:
            status = f"{Colors.OKGREEN}✅{Colors.ENDC}"
        else:
            status = f"{Colors.WARNING}⏳{Colors.ENDC}"

        # Status dos arquivos
        files = retro['files']
        file_icons = []
        if files['cfd']:
            file_icons.append("📊")
        if files['throughput']:
            file_icons.append("📈")
        if files['leadtime']:
            file_icons.append("⏱️")
        if files['tickets']:
            file_icons.append("🎫")
        if files['retrocards']:
            file_icons.append("💬")

        files_str = " ".join(file_icons) if file_icons else ""

        # Número da opção
        num_str = f"{Colors.BOLD}{index:2d}{Colors.ENDC}"
        print(f"      {num_str}. {retro['date']} {status} {files_str}")
        index += 1

    # Resumo
    total = len(retros)
    with_report = sum(1 for r in retros if r['has_report'])
    teams = len(set(r['team'] for r in retros))

    print(f"\n{Colors.BOLD}Resumo:{Colors.ENDC} {total} retrospectiva(s) | {with_report} com report | {teams} time(s)")
    print(f"{Colors.OKCYAN}Legenda: ✅ com report | ⏳ sem report | 📊 CFD | 📈 Throughput | ⏱️ Lead Time | 🎫 Tickets | 💬 Retrocards{Colors.ENDC}")
    print()

    # Seleção
    choice = get_input("Número da retrospectiva (ou Enter para voltar)", "")

    if not choice:
        return

    try:
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(retros):
            selected = retros[selected_index]
            open_retrospective(selected)
        else:
            print_error("Número inválido!")
    except ValueError:
        print_error("Digite um número válido!")


def open_retrospective(retro):
    """Abre a retrospectiva no navegador padrão"""
    report_path = Path(retro['path']) / 'report.md'

    if not report_path.exists():
        print_warning(f"report.md não encontrado em {retro['path']}")
        print_info("Deseja abrir o diretório da retrospectiva?")
        choice = get_input("(s/n)", "s")
        if choice.lower() == 's':
            dir_path = Path(retro['path']).resolve()
            webbrowser.open(f"file://{dir_path}")
        return

    # Converte para caminho absoluto
    abs_path = report_path.resolve()

    print_info(f"Abrindo: {abs_path}")

    # Abre no navegador padrão
    webbrowser.open(f"file://{abs_path}")
    print_success(f"Retrospectiva aberta no navegador!")


def get_existing_quarters(team):
    """Retorna lista de quarters existentes para um time"""
    path = Path(team)
    if not path.exists():
        return []

    quarters = []
    for item in path.iterdir():
        if item.is_dir() and '-Q' in item.name:
            quarters.append(item.name)
    return sorted(quarters)


def load_env_file():
    """Carrega variáveis do arquivo .env para o ambiente"""
    env_path = Path('.env')
    if not env_path.exists():
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignora linhas vazias e comentários
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove aspas se existirem
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Define variável de ambiente
                    os.environ[key] = value
        
        return True
    except Exception as e:
        print_error(f"Erro ao carregar .env: {e}")
        return False


def check_env_file():
    """Verifica se arquivo .env existe e está configurado"""
    env_path = Path('.env')
    if not env_path.exists():
        print_error("Arquivo .env não encontrado!")
        print_info("Crie um arquivo .env na raiz do projeto com:")
        print("""
JIRA_EMAIL=seu-email@empresa.com
JIRA_API_TOKEN=seu-token-aqui
JIRA_SITE=seusite.atlassian.net
JIRA_BOARD_<TIME>=<board-id>
        """)
        return False
    
    # Carrega o .env
    if not load_env_file():
        return False
    
    # Verifica variáveis essenciais
    required = ['JIRA_EMAIL', 'JIRA_API_TOKEN', 'JIRA_SITE']
    missing = [var for var in required if var not in os.environ]
    
    if missing:
        print_error(f"Variáveis faltando no .env: {', '.join(missing)}")
        return False
    
    print_info("Arquivo .env carregado com sucesso")
    return True


def run_step(title, command, cwd=None):
    """Executa um passo do wizard"""
    print_header(title)
    print_info(f"Executando: {command}")
    print()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            text=True
        )
        print_success(f"{title} concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{title} falhou!")
        print_error(f"Código de saída: {e.returncode}")
        return False


def create_structure(team, quarter, date):
    """Cria estrutura de diretórios"""
    path = Path(team) / quarter / date
    
    if path.exists():
        print_warning(f"Diretório já existe: {path}")
        response = get_input("Deseja continuar mesmo assim? (s/n)", "s")
        if response.lower() != 's':
            return False
    
    os.makedirs(path, exist_ok=True)
    print_success(f"Estrutura criada: {path}")
    return True


def extract_jira_data(team, quarter, date):
    """Extrai dados do Jira"""
    output_dir = f"{team}/{quarter}/{date}"
    script_path = "jira_extracter.py"
    
    days = get_input("Número de dias para extrair", "14")
    
    command = f"python3 {script_path} --days {days} --output-dir {output_dir}"
    
    return run_step(
        f"Extraindo Dados do Jira ({days} dias)",
        command
    )


def generate_charts(team, quarter, date):
    """Gera gráficos das métricas"""
    retro_path = f"{team}/{quarter}/{date}"
    script_path = "generate_metrics_charts.py"
    
    command = f"python3 {script_path} {retro_path}"
    
    return run_step(
        "Gerando Gráficos (CFD, Throughput, Lead Time, Tickets)",
        command
    )


def analyze_with_claude(team, quarter, date):
    """Chama Claude Code CLI para análise"""
    retro_path = f"{team}/{quarter}/{date}"

    print_header("Análise com Claude Code")
    print_info("Invocando Claude Code para análise dos dados...")
    print()

    # Monta prompt para o Claude
    prompt = f"Analise a retrospectiva com a skill analyze-retro o {retro_path}/ e gere o report.md completo."

    print(f"{Colors.OKBLUE}Prompt para o Claude:{Colors.ENDC}")
    print(f"{Colors.BOLD}{prompt}{Colors.ENDC}")
    print()

    response = get_input("Deseja executar o Claude Code agora? (s/n)", "s")

    if response.lower() == 's':
        try:
            subprocess.run(["claude", "--version"],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("Claude Code CLI não está instalado!")
            print_info("Instale com: npm install -g @anthropic-ai/claude-code")
            return False

        print_info("Executando Claude Code...")
        print()

        # Executa Claude Code com o prompt
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "Edit,Write,Read,Glob,Grep,Bash,Skill"],
            text=True
        )

        if result.returncode == 0:
            print_success("Análise concluída com sucesso!")
            return True
        else:
            print_error("Erro durante a análise com Claude Code")
            return False
    else:
        print_warning("Análise com Claude pulada.")
        print_info(f"Execute manualmente: claude -p 'analyze-retro {retro_path}'")
        return False


def publish_to_slack(team, quarter, date):
    """Publica retrospectiva no Slack como Canvas"""
    retro_path = f"{team}/{quarter}/{date}"
    report_path = f"{retro_path}/report.md"
    script_path = "publish_canvas_to_slack.py"

    print_header("Publicar no Slack")

    # Verifica se report.md existe
    if not Path(report_path).exists():
        print_error(f"Arquivo não encontrado: {report_path}")
        print_info("Execute a análise primeiro para gerar o report.md")
        return False

    # Verifica SLACK_BOT_TOKEN
    if not os.environ.get("SLACK_BOT_TOKEN"):
        print_error("SLACK_BOT_TOKEN não configurado!")
        print_info("Adicione ao .env: SLACK_BOT_TOKEN=xoxb-seu-token")
        return False

    title = get_input("Título do Canvas", f"Retrospectiva {team.capitalize()} {date}")

    command = f'python3 {script_path} "{report_path}" "{title}"'

    return run_step("Publicando Canvas no Slack", command)


def main_menu():
    """Menu principal do wizard"""
    print_header("🔮 Retro Wizard - Assistente de Retrospectivas")

    print(f"{Colors.BOLD}Escolha uma opção:{Colors.ENDC}\n")
    print("1. 🚀 Fluxo Completo (Criar + Extrair + Gerar Gráficos + Analisar)")
    print("2. 📁 Apenas Criar Estrutura de Diretórios")
    print("3. 📊 Apenas Extrair Dados do Jira")
    print("4. 📈 Apenas Gerar Gráficos")
    print("5. 🤖 Apenas Analisar com Claude")
    print("6. 📤 Publicar no Slack")
    print("7. 📋 Listar Retrospectivas")
    print("8. ❌ Sair")
    print()

    choice = get_input("Opção", "1")
    return choice


def collect_info():
    """Coleta informações do usuário"""
    print_header("📝 Informações da Retrospectiva")

    # Time - sugere times existentes
    existing_teams = get_existing_teams()
    default_team = existing_teams[0] if existing_teams else "financeiro"

    if existing_teams:
        print_info(f"Times existentes: {', '.join(existing_teams)}")

    team = get_input("Nome do time", default_team)

    # Quarter - sugere o quarter atual
    current_quarter = get_current_quarter()
    existing_quarters = get_existing_quarters(team)

    if existing_quarters:
        print_info(f"Quarters existentes para {team}: {', '.join(existing_quarters)}")

    while True:
        quarter_input = get_input("Quarter", current_quarter)
        quarter = validate_quarter(quarter_input)
        if quarter:
            break
        print_error("Quarter inválido! Use formato YYYY-QN (ex: 2026-Q1)")

    # Data - sugere a última data existente no quarter ou data atual
    last_date = get_last_retro_date(team, quarter)
    if last_date:
        suggested_date = last_date
        print_info(f"Última retrospectiva em {quarter}: {last_date}")
    else:
        suggested_date = datetime.now().strftime('%Y-%m-%d')

    while True:
        date_input = get_input("Data da retrospectiva (DD/MM/YYYY ou YYYY-MM-DD)", suggested_date)
        date = validate_date(date_input)
        if date:
            break
        print_error("Data inválida! Use formato DD/MM/YYYY ou YYYY-MM-DD")

    print()
    print_info(f"Time: {team}")
    print_info(f"Data: {date}")
    print_info(f"Quarter: {quarter}")
    print_info(f"Caminho: {team}/{quarter}/{date}")
    print()

    confirm = get_input("Confirma as informações? (s/n)", "s")
    if confirm.lower() != 's':
        return None

    return team, quarter, date


def run_workflow(steps, team, quarter, date):
    """Executa workflow com os passos selecionados"""
    results = []
    
    if 'create' in steps:
        success = create_structure(team, quarter, date)
        results.append(('Criar Estrutura', success))
        if not success:
            return results
    
    if 'extract' in steps:
        if not check_env_file():
            print_error("Configure o arquivo .env antes de extrair dados do Jira")
            results.append(('Extrair Dados', False))
            return results
        
        success = extract_jira_data(team, quarter, date)
        results.append(('Extrair Dados', success))
        if not success:
            return results
    
    if 'charts' in steps:
        success = generate_charts(team, quarter, date)
        results.append(('Gerar Gráficos', success))
        if not success:
            return results
    
    if 'analyze' in steps:
        success = analyze_with_claude(team, quarter, date)
        results.append(('Analisar com Claude', success))

    if 'publish' in steps:
        success = publish_to_slack(team, quarter, date)
        results.append(('Publicar no Slack', success))

    return results


def print_summary(results):
    """Imprime resumo da execução"""
    print_header("📊 Resumo da Execução")
    
    for step, success in results:
        if success:
            print_success(f"{step}")
        else:
            print_error(f"{step}")
    
    all_success = all(success for _, success in results)
    
    print()
    if all_success:
        print_success("Todas as etapas foram concluídas com sucesso! 🎉")
    else:
        print_warning("Algumas etapas falharam. Verifique os erros acima.")


def main():
    """Função principal"""
    try:
        # Carrega .env se existir (silenciosamente)
        load_env_file()

        while True:
            choice = main_menu()

            if choice == '8':
                print_info("Até logo! 👋")
                sys.exit(0)

            # Opção de listar retrospectivas (não precisa coletar info)
            if choice == '7':
                show_retrospectives_list()
                print()
                continue_choice = get_input("Deseja realizar outra operação? (s/n)", "n")
                if continue_choice.lower() != 's':
                    print_info("Até logo! 👋")
                    break
                continue

            # Coleta informações
            info = collect_info()
            if not info:
                print_warning("Operação cancelada.")
                continue

            team, quarter, date = info

            # Define steps baseado na escolha
            steps_map = {
                '1': ['create', 'extract', 'charts', 'analyze'],  # Completo
                '2': ['create'],
                '3': ['extract'],
                '4': ['charts'],
                '5': ['analyze'],
                '6': ['publish'],
            }

            steps = steps_map.get(choice, [])

            if not steps:
                print_error("Opção inválida!")
                continue

            # Executa workflow
            results = run_workflow(steps, team, quarter, date)

            # Mostra resumo
            print_summary(results)

            # Pergunta se quer continuar
            print()
            continue_choice = get_input("Deseja realizar outra operação? (s/n)", "n")
            if continue_choice.lower() != 's':
                print_info("Até logo! 👋")
                break

    except KeyboardInterrupt:
        print()
        print_warning("Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
