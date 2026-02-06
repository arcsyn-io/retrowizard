#!/usr/bin/env python3
"""
Skill: analyze-quarter
Gera análise consolidada de retrospectivas de um quarter completo
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import numpy as np
from datetime import datetime
import seaborn as sns
import sys
import re

# Configuração de estilo
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def find_retro_folders(quarter_dir):
    """Encontra todas as pastas de retrospectiva (formato YYYY-MM-DD) no quarter"""
    retros = []
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    for item in sorted(quarter_dir.iterdir()):
        if item.is_dir() and pattern.match(item.name):
            retros.append(item.name)

    return sorted(retros)

def load_all_data(quarter_dir, retros):
    """Carrega todos os CSVs de todas as retrospectivas"""
    data = {
        'throughput': [],
        'leadtime': [],
        'tickets': []
    }

    for retro in retros:
        retro_dir = quarter_dir / retro

        # Throughput
        throughput_file = retro_dir / 'throughput.csv'
        if throughput_file.exists():
            df = pd.read_csv(throughput_file)
            df['retro'] = retro
            data['throughput'].append(df)

        # Lead time
        leadtime_file = retro_dir / 'leadtime.csv'
        if leadtime_file.exists():
            df = pd.read_csv(leadtime_file)
            df['retro'] = retro
            data['leadtime'].append(df)

        # Tickets
        tickets_file = retro_dir / 'tickets.csv'
        if tickets_file.exists():
            df = pd.read_csv(tickets_file)
            df['retro'] = retro
            data['tickets'].append(df)

    # Concatenar dataframes
    for key in data:
        if data[key]:
            data[key] = pd.concat(data[key], ignore_index=True)
        else:
            data[key] = pd.DataFrame()

    return data

def calculate_p90(leadtime_df):
    """Calcula o percentil 90 do lead time"""
    if leadtime_df.empty:
        return 0

    expanded = []
    for _, row in leadtime_df.iterrows():
        expanded.extend([row['Leadtime']] * int(row['item count']))

    return np.percentile(expanded, 90) if expanded else 0

def calculate_median(leadtime_df):
    """Calcula a mediana do lead time"""
    if leadtime_df.empty:
        return 0

    expanded = []
    for _, row in leadtime_df.iterrows():
        expanded.extend([row['Leadtime']] * int(row['item count']))

    return np.median(expanded) if expanded else 0

def calculate_cv(data):
    """Calcula o coeficiente de variação"""
    if len(data) == 0:
        return 0
    mean = np.mean(data)
    if mean == 0:
        return 0
    std = np.std(data)
    return (std / mean) * 100

def chart_1_throughput_evolution(data, output_dir, quarter_name, retros):
    """Gráfico 1: Evolução do Throughput por Semana"""
    df = data['throughput'].copy()
    df['Period'] = pd.to_datetime(df['Period'])
    df = df.sort_values('Period')

    # Se houver múltiplos valores para a mesma semana, usar o maior
    df = df.groupby('Period', as_index=False)['Throughput'].max()

    # Filtrar valores zero
    df_filtered = df[df['Throughput'] > 0].copy()

    # Identificar período de crise e recuperação
    min_throughput = df_filtered['Throughput'].min()
    min_idx = df_filtered['Throughput'].idxmin()
    crisis_date = df_filtered.loc[min_idx, 'Period']

    # Calcular médias por período
    crisis_mask = df_filtered['Period'] <= crisis_date
    recovery_mask = df_filtered['Period'] > crisis_date

    pre_crisis_mean = df_filtered[crisis_mask]['Throughput'].mean() if crisis_mask.any() else 0
    post_recovery_mean = df_filtered[recovery_mask]['Throughput'].mean() if recovery_mask.any() else 0

    # Determinar recuperação (últimas 3-4 semanas)
    recovery_start = df_filtered[recovery_mask]['Period'].min() if recovery_mask.any() else None

    fig, ax = plt.subplots(figsize=(14, 7))

    # Plot da linha principal
    ax.plot(df_filtered['Period'], df_filtered['Throughput'],
            marker='o', linewidth=3, markersize=10, color='#2E86AB', label='Throughput Semanal')

    # Adicionar valores nos pontos
    for _, row in df_filtered.iterrows():
        ax.text(row['Period'], row['Throughput'] + 1, str(int(row['Throughput'])),
                ha='center', fontsize=10, fontweight='bold', color='#2E86AB')

    # Marcar ponto de crise
    ax.plot(crisis_date, min_throughput, marker='X', markersize=20,
            color='#C73E1D', label='Crise (0-3 itens)', zorder=5)

    # Área de recuperação
    if recovery_start is not None:
        recovery_data = df_filtered[recovery_mask]
        ax.axvspan(recovery_start, df_filtered['Period'].max(),
                  alpha=0.2, color='#06A77D', label='Período de Recuperação')

    # Adicionar estatísticas
    stats_text = f"Médias por Período:\n"
    if pre_crisis_mean > 0:
        stats_text += f"• Novembro: {pre_crisis_mean:.1f} itens/sem\n"
    if post_recovery_mean > 0 and pre_crisis_mean > 0:
        improvement = ((post_recovery_mean - pre_crisis_mean) / pre_crisis_mean) * 100
        stats_text += f"• Dezembro (início): {df_filtered[recovery_mask].head(2)['Throughput'].mean():.1f} itens/sem (+{improvement:.0f}%)\n"
        stats_text += f"• Dezembro (atual): {post_recovery_mean:.1f} itens/sem (+{((post_recovery_mean - pre_crisis_mean) / pre_crisis_mean * 100):.0f}%)"

    ax.text(0.98, 0.03, stats_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Título dinâmico
    if min_throughput <= 5 and post_recovery_mean > 15:
        title = f'Recuperação Dramática do Throughput\nDe {int(min_throughput)} itens/semana para {int(post_recovery_mean)} itens/semana'
    else:
        title = f'Evolução do Throughput - {quarter_name}'

    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Semana', fontsize=13)
    ax.set_ylabel('Itens Entregues', fontsize=13)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / '01_throughput_evolution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Gráfico 1: Evolução do Throughput")

def chart_2_variability_improvement(data, output_dir, quarter_name, retros):
    """Gráfico 2: Melhoria na Previsibilidade (Variabilidade)"""
    variability_data = []

    for retro in retros:
        retro_data = data['throughput'][data['throughput']['retro'] == retro]
        if not retro_data.empty:
            valid_data = retro_data[retro_data['Throughput'] > 0]
            if len(valid_data) >= 3:
                cv = calculate_cv(valid_data['Throughput'].values)
                variability_data.append({
                    'retro': retro,
                    'cv': cv,
                    'label': retro[-5:].replace('-', '/')
                })

    if not variability_data:
        print("⚠ Dados insuficientes para gráfico de variabilidade")
        return

    df = pd.DataFrame(variability_data)

    # Calcular redução
    initial_cv = df.iloc[0]['cv']
    final_cv = df.iloc[-1]['cv']
    reduction_pct = ((initial_cv - final_cv) / initial_cv) * 100

    fig, ax = plt.subplots(figsize=(12, 7))

    # Definir cores baseadas em zonas
    colors = []
    for cv in df['cv']:
        if cv >= 50:
            colors.append('#C73E1D')  # Vermelho - Muito Alta
        elif cv >= 30:
            colors.append('#F18F01')  # Laranja - Moderada
        else:
            colors.append('#06A77D')  # Verde - Previsível

    # Barras
    bars = ax.bar(range(len(df)), df['cv'], color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Valores nas barras
    for i, (bar, cv) in enumerate(zip(bars, df['cv'])):
        ax.text(i, cv + 1.5, f'{cv:.0f}%', ha='center', fontsize=13, fontweight='bold')

    # Linha de tendência
    ax.plot(range(len(df)), df['cv'], color='#2E2E2E', linestyle='--', linewidth=2,
            marker='o', markersize=8, label='Tendência de Melhoria', alpha=0.7)

    # Anotação da melhoria
    mid_point = len(df) // 2
    if reduction_pct > 0:
        ax.annotate(f'De "Muito Alta" para\n"Moderada"\n(-{reduction_pct:.1f}%)',
                   xy=(mid_point, df['cv'].mean()), xytext=(mid_point, df['cv'].mean() + 10),
                   fontsize=12, ha='center',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=2),
                   arrowprops=dict(arrowstyle='->', lw=2))

    # Zonas de referência
    ax.axhspan(50, 100, alpha=0.1, color='#C73E1D', label='Zona Instável')
    ax.axhspan(30, 50, alpha=0.1, color='#F18F01', label='Zona Moderada')
    ax.axhspan(0, 30, alpha=0.1, color='#06A77D', label='Zona Previsível')

    ax.set_title(f'Melhoria na Previsibilidade do Time\nRedução de {reduction_pct:.1f}% na Variabilidade',
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Período', fontsize=13)
    ax.set_ylabel('Variabilidade (%)', fontsize=13)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['label'], fontsize=11)
    ax.legend(loc='upper right', fontsize=10)
    ax.set_ylim(0, max(df['cv']) + 15)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_dir / '02_variability_improvement.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Gráfico 2: Melhoria na Previsibilidade")

def chart_3_leadtime_velocity(data, output_dir, quarter_name, retros):
    """Gráfico 3: Lead Time - Velocidade e Consistência"""
    leadtime_stats = []

    for retro in retros:
        retro_data = data['leadtime'][data['leadtime']['retro'] == retro]
        if not retro_data.empty:
            p90 = calculate_p90(retro_data)
            median = calculate_median(retro_data)
            leadtime_stats.append({
                'retro': retro,
                'p90': p90,
                'median': median,
                'label': retro[-5:].replace('-', '/')
            })

    if not leadtime_stats:
        print("⚠ Dados insuficientes para gráfico de lead time")
        return

    df = pd.DataFrame(leadtime_stats)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Gráfico 1: Lead Time P90 (Consistência)
    bars1 = ax1.bar(range(len(df)), df['p90'], color='#4A90E2', alpha=0.7, edgecolor='black')
    for i, (bar, p90) in enumerate(zip(bars1, df['p90'])):
        ax1.text(i, p90 + 0.3, f'{p90:.0f} dias', ha='center', fontsize=11, fontweight='bold')

    # Linha de meta
    meta_p90 = 8
    ax1.axhline(y=meta_p90, color='#06A77D', linestyle='--', linewidth=2, label=f'Meta: ≤{meta_p90} dias')

    # Anotação
    ax1.annotate(f'90% dos itens\nentregues em até\n{int(df["p90"].mean()):.0f} dias',
                xy=(len(df)//2, df['p90'].mean()), xytext=(len(df)//2, df['p90'].max() + 1),
                fontsize=10, ha='center',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black'))

    ax1.set_title('Lead Time p90 Consistente', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Período', fontsize=11)
    ax1.set_ylabel('Dias', fontsize=11)
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels(df['label'])
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim(0, max(df['p90']) + 3)

    # Gráfico 2: Lead Time Mediano (Velocidade)
    bars2 = ax2.bar(range(len(df)), df['median'], color='#06A77D', alpha=0.7, edgecolor='black')
    for i, (bar, median) in enumerate(zip(bars2, df['median'])):
        ax2.text(i, median + 0.15, f'{median:.1f} dias', ha='center', fontsize=11, fontweight='bold')

    # Anotação de melhoria
    if len(df) > 1:
        best_median = df['median'].min()
        ax2.annotate(f'50% dos itens\nentregues em\napenas {best_median:.0f}-{df["median"].iloc[-1]:.0f} dias!',
                    xy=(len(df)-1, df['median'].iloc[-1]), xytext=(len(df)//2, df['median'].max() + 1.5),
                    fontsize=10, ha='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black'))

    ax2.set_title('Lead Time Mediano Excelente', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Período', fontsize=11)
    ax2.set_ylabel('Dias', fontsize=11)
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(df['label'])
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_ylim(0, max(df['median']) + 2.5)

    fig.suptitle('Lead Time: Velocidade e Consistência', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '03_leadtime_velocity.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Gráfico 3: Lead Time - Velocidade e Consistência")

def chart_4_epic_heatmap(data, output_dir, quarter_name, retros):
    """Gráfico 4: Totais por Épico"""
    df = data['tickets']

    if df.empty or 'Chave pai' not in df.columns or 'Parent summary' not in df.columns:
        print("⚠ Dados insuficientes para gráfico de épicos")
        return

    # Filtrar apenas itens com épicos
    df_with_epic = df[df['Chave pai'].notna()].copy()

    if df_with_epic.empty:
        print("⚠ Nenhum item com épico encontrado")
        return

    # Contar total por épico
    epic_counts = df_with_epic['Parent summary'].value_counts().head(10)

    # Truncar nomes de épicos para melhor visualização
    def truncate_epic(name, max_len=60):
        if len(name) > max_len:
            return name[:max_len-3] + '...'
        return name

    epic_labels = [truncate_epic(name) for name in epic_counts.index]

    # Cores em gradiente baseado na quantidade
    colors = plt.cm.YlGnBu(np.linspace(0.4, 0.9, len(epic_counts)))

    fig, ax = plt.subplots(figsize=(12, max(8, len(epic_counts) * 0.6)))

    # Barras horizontais
    bars = ax.barh(range(len(epic_counts)), epic_counts.values, color=colors, edgecolor='black', linewidth=1)

    # Adicionar valores nas barras
    for i, (bar, count) in enumerate(zip(bars, epic_counts.values)):
        ax.text(count + 0.5, i, str(count), va='center', fontsize=12, fontweight='bold')

    ax.set_yticks(range(len(epic_counts)))
    ax.set_yticklabels(epic_labels, fontsize=11)
    ax.set_xlabel('Itens Entregues', fontsize=13)
    ax.set_title(f'Total de Entregas por Épico - {quarter_name}',
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, max(epic_counts.values) * 1.15)

    # Adicionar total geral
    total_items = epic_counts.sum()
    ax.text(0.98, 0.02, f'Total: {total_items} itens nos top {len(epic_counts)} épicos',
            transform=ax.transAxes, fontsize=11, ha='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_dir / '04_epic_totals.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Gráfico 4: Totais por Épico")

def generate_quarterly_report(data, output_dir, quarter_name, retros):
    """Gera relatório consolidado do quarter com insights"""

    # Calcular métricas consolidadas
    df_throughput = data['throughput'].copy()
    df_throughput['Period'] = pd.to_datetime(df_throughput['Period'])
    df_throughput = df_throughput.groupby('Period', as_index=False)['Throughput'].max()
    df_throughput_filtered = df_throughput[df_throughput['Throughput'] > 0]

    df_leadtime = data['leadtime']
    df_tickets = data['tickets']

    # Métricas gerais
    total_tickets = len(df_tickets)
    avg_throughput = df_throughput_filtered['Throughput'].mean()
    median_throughput = df_throughput_filtered['Throughput'].median()
    min_throughput = df_throughput_filtered['Throughput'].min()
    max_throughput = df_throughput_filtered['Throughput'].max()

    # Variabilidade
    initial_retro = retros[0]
    final_retro = retros[-1]
    initial_data = data['throughput'][data['throughput']['retro'] == initial_retro]
    final_data = data['throughput'][data['throughput']['retro'] == final_retro]

    initial_cv = calculate_cv(initial_data[initial_data['Throughput'] > 0]['Throughput'].values) if len(initial_data) > 0 else 0
    final_cv = calculate_cv(final_data[final_data['Throughput'] > 0]['Throughput'].values) if len(final_data) > 0 else 0
    cv_improvement = ((initial_cv - final_cv) / initial_cv * 100) if initial_cv > 0 else 0

    # Lead time
    p90_overall = calculate_p90(df_leadtime)
    median_overall = calculate_median(df_leadtime)

    # Épicos
    df_with_epic = df_tickets[df_tickets['Chave pai'].notna()] if 'Chave pai' in df_tickets.columns else pd.DataFrame()
    top_epics = df_with_epic['Parent summary'].value_counts().head(5) if not df_with_epic.empty else pd.Series()

    # Tipos de item
    if 'Tipo de item' in df_tickets.columns:
        item_types = df_tickets['Tipo de item'].value_counts()
        bugs_count = item_types.get('Bug', 0)
        incidents_count = item_types.get('Incidente', 0)
        tasks_count = item_types.get('Tarefa', 0)
        bugs_pct = (bugs_count / total_tickets * 100) if total_tickets > 0 else 0
        incidents_pct = (incidents_count / total_tickets * 100) if total_tickets > 0 else 0
    else:
        bugs_count = incidents_count = tasks_count = 0
        bugs_pct = incidents_pct = 0

    # Gerar markdown
    report = f"""# Relatório Consolidado - {quarter_name}

