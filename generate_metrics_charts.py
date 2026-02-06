#!/usr/bin/env python3
"""
Script para gerar gráficos de métricas de retrospectiva.

Modos de uso:

1. Gerar todos os gráficos de uma retrospectiva (CFD, Throughput, Lead Time, Tickets):
    python generate_metrics_charts.py <caminho_da_retrospectiva>
    Exemplo: python generate_metrics_charts.py financeiro/2026-Q1/2026-01-16/

2. Gerar apenas gráfico de tickets de um CSV:
    python generate_metrics_charts.py <caminho_do_csv> [saida.png]
    Exemplo: python generate_metrics_charts.py tickets.csv
    Exemplo: python generate_metrics_charts.py tickets.csv meu_grafico.png
"""

import sys
from pathlib import Path


def setup_venv():
    """Configura ambiente virtual e instala dependências."""
    venv_path = Path(__file__).parent / ".venv"

    if not venv_path.exists():
        print("Criando ambiente virtual...")
        import subprocess
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

        pip_path = venv_path / "bin" / "pip"
        print("Instalando dependências...")
        subprocess.run([str(pip_path), "install", "-q", "pandas", "matplotlib"], check=True)
        print("Ambiente configurado com sucesso!\n")

    return venv_path / "bin" / "python"


def run_in_venv():
    """Executa o script no ambiente virtual."""
    import subprocess
    python_path = setup_venv()

    # Re-executar este script com o Python do venv
    result = subprocess.run([str(python_path), __file__, "--in-venv"] + sys.argv[1:])
    sys.exit(result.returncode)


def generate_single_ticket_chart(csv_path: str, output_path: str = None):
    """
    Gera apenas o gráfico de rosca de tickets a partir de um CSV.
    Compatível com o antigo generate_chart.py.
    
    Args:
        csv_path: Caminho para o arquivo CSV
        output_path: Caminho para salvar o gráfico (opcional)
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    # Cores semânticas
    COLORS_TICKETS = {
        'Incidente': '#DC2626',
        'Incident': '#DC2626',
        'Bug': '#F97316',
        'Tarefa': '#10B981',
        'Task': '#10B981',
        'História': '#3B82F6',
        'Story': '#3B82F6',
        'Sub-tarefa': '#8B5CF6',
        'Subtask': '#8B5CF6',
        'Melhoria': '#06B6D4',
        'Improvement': '#06B6D4'
    }

    # Ler o CSV
    df = pd.read_csv(csv_path)

    # Contar a frequência de cada tipo de item
    item_counts = df['Tipo de item'].value_counts()

    # Cores semânticas
    colors = [COLORS_TICKETS.get(tipo, '#6B7280') for tipo in item_counts.index]

    # Criar figura e eixo
    fig, ax = plt.subplots(figsize=(10, 8))

    # Criar gráfico de rosca
    wedges, texts, autotexts = ax.pie(
        item_counts.values,
        labels=item_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.85,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )

    # Criar o "buraco" da rosca
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    # Adicionar título
    plt.title('Distribuição de Tipos de Itens',
              fontsize=14,
              pad=20)

    # Garantir que o gráfico seja circular
    ax.axis('equal')

    # Ajustar layout para evitar cortes
    plt.tight_layout()

    # Salvar ou mostrar o gráfico
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo em: {output_path}")
    else:
        plt.show()

    plt.close()

    # Imprimir estatísticas
    print("\n📊 Estatísticas:")
    print(f"   Total de itens: {len(df)}")
    print("\n   Distribuição por tipo:")
    for item_type, count in item_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   • {item_type}: {count} ({percentage:.1f}%)")


def generate_charts(retro_path: str):
    """
    Gera os 4 gráficos de métricas.
    
    Args:
        retro_path: Caminho para a pasta da retrospectiva
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')

    # Configuração de cores (baseado no Jira)
    COLORS_CFD = {
        'IN PROGRESS': '#8BC34A',    # Verde claro
        'CODE REVIEW': '#4CAF50',    # Verde escuro
        'READY TO TEST': '#FF9800',  # Laranja
        'TESTING': '#90CAF9',        # Azul claro
        'BLOCKED': '#DC2626'
    }

    COLORS_TICKETS = {
        'Incidente': '#DC2626',
        'Incident': '#DC2626',
        'Bug': '#F97316',
        'Tarefa': '#10B981',
        'Task': '#10B981',
        'História': '#3B82F6',
        'Story': '#3B82F6',
        'Sub-tarefa': '#8B5CF6',
        'Subtask': '#8B5CF6',
        'Melhoria': '#06B6D4',
        'Improvement': '#06B6D4'
    }

    retro_dir = Path(retro_path)
    
    # ========== CFD CHART ==========
    cfd_file = retro_dir / 'cfd.csv'
    if cfd_file.exists():
        try:
            df_cfd = pd.read_csv(cfd_file)
            df_cfd['Date'] = pd.to_datetime(df_cfd['Date'])

            # Definir ordem e colunas disponíveis (ignorar DONE e READY TO DEV)
            # ORDEM DO STACK: TESTING na base -> READY TO TEST -> CODE REVIEW -> IN PROGRESS no topo
            # Isso reflete o fluxo natural: itens entram em IN PROGRESS e saem em TESTING
            available_columns = ['TESTING', 'READY TO TEST', 'CODE REVIEW', 'IN PROGRESS']
            columns_cfd = [col for col in available_columns if col in df_cfd.columns]
            colors_cfd = [COLORS_CFD[col] for col in columns_cfd]

            fig, ax = plt.subplots(figsize=(14, 7))
            ax.stackplot(df_cfd['Date'],
                         [df_cfd[col] for col in columns_cfd],
                         labels=columns_cfd,
                         colors=colors_cfd,
                         alpha=0.85)

            ax.set_xlim(df_cfd['Date'].min(), df_cfd['Date'].max())
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Number of Items', fontsize=12)
            ax.set_title('Cumulative Flow Diagram (CFD)', fontsize=14, pad=15)
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3, linestyle='--')
            plt.tight_layout()
            plt.savefig(retro_dir / 'cfd.png', dpi=300, bbox_inches='tight')
            plt.close()
            print('✅ CFD gerado')
        except Exception as e:
            print(f'⚠️  Erro ao gerar CFD: {e}')
    else:
        print('⚠️  cfd.csv não encontrado')

    # ========== THROUGHPUT CHART ==========
    tp_file = retro_dir / 'throughput.csv'
    if tp_file.exists():
        try:
            df_tp = pd.read_csv(tp_file)
            df_tp['Period'] = pd.to_datetime(df_tp['Period'])

            # Calcular médias móvel e acumulada
            df_tp['Rolling_Avg'] = df_tp['Throughput'].rolling(window=3, min_periods=1).mean()
            df_tp['Accumulated_Avg'] = df_tp['Throughput'].expanding().mean()

            fig, ax = plt.subplots(figsize=(14, 7))

            # Barras semanais
            x_pos = range(len(df_tp))
            ax.bar(x_pos, df_tp['Throughput'], color='#1E88E5', alpha=0.7, label='Throughput', width=0.6)

            # Linhas de média
            ax.plot(x_pos, df_tp['Rolling_Avg'], color='#FF6B35', linewidth=2,
                    marker='o', markersize=6, label='Rolling Average (3 weeks)')
            ax.plot(x_pos, df_tp['Accumulated_Avg'], color='#059669', linewidth=2,
                    marker='s', markersize=6, label='Accumulated Average')

            ax.set_xticks(x_pos)
            ax.set_xticklabels(df_tp['Period'].dt.strftime('%Y-%m-%d'), rotation=45, ha='right')
            ax.set_xlabel('Week Start', fontsize=12)
            ax.set_ylabel('Items Completed', fontsize=12)
            ax.set_title('Throughput Semanal', fontsize=14, pad=15)
            ax.legend(loc='upper right', fontsize=10)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            plt.tight_layout()
            plt.savefig(retro_dir / 'throughput.png', dpi=300, bbox_inches='tight')
            plt.close()
            print('✅ Throughput gerado')
        except Exception as e:
            print(f'⚠️  Erro ao gerar Throughput: {e}')
    else:
        print('⚠️  throughput.csv não encontrado')

    # ========== LEAD TIME CHART ==========
    lt_file = retro_dir / 'leadtime.csv'
    if lt_file.exists():
        try:
            df_lt = pd.read_csv(lt_file)
            df_lt.columns = df_lt.columns.str.strip()

            # Expandir dados
            leadtimes = []
            for _, row in df_lt.iterrows():
                leadtimes.extend([row['Leadtime']] * int(row['item count']))

            leadtimes = np.array(leadtimes)
            unique_lt = np.sort(np.unique(leadtimes))
            counts = [np.sum(leadtimes == lt) for lt in unique_lt]

            # Percentual acumulado
            cumulative = np.cumsum(counts)
            cumulative_pct = (cumulative / cumulative[-1]) * 100

            # Percentis
            p50 = np.percentile(leadtimes, 50)
            p90 = np.percentile(leadtimes, 90)

            # Gráfico com duplo eixo Y
            fig, ax1 = plt.subplots(figsize=(14, 7))

            # Barras (eixo esquerdo)
            ax1.bar(unique_lt, counts, color='#1E88E5', alpha=0.7, label='Issue Count', width=0.8)
            ax1.set_xlabel('Lead Time (dias)', fontsize=12)
            ax1.set_ylabel('Issue Count', fontsize=12, color='#1E88E5')
            ax1.tick_params(axis='y', labelcolor='#1E88E5')

            # Linhas de percentil
            ax1.axvline(x=p50, color='#059669', linestyle='--', linewidth=2, label=f'p50: {p50:.1f}d')
            ax1.axvline(x=p90, color='#DC2626', linestyle='--', linewidth=2, label=f'p90: {p90:.1f}d')

            # Linha acumulada (eixo direito)
            ax2 = ax1.twinx()
            ax2.plot(unique_lt, cumulative_pct, color='#FF6B35', linewidth=2.5,
                     marker='o', markersize=6, label='Acc percentage')
            ax2.set_ylabel('Accumulated %', fontsize=12, color='#FF6B35')
            ax2.tick_params(axis='y', labelcolor='#FF6B35')
            ax2.set_ylim(0, 105)

            # Título e legendas
            ax1.set_title('Lead time distribution', fontsize=14, pad=15)

            # Combinar legendas
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

            ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
            plt.tight_layout()
            plt.savefig(retro_dir / 'leadtime.png', dpi=300, bbox_inches='tight')
            plt.close()
            print('✅ Lead Time gerado')
        except Exception as e:
            print(f'⚠️  Erro ao gerar Lead Time: {e}')
    else:
        print('⚠️  leadtime.csv não encontrado')

    # ========== TICKETS CHART ==========
    tickets_file = retro_dir / 'tickets.csv'
    if tickets_file.exists():
        try:
            df_tickets = pd.read_csv(tickets_file)
            type_counts = df_tickets['Tipo de item'].value_counts()

            # Cores semânticas
            colors = [COLORS_TICKETS.get(tipo, '#6B7280') for tipo in type_counts.index]

            # Gráfico de rosca
            fig, ax = plt.subplots(figsize=(10, 8))
            wedges, texts, autotexts = ax.pie(
                type_counts.values,
                labels=type_counts.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                pctdistance=0.85,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )

            # Criar donut
            centre_circle = plt.Circle((0, 0), 0.70, fc='white')
            fig.gca().add_artist(centre_circle)

            ax.set_title('Distribuição de Tipos de Itens', fontsize=14, pad=20)
            plt.tight_layout()
            plt.savefig(retro_dir / 'tickets.png', dpi=300, bbox_inches='tight')
            plt.close()
            print('✅ Tickets gerado')
        except Exception as e:
            print(f'⚠️  Erro ao gerar Tickets: {e}')
    else:
        print('⚠️  tickets.csv não encontrado')

    print('\n✅ TODOS OS GRÁFICOS PROCESSADOS!')