## Sumário Executivo

**Período analisado:** {retros[0]} a {retros[-1]} ({len(retros)} retrospectivas)

### Destaques do Quarter

- ✅ **{total_tickets} itens entregues** no total
- 📈 **Throughput médio:** {avg_throughput:.1f} itens/semana
- ⚡ **Lead Time P90:** {p90_overall:.0f} dias
- 🎯 **Previsibilidade:** Melhoria de {cv_improvement:.1f}% na variabilidade

---

## 1. Análise de Throughput

### Métricas do Quarter

| Métrica | Valor |
|---------|-------|
| **Throughput Médio** | {avg_throughput:.1f} itens/semana |
| **Throughput Mediano** | {median_throughput:.0f} itens/semana |
| **Maior Throughput** | {max_throughput:.0f} itens/semana |
| **Menor Throughput** | {min_throughput:.0f} itens/semana |

### Insights

"""

    # Análise de tendência de throughput
    if max_throughput > min_throughput * 3:
        report += f"- 🚨 **Recuperação dramática observada:** O time saiu de {min_throughput:.0f} itens/semana para {max_throughput:.0f} itens/semana\n"
    elif avg_throughput > 15:
        report += f"- ✅ **Capacidade consistente:** Média de {avg_throughput:.1f} itens/semana demonstra boa produtividade\n"
    else:
        report += f"- ⚠️ **Capacidade em desenvolvimento:** Média de {avg_throughput:.1f} itens/semana pode ser melhorada\n"

    report += f"""
![Evolução do Throughput](./01_throughput_evolution.png)

---

## 2. Previsibilidade e Variabilidade

### Evolução da Variabilidade

| Período | Variabilidade (CV) | Classificação |
|---------|-------------------|---------------|
| **Início ({retros[0][-5:]})** | {initial_cv:.1f}% | {"🔴 Instável" if initial_cv >= 50 else "🟡 Moderada" if initial_cv >= 30 else "🟢 Previsível"} |
| **Final ({retros[-1][-5:]})** | {final_cv:.1f}% | {"🔴 Instável" if final_cv >= 50 else "🟡 Moderada" if final_cv >= 30 else "🟢 Previsível"} |
| **Melhoria** | {cv_improvement:.1f}% | {"✅ Positiva" if cv_improvement > 0 else "⚠️ Atenção necessária"} |

### Insights

"""

    if cv_improvement > 30:
        report += f"- 🎯 **Melhoria significativa:** Redução de {cv_improvement:.1f}% na variabilidade indica evolução na previsibilidade do time\n"
        report += "- ✅ O time está se tornando mais consistente e confiável nas entregas\n"
    elif cv_improvement > 0:
        report += f"- ✅ **Evolução positiva:** Redução de {cv_improvement:.1f}% mostra tendência de melhoria\n"
    else:
        report += "- ⚠️ **Atenção:** Variabilidade não reduziu - investigar fatores de instabilidade\n"

    if final_cv < 30:
        report += "- 🟢 **Zona previsível alcançada:** Time demonstra alta previsibilidade\n"
    elif final_cv < 50:
        report += "- 🟡 **Zona moderada:** Previsibilidade razoável, mas há espaço para melhoria\n"
    else:
        report += "- 🔴 **Zona instável:** Foco em reduzir variabilidade é prioritário\n"

    report += f"""