def main():
    # Se não estiver rodando no venv, configura e re-executa
    if "--in-venv" not in sys.argv:
        run_in_venv()
        return

    # Remove o flag --in-venv dos argumentos
    sys.argv.remove("--in-venv")

    if len(sys.argv) < 2:
        print("Uso:")
        print("  1. Gerar todos os gráficos de uma retrospectiva:")
        print("     python generate_metrics_charts.py <caminho_da_retrospectiva>")
        print("\n  2. Gerar apenas gráfico de tickets de um CSV:")
        print("     python generate_metrics_charts.py <caminho_do_csv> [saida.png]")
        print("\nExemplos:")
        print("  python generate_metrics_charts.py financeiro/2026-Q1/2026-01-16/")
        print("  python generate_metrics_charts.py tickets.csv")
        print("  python generate_metrics_charts.py tickets.csv meu_grafico.png")
        sys.exit(1)

    path_arg = sys.argv[1]
    path = Path(path_arg)

    # Verificar se o arquivo/diretório existe
    if not path.exists():
        print(f"Erro: Caminho não encontrado: {path_arg}")
        sys.exit(1)

    try:
        # Modo 1: Se for um diretório, gerar todos os gráficos
        if path.is_dir():
            generate_charts(path_arg)
        
        # Modo 2: Se for um arquivo CSV, gerar apenas gráfico de tickets
        elif path.is_file() and path.suffix == '.csv':
            output_path = sys.argv[2] if len(sys.argv) > 2 else None
            generate_single_ticket_chart(path_arg, output_path)
        
        else:
            print(f"Erro: '{path_arg}' deve ser um diretório ou arquivo CSV")
            sys.exit(1)
            
    except Exception as e:
        print(f"Erro ao gerar gráfico(s): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