![Melhoria na Previsibilidade](./02_variability_improvement.png)

---

## 3. Lead Time: Velocidade e Consistência

### Métricas Consolidadas

| Métrica | Valor | Avaliação |
|---------|-------|-----------|
| **Lead Time P90** | {p90_overall:.0f} dias | {"✅ Excelente" if p90_overall <= 8 else "⚠️ Acima da meta"} |
| **Lead Time Mediano** | {median_overall:.0f} dias | {"⚡ Muito rápido" if median_overall <= 2 else "✅ Rápido" if median_overall <= 5 else "⚠️ Pode melhorar"} |

### Insights

"""

    if p90_overall <= 8:
        report += f"- ✅ **P90 excelente:** 90% dos itens entregues em até {p90_overall:.0f} dias - dentro da meta\n"
    else:
        report += f"- ⚠️ **P90 acima da meta:** {p90_overall:.0f} dias - meta é ≤8 dias\n"

    if median_overall <= 2:
        report += f"- ⚡ **Velocidade excepcional:** 50% dos itens entregues em {median_overall:.0f} dias ou menos\n"
    elif median_overall <= 5:
        report += f"- ✅ **Boa velocidade:** Mediana de {median_overall:.0f} dias indica fluxo eficiente\n"
    else:
        report += f"- ⚠️ **Velocidade pode melhorar:** Mediana de {median_overall:.0f} dias sugere oportunidades de otimização\n"

    report += f"""
![Lead Time](./03_leadtime_velocity.png)

---

## 4. Distribuição de Trabalho

### Tipos de Item

| Tipo | Quantidade | Percentual |
|------|-----------|-----------|
| Tarefas | {tasks_count} | {(tasks_count/total_tickets*100):.1f}% |
| Bugs | {bugs_count} | {bugs_pct:.1f}% |
| Incidentes | {incidents_count} | {incidents_pct:.1f}% |

### Top 5 Épicos Mais Produtivos

"""

    if not top_epics.empty:
        for i, (epic, count) in enumerate(top_epics.items(), 1):
            pct = (count / total_tickets * 100)
            report += f"{i}. **{epic[:60]}{'...' if len(epic) > 60 else ''}** - {count} itens ({pct:.1f}%)\n"
    else:
        report += "_Nenhum épico encontrado_\n"

    report += "\n### Insights\n\n"

    # Análise de qualidade
    reactive_work = bugs_pct + incidents_pct
    if reactive_work > 30:
        report += f"- 🔴 **Alta taxa de trabalho reativo:** {reactive_work:.1f}% (bugs + incidentes) - meta é <20%\n"
        report += "- ⚠️ Priorizar melhoria de qualidade e estabilidade\n"
    elif reactive_work > 20:
        report += f"- 🟡 **Trabalho reativo moderado:** {reactive_work:.1f}% (bugs + incidentes)\n"
        report += "- ✅ Monitorar e buscar redução contínua\n"
    else:
        report += f"- ✅ **Baixa taxa de trabalho reativo:** {reactive_work:.1f}% (bugs + incidentes)\n"
        report += "- 🎯 Equilíbrio saudável entre trabalho planejado e reativo\n"

    report += f"""
![Épicos](./04_epic_totals.png)

---

## Recomendações para o Próximo Quarter

"""

    recommendations = []

    # Recomendações baseadas em throughput
    if cv_improvement < 10:
        recommendations.append("**Estabilizar throughput:** Investigar causas de variabilidade e implementar práticas para tornar entregas mais previsíveis")

    # Recomendações baseadas em lead time
    if p90_overall > 8:
        recommendations.append(f"**Reduzir lead time:** P90 atual de {p90_overall:.0f} dias está acima da meta - identificar e remover gargalos")

    # Recomendações baseadas em qualidade
    if bugs_pct > 15:
        recommendations.append(f"**Melhorar qualidade:** Taxa de bugs de {bugs_pct:.1f}% requer atenção - reforçar testes e code review")

    if incidents_pct > 15:
        recommendations.append(f"**Aumentar estabilidade:** {incidents_pct:.1f}% de incidentes - investir em monitoramento e testes de integração")

    # Se tudo está bem
    if not recommendations:
        recommendations.append("**Manter o ritmo:** Métricas estão saudáveis - continuar com as práticas atuais")
        recommendations.append("**Buscar melhoria contínua:** Identificar pequenas otimizações em processos e ferramentas")

    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"

    report += f"""

---

## Conclusão

O quarter {quarter_name} demonstrou {"**evolução positiva**" if cv_improvement > 0 and p90_overall <= 10 else "**necessidade de melhorias**"} nas métricas de desempenho.
Com {total_tickets} itens entregues, o time {"manteve" if avg_throughput >= 15 else "está desenvolvendo"} uma boa capacidade de entrega.

{"✅ **Continue com as boas práticas e mantenha o foco na melhoria contínua.**" if cv_improvement > 20 and p90_overall <= 8 else "⚠️ **Implemente as recomendações acima para melhorar a performance no próximo quarter.**"}

---

_Relatório gerado automaticamente pela skill analyze-quarter_
"""

    # Salvar relatório
    report_file = output_dir / 'report-quarterly.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print("✓ Relatório consolidado gerado")

def main():
    if len(sys.argv) < 3:
        print("Uso: analyze-quarter [nome-do-time] [YYYY-QN]")
        print("Exemplo: analyze-quarter financeiro 2025-Q4")
        sys.exit(1)

    team_name = sys.argv[1]
    quarter = sys.argv[2]

    # Encontrar diretório base do repositório
    repo_root = Path(__file__).parent.parent.parent.parent
    quarter_dir = repo_root / team_name / quarter

    if not quarter_dir.exists():
        print(f"❌ Erro: Diretório não encontrado: {quarter_dir}")
        sys.exit(1)

    print("=" * 60)
    print(f"Análise Consolidada {quarter} - Time {team_name.title()}")
    print("=" * 60)
    print()

    # Detectar retrospectivas automaticamente
    retros = find_retro_folders(quarter_dir)
    if not retros:
        print(f"❌ Erro: Nenhuma retrospectiva encontrada em {quarter_dir}")
        print("As retrospectivas devem estar em pastas com formato YYYY-MM-DD")
        sys.exit(1)

    print(f"📁 Retrospectivas encontradas: {len(retros)}")
    for retro in retros:
        print(f"   - {retro}")
    print()

    print("Carregando dados...")
    data = load_all_data(quarter_dir, retros)
    print(f"✓ Dados carregados: {len(data['throughput'])} registros de throughput, "
          f"{len(data['tickets'])} tickets")
    print()

    print("Gerando gráficos...")
    print()

    quarter_name = f"{quarter} - {team_name.title()}"

    chart_1_throughput_evolution(data, quarter_dir, quarter_name, retros)
    chart_2_variability_improvement(data, quarter_dir, quarter_name, retros)
    chart_3_leadtime_velocity(data, quarter_dir, quarter_name, retros)
    chart_4_epic_heatmap(data, quarter_dir, quarter_name, retros)

    print()
    print("Gerando relatório consolidado...")
    generate_quarterly_report(data, quarter_dir, quarter_name, retros)

    print()
    print("=" * 60)
    print(f"✅ Análise completa! Arquivos salvos em:")
    print(f"   {quarter_dir}")
    print("   - 4 gráficos PNG")
    print("   - report-quarterly.md")
    print("=" * 60)

if __name__ == '__main__':
    main()
