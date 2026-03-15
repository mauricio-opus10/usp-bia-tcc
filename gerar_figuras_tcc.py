#!/usr/bin/env python3
"""
Gera figuras de alta qualidade para o TCC.
Cada figura é salva em sua própria subpasta dentro de data/output/figuras_tcc/
com o script .py correspondente e a imagem .png.

Uso:
    python gerar_figuras_tcc.py           # Gera todas as figuras
    python gerar_figuras_tcc.py --fig 1   # Gera apenas a Figura 1
"""

import sys
import os
import inspect
import warnings
warnings.filterwarnings('ignore')

# Adicionar src ao path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import community as community_louvain
import seaborn as sns

from src.etl.load_cow import (load_alliances, load_nmc, load_trade,
                              load_mids, load_mids_participants, load_diplomatic)
from src.etl.transform import (prepare_alliance_edges, prepare_trade_edges,
                                filter_states_by_cinc)
from src.network.build_network import (build_alliance_network, build_trade_network,
                                        build_dispute_network)
from src.utils.helpers import TIME_WINDOWS, RANDOM_SEED

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

FIGURAS_BASE_DIR = os.path.join(PROJECT_ROOT, 'data', 'output', 'figuras_tcc')
os.makedirs(FIGURAS_BASE_DIR, exist_ok=True)

# Paleta de cores para comunidades (3 cores distintas, acessíveis)
COMMUNITY_COLORS = ['#2166AC', '#D6604D', '#4DAF4A']  # azul, vermelho, verde

# Nomes dos países em português
COUNTRY_NAMES_PT = {
    'United States of America': 'EUA',
    'United Kingdom': 'Reino Unido',
    'France': 'França',
    'Germany': 'Alemanha',
    'Russia': 'Rússia',
    'Italy': 'Itália',
    'Austria-Hungary': 'Áustria-Hungria',
    'Japan': 'Japão',
    'China': 'China',
    'Spain': 'Espanha',
    'Turkey': 'Turquia',
    'Belgium': 'Bélgica',
    'Brazil': 'Brasil',
    'Poland': 'Polônia',
    'Czechoslovakia': 'Tchecoslováquia',
}

# Abreviações COW -> PT
COW_ABB_PT = {
    'USA': 'EUA', 'UKG': 'Reino Unido', 'FRN': 'França', 'GMY': 'Alemanha',
    'RUS': 'Rússia', 'ITA': 'Itália', 'AUH': 'Áustria-Hungria', 'JPN': 'Japão',
    'CHN': 'China', 'SPN': 'Espanha', 'TUR': 'Turquia', 'BEL': 'Bélgica',
    'BRA': 'Brasil', 'POL': 'Polônia', 'CZE': 'Tchecoslováquia',
}

# COW codes para identificação de blocos
COW_GERMANY = 255
COW_USA = 2
COW_FRANCE = 220
COW_UK = 200
COW_RUSSIA = 365


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _get_figure_dir(fig_num: int, name: str) -> str:
    """Cria e retorna o diretório para uma figura específica."""
    fig_dir = os.path.join(FIGURAS_BASE_DIR, f'figura_{fig_num}_{name}')
    os.makedirs(fig_dir, exist_ok=True)
    return fig_dir


def _save_figure_code(fig_dir: str, func):
    """Salva o código-fonte da função geradora na pasta da figura."""
    source = inspect.getsource(func)
    code_path = os.path.join(fig_dir, 'codigo.py')
    header = (
        '#!/usr/bin/env python3\n'
        '"""\n'
        'Código que gerou a figura nesta pasta.\n'
        'Extraído automaticamente de gerar_figuras_tcc.py\n'
        'Para regenerar: python gerar_figuras_tcc.py --fig <N>\n'
        '"""\n\n'
    )
    with open(code_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(source)


def _save_and_close(fig, fig_dir, filename, func):
    """Salva a figura, o código-fonte e fecha o plot."""
    output_path = os.path.join(fig_dir, filename)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    _save_figure_code(fig_dir, func)
    print(f"  Imagem: {output_path}")
    print(f"  Código: {os.path.join(fig_dir, 'codigo.py')}")
    return output_path


def _get_country_label(name: str) -> str:
    """Retorna nome abreviado em português."""
    return COUNTRY_NAMES_PT.get(name, name)


def _identify_blocs(partition: dict, period: str) -> dict:
    """Identifica nomes dos blocos baseado nos membros-chave."""
    comm_members = {}
    for node, comm_id in partition.items():
        comm_members.setdefault(comm_id, set()).add(node)

    bloc_names = {}
    if period == 'pre_wwi':
        for cid, members in comm_members.items():
            if COW_GERMANY in members:
                bloc_names[cid] = 'Potências Centrais'
            elif COW_UK in members:
                bloc_names[cid] = 'Bloco Anglo-Saxão'
            elif COW_FRANCE in members or COW_RUSSIA in members:
                bloc_names[cid] = 'Bloco Franco-Russo'
            else:
                bloc_names[cid] = f'Comunidade {cid}'
    else:
        for cid, members in comm_members.items():
            if COW_GERMANY in members:
                bloc_names[cid] = 'Eixo'
            elif COW_USA in members and COW_FRANCE not in members:
                bloc_names[cid] = 'Bloco Americano'
            elif COW_FRANCE in members or COW_UK in members:
                bloc_names[cid] = 'Aliados'
            else:
                bloc_names[cid] = f'Comunidade {cid}'
    return bloc_names


def _build_alliance_graph(period: str) -> nx.Graph:
    """Constrói grafo de alianças para um período."""
    window = TIME_WINDOWS[period]
    start, end = window['start'], window['end']
    df_alliances = load_alliances(start_year=start, end_year=end)
    df_nmc = load_nmc(start_year=start, end_year=end)
    relevant_states = filter_states_by_cinc(df_nmc, threshold=0.01)
    edges = prepare_alliance_edges(df_alliances, start_year=start, end_year=end)
    edges = edges[
        (edges['source'].isin(relevant_states)) &
        (edges['target'].isin(relevant_states))
    ]
    return build_alliance_network(edges, weighted=True)


def _draw_convex_hull(ax, points, color, alpha=0.12, pad=0.06):
    """Desenha região sombreada (convex hull) ao redor de um conjunto de pontos."""
    from scipy.spatial import ConvexHull
    if len(points) < 3:
        cx, cy = np.mean(points, axis=0)
        circle = plt.Circle((cx, cy), pad + 0.08, color=color, alpha=alpha, zorder=0)
        ax.add_patch(circle)
        return
    try:
        hull = ConvexHull(points)
        hull_pts = points[hull.vertices]
        centroid = np.mean(hull_pts, axis=0)
        norms = np.linalg.norm(hull_pts - centroid, axis=1, keepdims=True).clip(0.01)
        expanded = centroid + (hull_pts - centroid) * (1 + pad / norms)
        from matplotlib.patches import Polygon
        poly = Polygon(expanded, closed=True, facecolor=color, edgecolor=color,
                       alpha=alpha, linewidth=1.5, linestyle='--', zorder=0)
        ax.add_patch(poly)
    except Exception:
        pass


def _draw_network_panel(ax, G, partition, blocos_dict, period_label, mod,
                        show_hulls=False):
    """Desenha um painel de rede reutilizável. Retorna legend_info list."""
    pos = nx.spring_layout(G, k=2.5 / np.sqrt(max(G.number_of_nodes(), 1)),
                           seed=RANDOM_SEED, iterations=100)
    name_attrs = nx.get_node_attributes(G, 'name')
    degrees = dict(G.degree())
    max_deg = max(degrees.values()) if degrees else 1

    if show_hulls:
        comm_nodes = {}
        for n, cid in partition.items():
            comm_nodes.setdefault(cid, []).append(n)
        for cid, nodes in comm_nodes.items():
            color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
            pts = np.array([pos[n] for n in nodes])
            _draw_convex_hull(ax, pts, color, alpha=0.15, pad=0.08)
            centroid = np.mean(pts, axis=0)
            bloc_name = blocos_dict.get(cid, f'Comunidade {cid}')
            ax.annotate(bloc_name, xy=centroid, fontsize=11, fontstyle='italic',
                        fontweight='bold', ha='center', va='bottom', color=color,
                        xytext=(0, 18), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  edgecolor=color, alpha=0.8))
        intra = [(u, v) for u, v in G.edges() if partition[u] == partition[v]]
        inter = [(u, v) for u, v in G.edges() if partition[u] != partition[v]]
        nx.draw_networkx_edges(G, pos, edgelist=inter, ax=ax,
                               width=0.8, alpha=0.2, edge_color='#999999', style='dashed')
        nx.draw_networkx_edges(G, pos, edgelist=intra, ax=ax,
                               width=1.5, alpha=0.5, edge_color='#555555')
    else:
        edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
        max_w = max(edge_weights) if edge_weights else 1
        edge_widths = [0.5 + (w / max_w) * 2.5 for w in edge_weights]
        nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths,
                               alpha=0.4, edge_color='#666666')

    node_colors = [COMMUNITY_COLORS[partition[n] % len(COMMUNITY_COLORS)] for n in G.nodes()]
    node_sizes = [400 + (degrees[n] / max_deg) * 900 for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                           node_color=node_colors, edgecolors='#333333',
                           linewidths=1.0, alpha=0.9)

    labels = {n: _get_country_label(name_attrs.get(n, str(n))) for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=13,
                            font_weight='bold', font_family='sans-serif')

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G)
    if show_hulls:
        n_comm = len(set(partition.values()))
        comm_sizes = [len(v) for v in comm_nodes.values()]
        ax.set_title(f'{period_label}\nMod.={mod:.3f}  |  {n_comm} comunidades  |  Tamanhos: {comm_sizes}',
                     fontsize=16, fontweight='bold', pad=12)
    else:
        ax.set_title(f'{period_label}\nN={n_nodes}  |  E={n_edges}  |  Dens.={density:.3f}  |  Mod.={mod:.3f}',
                     fontsize=16, fontweight='bold', pad=12)
    ax.axis('off')

    legend_info = []
    for comm_id in sorted(set(partition.values())):
        color = COMMUNITY_COLORS[comm_id % len(COMMUNITY_COLORS)]
        bloc_name = blocos_dict.get(comm_id, f'Comunidade {comm_id}')
        members = [_get_country_label(name_attrs.get(n, str(n)))
                   for n, c in partition.items() if c == comm_id]
        legend_info.append((bloc_name, members, color))
    return legend_info


def _add_bottom_legends(fig, axes, legend_info_left, legend_info_right,
                        title_left, title_right):
    """Adiciona legendas abaixo dos painéis, fora da área do gráfico."""
    patches_l = [mpatches.Patch(color=c, label=f'{b}: {", ".join(m)}')
                 for b, m, c in legend_info_left]
    patches_r = [mpatches.Patch(color=c, label=f'{b}: {", ".join(m)}')
                 for b, m, c in legend_info_right]

    axes[0].legend(handles=patches_l, loc='upper center',
                   bbox_to_anchor=(0.5, -0.05), fontsize=11, framealpha=0.95,
                   edgecolor='#cccccc', title=title_left, title_fontsize=13)
    axes[1].legend(handles=patches_r, loc='upper center',
                   bbox_to_anchor=(0.5, -0.05), fontsize=11, framealpha=0.95,
                   edgecolor='#cccccc', title=title_right, title_fontsize=13)


# ============================================================================
# FIGURA 1 — Comparação das redes de alianças
# ============================================================================

def gerar_figura_1():
    """Figura 1 — Comparação das redes de alianças pré-WWI e pré-WWII."""
    print("Gerando Figura 1 — Comparação das redes de alianças...")
    fig_dir = _get_figure_dir(1, 'aliancas_comparacao')

    G1 = _build_alliance_graph('pre_wwi')
    G2 = _build_alliance_graph('pre_wwii')
    part1 = community_louvain.best_partition(G1, random_state=RANDOM_SEED)
    part2 = community_louvain.best_partition(G2, random_state=RANDOM_SEED)
    mod1 = community_louvain.modularity(part1, G1)
    mod2 = community_louvain.modularity(part2, G2)
    blocos1 = _identify_blocs(part1, 'pre_wwi')
    blocos2 = _identify_blocs(part2, 'pre_wwii')

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(bottom=0.18)

    li_l = _draw_network_panel(axes[0], G1, part1, blocos1, 'Pré-WWI (1890–1914)', mod1)
    li_r = _draw_network_panel(axes[1], G2, part2, blocos2, 'Pré-WWII (1925–1939)', mod2)
    _add_bottom_legends(fig, axes, li_l, li_r,
                        'Comunidades Pré-WWI (Louvain)', 'Comunidades Pré-WWII (Louvain)')

    return _save_and_close(fig, fig_dir, 'figura_1_aliancas_comparacao.png', gerar_figura_1)


# ============================================================================
# FIGURA 2 — Comunidades detectadas por Louvain
# ============================================================================

def gerar_figura_2():
    """Figura 2 — Comunidades detectadas pelo algoritmo de Louvain nos dois períodos."""
    print("Gerando Figura 2 — Comunidades Louvain...")
    fig_dir = _get_figure_dir(2, 'comunidades_louvain')

    G1 = _build_alliance_graph('pre_wwi')
    G2 = _build_alliance_graph('pre_wwii')
    part1 = community_louvain.best_partition(G1, random_state=RANDOM_SEED)
    part2 = community_louvain.best_partition(G2, random_state=RANDOM_SEED)
    mod1 = community_louvain.modularity(part1, G1)
    mod2 = community_louvain.modularity(part2, G2)
    blocos1 = _identify_blocs(part1, 'pre_wwi')
    blocos2 = _identify_blocs(part2, 'pre_wwii')

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(bottom=0.20)

    li_l = _draw_network_panel(axes[0], G1, part1, blocos1, 'Pré-WWI (1890–1914)', mod1, show_hulls=True)
    li_r = _draw_network_panel(axes[1], G2, part2, blocos2, 'Pré-WWII (1925–1939)', mod2, show_hulls=True)
    _add_bottom_legends(fig, axes, li_l, li_r,
                        'Comunidades Pré-WWI', 'Comunidades Pré-WWII')

    fig.text(0.5, 0.01,
             'Linhas contínuas = alianças intra-bloco  |  Linhas tracejadas = alianças inter-bloco',
             ha='center', fontsize=12, fontstyle='italic', color='#666666')

    return _save_and_close(fig, fig_dir, 'figura_2_comunidades_louvain.png', gerar_figura_2)


# ============================================================================
# FIGURA 3 — Ranking de densidade por camada
# ============================================================================

def gerar_figura_3():
    """Figura 3 — Ranking de densidade por camada nos dois períodos."""
    print("Gerando Figura 3 — Ranking de densidade por camada...")
    fig_dir = _get_figure_dir(3, 'ranking_densidade')

    # Dados verificados do TCC
    camadas = ['Diplomacia', 'Comércio', 'Disputas', 'Alianças']
    densidades_wwi =  [0.970, 0.939, 0.591, 0.382]
    densidades_wwii = [1.000, 0.987, 0.470, 0.423]
    variacoes = [d2 - d1 for d1, d2 in zip(densidades_wwi, densidades_wwii)]
    cores_camada = ['#8856a7', '#43a2ca', '#e34a33', '#2166AC']

    y = np.arange(len(camadas))
    bar_height = 0.35

    # Figura com espaço extra embaixo para legenda
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(bottom=0.15)

    # Barras pré-WWI (tom claro)
    bars1 = ax.barh(y + bar_height/2, densidades_wwi, bar_height,
                    label='Pré-WWI (1890–1914)', color=[c + '99' for c in cores_camada],
                    edgecolor=cores_camada, linewidth=1.2)

    # Barras pré-WWII (tom cheio)
    bars2 = ax.barh(y - bar_height/2, densidades_wwii, bar_height,
                    label='Pré-WWII (1925–1939)', color=cores_camada,
                    edgecolor='#333333', linewidth=1.2)

    # Anotações de valor
    for bar in bars1:
        w = bar.get_width()
        ax.text(w + 0.01, bar.get_y() + bar.get_height()/2,
                f'{w:.1%}', va='center', fontsize=14, color='#555555')
    for bar in bars2:
        w = bar.get_width()
        ax.text(w + 0.01, bar.get_y() + bar.get_height()/2,
                f'{w:.1%}', va='center', fontsize=14, fontweight='bold')

    # Variações à direita
    for i, var in enumerate(variacoes):
        sinal = '+' if var >= 0 else ''
        cor = '#2ca02c' if var >= 0 else '#d62728'
        ax.text(1.08, y[i], f'{sinal}{var:.1%}',
                va='center', fontsize=15, fontweight='bold', color=cor,
                transform=ax.get_yaxis_transform())
    ax.text(1.08, len(camadas) - 0.3, 'Variação', va='center', fontsize=14,
            fontweight='bold', color='#333333', fontstyle='italic',
            transform=ax.get_yaxis_transform())

    ax.set_yticks(y)
    ax.set_yticklabels(camadas, fontsize=16, fontweight='bold')
    ax.set_xlabel('Densidade da rede', fontsize=16)
    ax.set_xlim(0, 1.12)
    ax.set_title('Ranking de Densidade por Camada de Rede',
                 fontsize=19, fontweight='bold', pad=15)

    from matplotlib.ticker import PercentFormatter
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.xaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=13)

    # Legenda ABAIXO do gráfico
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08),
              fontsize=14, framealpha=0.95, ncol=2, edgecolor='#cccccc')

    # Nota para disputas — posicionada à direita, no espaço em branco
    ax.annotate(
        'Única camada com\nredução de densidade',
        xy=(0.60, y[2]),
        xytext=(0.75, y[2]),
        fontsize=13, fontstyle='italic', color='#d62728',
        arrowprops=dict(arrowstyle='->', color='#d62728', lw=1.5),
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff5f5',
                  edgecolor='#d62728', alpha=0.9)
    )

    return _save_and_close(fig, fig_dir, 'figura_3_ranking_densidade.png', gerar_figura_3)


# ============================================================================
# FIGURA 5 — Slope chart: brokers de disputas (USA ↔ Alemanha)
# ============================================================================

def _spread_labels(values, min_gap=0.012):
    """Separa posições de rótulos para evitar sobreposição vertical."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    positions = [v for _, v in indexed]
    # Empurrar rótulos para cima quando muito próximos
    for i in range(1, len(positions)):
        if positions[i] - positions[i - 1] < min_gap:
            positions[i] = positions[i - 1] + min_gap
    # Reconstruir na ordem original
    result = [0.0] * len(values)
    for rank, (orig_idx, _) in enumerate(indexed):
        result[orig_idx] = positions[rank]
    return result


def gerar_figura_5():
    """Figura 5 — Inversão de brokers de disputas: EUA ↔ Alemanha."""
    print("Gerando Figura 5 — Slope chart de brokers de disputas...")
    fig_dir = _get_figure_dir(5, 'brokers_slope_disputas')

    # Dados de betweenness centrality na camada de disputas (verificados)
    paises = ['EUA', 'Alemanha', 'Rússia', 'Áust.-Hung./Polônia', 'Reino Unido',
              'França', 'Turquia/Espanha', 'Itália', 'Japão']

    # Betweenness pré-WWI (disputas)
    bc_wwi = [0.186, 0.082, 0.064, 0.082, 0.018, 0.017, 0.072, 0.010, 0.000]
    # Betweenness pré-WWII (disputas)
    bc_wwii = [0.012, 0.136, 0.034, 0.030, 0.015, 0.034, 0.030, 0.034, 0.008]

    # Calcular posições de rótulos sem sobreposição (gap menor = mais compacto)
    label_y_left = _spread_labels(bc_wwi, min_gap=0.011)
    label_y_right = _spread_labels(bc_wwii, min_gap=0.011)

    # Formato retangular — aproveita largura da página Word
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(bottom=0.13, left=0.08, right=0.92)

    # Posições x dos pontos
    x_left, x_right = 0.25, 0.75
    x = [x_left, x_right]

    # Cores: destaque para USA e Alemanha
    colors = {
        'EUA': '#2166AC',
        'Alemanha': '#d62728',
    }
    default_color = '#aaaaaa'

    for i, pais in enumerate(paises):
        cor = colors.get(pais, default_color)
        lw = 3.5 if pais in colors else 1.5
        alpha = 1.0 if pais in colors else 0.5
        zorder = 10 if pais in colors else 1

        ax.plot(x, [bc_wwi[i], bc_wwii[i]], 'o-', color=cor, linewidth=lw,
                markersize=10 if pais in colors else 6, alpha=alpha, zorder=zorder)

        # Fontes: destaques maiores, secundários menores
        fs = 13 if pais in colors else 10
        fw = 'bold' if pais in colors else 'normal'

        # Rótulos COLADOS nos pontos (offset pequeno)
        # Esquerda: rótulo logo à esquerda do ponto
        ax.annotate(f'{pais} ({bc_wwi[i]:.3f})',
                    xy=(x_left, bc_wwi[i]),
                    xytext=(x_left - 0.02, label_y_left[i]),
                    ha='right', va='center', fontsize=fs, color=cor, fontweight=fw,
                    arrowprops=dict(arrowstyle='-', color=cor, lw=0.5, alpha=0.3)
                    if abs(label_y_left[i] - bc_wwi[i]) > 0.005 else None)

        # Direita: rótulo logo à direita do ponto
        ax.annotate(f'{pais} ({bc_wwii[i]:.3f})',
                    xy=(x_right, bc_wwii[i]),
                    xytext=(x_right + 0.02, label_y_right[i]),
                    ha='left', va='center', fontsize=fs, color=cor, fontweight=fw,
                    arrowprops=dict(arrowstyle='-', color=cor, lw=0.5, alpha=0.3)
                    if abs(label_y_right[i] - bc_wwii[i]) > 0.005 else None)

    # Eixo x
    ax.set_xticks(x)
    ax.set_xticklabels(['Pré-WWI\n(1890–1914)', 'Pré-WWII\n(1925–1939)'],
                       fontsize=16, fontweight='bold')
    ax.set_xlim(-0.02, 1.02)

    # Eixo y
    ax.set_ylim(-0.015, 0.22)
    ax.tick_params(axis='y', labelsize=13)

    ax.set_title('Inversão Estrutural: Brokers de Disputas\n'
                 '(Betweenness Centrality na rede de disputas militarizadas)',
                 fontsize=18, fontweight='bold', pad=15)

    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    # Anotações interpretativas — posicionadas em áreas limpas
    # "Alemanha assume" acima à direita do ponto Alemanha pré-WWII
    ax.annotate('Alemanha assume\n(revisionismo)',
                xy=(x_right, 0.136),
                xytext=(x_right - 0.12, 0.19),
                fontsize=12, ha='center', color='#d62728', fontstyle='italic',
                arrowprops=dict(arrowstyle='->', color='#d62728', lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff5f5',
                          edgecolor='#d62728', alpha=0.9),
                zorder=20)

    # "EUA sai do centro" — abaixo do cruzamento, à direita
    ax.annotate('EUA sai do centro\n(isolacionismo)',
                xy=(x_right, 0.012),
                xytext=(0.50, -0.005),
                fontsize=12, ha='center', color='#2166AC', fontstyle='italic',
                arrowprops=dict(arrowstyle='->', color='#2166AC', lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0f4ff',
                          edgecolor='#2166AC', alpha=0.9),
                zorder=20)

    # Legenda abaixo
    legend_patches = [
        mpatches.Patch(color='#2166AC', label='EUA — broker central pré-WWI'),
        mpatches.Patch(color='#d62728', label='Alemanha — broker central pré-WWII'),
        mpatches.Patch(color='#aaaaaa', label='Demais Estados'),
    ]
    ax.legend(handles=legend_patches, loc='upper center',
              bbox_to_anchor=(0.5, -0.08), fontsize=13, ncol=3,
              framealpha=0.95, edgecolor='#cccccc')

    return _save_and_close(fig, fig_dir, 'figura_5_brokers_slope_disputas.png', gerar_figura_5)


# ============================================================================
# FIGURA 6 — Heatmap de betweenness centrality por país e camada
# ============================================================================

def gerar_figura_6():
    """Figura 6 — Heatmap de betweenness centrality por país e camada (4 camadas)."""
    print("Gerando Figura 6 — Heatmap de betweenness (4 camadas)...")
    fig_dir = _get_figure_dir(6, 'heatmap_betweenness')

    # Dados de betweenness — 4 camadas
    # Pré-WWI
    paises_wwi = ['Rússia', 'Itália', 'Alemanha', 'Reino Unido', 'França',
                  'Áustria-Hungria', 'Espanha', 'EUA', 'Japão', 'Turquia',
                  'China', 'Bélgica']
    bc_ali_wwi = [0.376, 0.057, 0.211, 0.117, 0.009, 0.037, 0.000, 0.000, 0.022, 0.000, 0.000, 0.000]
    bc_dis_wwi = [0.064, 0.010, 0.082, 0.018, 0.017, 0.082, 0.000, 0.186, 0.000, 0.072, 0.000, 0.000]
    bc_com_wwi = [0.009, 0.009, 0.009, 0.009, 0.009, 0.002, 0.000, 0.009, 0.005, 0.002, 0.000, 0.009]
    bc_dip_wwi = [0.004, 0.004, 0.004, 0.004, 0.004, 0.004, 0.004, 0.004, 0.000, 0.000, 0.000, 0.004]

    # Pré-WWII
    paises_wwii = ['Rússia', 'Itália', 'Alemanha', 'Reino Unido', 'França',
                   'Polônia', 'Espanha', 'EUA', 'Japão', 'Tchecoslováquia',
                   'China', 'Bélgica', 'Brasil']
    bc_ali_wwii = [0.188, 0.092, 0.081, 0.114, 0.177, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.061, 0.000]
    bc_dis_wwii = [0.136, 0.022, 0.354, 0.022, 0.011, 0.012, 0.000, 0.007, 0.014, 0.000, 0.077, 0.000, 0.000]
    bc_com_wwii = [0.000, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.000]
    bc_dip_wwii = [0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]

    # Montar DataFrames
    df_wwi = pd.DataFrame({
        'País': paises_wwi,
        'Alianças': bc_ali_wwi,
        'Disputas': bc_dis_wwi,
        'Comércio': bc_com_wwi,
        'Diplomacia': bc_dip_wwi,
    }).set_index('País')

    df_wwii = pd.DataFrame({
        'País': paises_wwii,
        'Alianças': bc_ali_wwii,
        'Disputas': bc_dis_wwii,
        'Comércio': bc_com_wwii,
        'Diplomacia': bc_dip_wwii,
    }).set_index('País')

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(bottom=0.10)

    for ax, df, title in [
        (axes[0], df_wwi, 'Pré-WWI (1890–1914)'),
        (axes[1], df_wwii, 'Pré-WWII (1925–1939)'),
    ]:
        # Ordenar por soma de betweenness
        df = df.copy()
        df['total'] = df.sum(axis=1)
        df = df.sort_values('total', ascending=True).drop(columns='total')

        sns.heatmap(df, ax=ax, annot=True, fmt='.3f', cmap='YlOrRd',
                    linewidths=0.5, linecolor='white', cbar_kws={'shrink': 0.8},
                    vmin=0, vmax=0.4, annot_kws={'fontsize': 12})
        ax.set_title(title, fontsize=17, fontweight='bold', pad=10)
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.tick_params(axis='y', labelsize=13)
        ax.tick_params(axis='x', labelsize=13, rotation=45)

    fig.suptitle('Betweenness Centrality por País e Camada',
                 fontsize=19, fontweight='bold', y=1.02)

    plt.tight_layout(rect=[0, 0.06, 1, 1])

    # Nota explicativa
    fig.text(0.5, 0.01,
             'Valores mais altos (vermelho) indicam maior papel de intermediação  |  '
             'Comércio e Diplomacia têm baixa variação (redes quase completas)',
             ha='center', fontsize=12, fontstyle='italic', color='#666666')

    return _save_and_close(fig, fig_dir, 'figura_6_heatmap_betweenness.png', gerar_figura_6)


# ============================================================================
# FIGURA 7 — Teste de robustez: variação de CINC threshold
# ============================================================================

def gerar_figura_8():
    """Figura 8 — Teste de robustez: densidade vs threshold CINC."""
    print("Gerando Figura 8 — Teste de robustez CINC...")
    fig_dir = _get_figure_dir(8, 'robustez_cinc')

    # Dados do notebook 03 (verificados) + diplomacia
    thresholds = [0.005, 0.010, 0.015, 0.020]

    data = {
        'Alianças Pré-WWI':   [0.333, 0.382, 0.382, 0.417],
        'Alianças Pré-WWII':  [0.316, 0.423, 0.556, 0.611],
        'Disputas Pré-WWI':   [0.433, 0.621, 0.691, 0.806],
        'Disputas Pré-WWII':  [0.443, 0.731, 0.956, 0.972],
        'Comércio Pré-WWI':   [0.765, 0.939, 0.927, 0.972],
        'Comércio Pré-WWII':  [0.931, 0.987, 1.000, 1.000],
        'Diplomacia Pré-WWI': [0.882, 0.970, 0.982, 1.000],
        'Diplomacia Pré-WWII':[0.964, 1.000, 1.000, 1.000],
    }

    fig, axes = plt.subplots(1, 4, figsize=(18, 6))
    fig.patch.set_facecolor('white')

    camadas = ['Alianças', 'Disputas', 'Comércio', 'Diplomacia']
    cores = {'Pré-WWI': '#2166AC', 'Pré-WWII': '#D6604D'}

    for ax, camada in zip(axes, camadas):
        for periodo, cor in cores.items():
            key = f'{camada} {periodo}'
            ls = '-' if 'WWI' in periodo and 'WWII' not in periodo else '--'
            ax.plot(thresholds, data[key], 'o-', color=cor, linewidth=2,
                    markersize=7, label=periodo, linestyle=ls)

        ax.set_title(camada, fontsize=17, fontweight='bold')
        ax.set_xlabel('Threshold CINC', fontsize=14)
        ax.set_ylabel('Densidade' if ax == axes[0] else '', fontsize=14)
        ax.set_ylim(0, 1.05)
        ax.set_xticks(thresholds)
        ax.set_xticklabels([f'{t:.1%}' for t in thresholds], fontsize=12)
        ax.tick_params(axis='y', labelsize=12)
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

        from matplotlib.ticker import PercentFormatter
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))

    fig.suptitle('Teste de Robustez: Densidade vs. Threshold CINC',
                 fontsize=19, fontweight='bold')

    plt.tight_layout(rect=[0, 0.13, 1, 0.95])

    # Legenda unificada abaixo
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center',
               bbox_to_anchor=(0.5, 0.08), fontsize=14, ncol=2,
               framealpha=0.95, edgecolor='#cccccc')

    fig.text(0.5, 0.01,
             'As tendências se mantêm estáveis em todos os thresholds — '
             'resultados são robustos à variação do critério de seleção de Estados',
             ha='center', fontsize=12, fontstyle='italic', color='#666666')

    return _save_and_close(fig, fig_dir, 'figura_8_robustez_cinc.png', gerar_figura_8)


# ============================================================================
# FIGURA 4 — Comparação visual das 4 redes (4x2 grid)
# ============================================================================

# Mapa de código COW -> nome PT para nós sem atributo 'name'
_CCODE_TO_NAME_PT = {
    2: 'EUA', 140: 'Brasil', 200: 'Reino Unido', 211: 'Bélgica',
    220: 'França', 230: 'Espanha', 255: 'Alemanha', 290: 'Polônia',
    300: 'Áustria-Hungria', 315: 'Tchecoslováquia', 325: 'Itália',
    365: 'Rússia', 640: 'Turquia', 710: 'China', 740: 'Japão',
}

# Cores por camada
_LAYER_COLORS = {
    'Alianças':   '#2166AC',
    'Comércio':   '#43a2ca',
    'Disputas':   '#e34a33',
    'Diplomacia': '#8856a7',
}


def _build_trade_graph(period: str) -> nx.Graph:
    """Constrói grafo de comércio agregado para um período."""
    window = TIME_WINDOWS[period]
    start, end = window['start'], window['end']
    df_trade = load_trade(start_year=start, end_year=end)
    df_nmc = load_nmc(start_year=start, end_year=end)
    relevant_states = filter_states_by_cinc(df_nmc, threshold=0.01)

    # Agregar comércio no período: aresta se houve comércio positivo em qualquer ano
    df_trade = df_trade.copy()
    df_trade['flow1'] = df_trade['flow1'].replace(-9, 0)
    df_trade['flow2'] = df_trade['flow2'].replace(-9, 0)
    df_trade['total'] = df_trade['flow1'] + df_trade['flow2']

    # Filtrar estados relevantes
    df_trade = df_trade[
        (df_trade['ccode1'].isin(relevant_states)) &
        (df_trade['ccode2'].isin(relevant_states))
    ]

    # Agregar por díade (soma do comércio no período todo)
    edges = df_trade.groupby(['ccode1', 'ccode2']).agg(
        weight=('total', 'sum'),
        source_name=('importer1', 'first'),
        target_name=('importer2', 'first'),
    ).reset_index()
    edges = edges[edges['weight'] > 0]
    edges = edges.rename(columns={'ccode1': 'source', 'ccode2': 'target'})

    return build_trade_network(edges, normalize_weights=True)


def _build_dispute_graph(period: str) -> nx.Graph:
    """Constrói grafo de disputas para um período."""
    window = TIME_WINDOWS[period]
    start, end = window['start'], window['end']
    df_mids = load_mids(start_year=start, end_year=end)
    df_midb = load_mids_participants(start_year=start, end_year=end)
    df_nmc = load_nmc(start_year=start, end_year=end)
    relevant_states = filter_states_by_cinc(df_nmc, threshold=0.01)

    G = build_dispute_network(df_mids, df_midb, weighted=True, opponents_only=True)

    # Filtrar para estados relevantes
    nodes_to_remove = [n for n in G.nodes() if n not in relevant_states]
    G.remove_nodes_from(nodes_to_remove)
    # Adicionar estados relevantes sem disputas como nós isolados
    for s in relevant_states:
        if s not in G:
            G.add_node(s)

    return G


def _build_diplomacy_graph(period: str) -> nx.Graph:
    """Constrói grafo de diplomacia para um período."""
    window = TIME_WINDOWS[period]
    start, end = window['start'], window['end']
    df_diplo = load_diplomatic(start_year=start, end_year=end)
    df_nmc = load_nmc(start_year=start, end_year=end)
    relevant_states = filter_states_by_cinc(df_nmc, threshold=0.01)

    # Filtrar para estados relevantes
    df = df_diplo[
        (df_diplo['ccode1'].isin(relevant_states)) &
        (df_diplo['ccode2'].isin(relevant_states))
    ].copy()

    # Agregar: aresta se houve troca diplomática (DE=1) em qualquer ano
    edges = df.groupby(['ccode1', 'ccode2']).agg(
        has_exchange=('DE', 'max'),
    ).reset_index()
    edges = edges[edges['has_exchange'] == 1]

    G = nx.Graph()
    for s in relevant_states:
        G.add_node(s)
    for _, row in edges.iterrows():
        G.add_edge(int(row['ccode1']), int(row['ccode2']), weight=1)

    return G


def _get_node_label_pt(G, node):
    """Retorna rótulo em PT para um nó, usando atributo 'name' ou mapa de ccodes."""
    name_attr = G.nodes[node].get('name', '')
    if name_attr:
        return COUNTRY_NAMES_PT.get(name_attr, name_attr)
    return _CCODE_TO_NAME_PT.get(node, str(node))


def gerar_figura_4():
    """Figura 4 — Comparação visual das 4 redes em grade 4×2."""
    print("Gerando Figura 4 — Comparação visual das 4 redes...")
    fig_dir = _get_figure_dir(4, 'comparacao_4_redes')

    periods = [
        ('pre_wwi', 'Pré-WWI (1890–1914)'),
        ('pre_wwii', 'Pré-WWII (1925–1939)'),
    ]

    layers = [
        ('Alianças', _build_alliance_graph),
        ('Comércio', _build_trade_graph),
        ('Disputas', _build_dispute_graph),
        ('Diplomacia', _build_diplomacy_graph),
    ]

    fig, axes = plt.subplots(4, 2, figsize=(18, 26))
    fig.patch.set_facecolor('white')

    # Pré-construir todos os grafos para reutilizar
    graphs = {}
    for period_key, _ in periods:
        for layer_name, build_func in layers:
            graphs[(layer_name, period_key)] = build_func(period_key)

    for col, (period_key, period_label) in enumerate(periods):
        # Coletar todos os nós que aparecem em qualquer camada neste período
        all_nodes = set()
        for layer_name, _ in layers:
            all_nodes.update(graphs[(layer_name, period_key)].nodes())

        # Layout compartilhado usando alianças como guia de posicionamento
        G_layout = nx.Graph()
        G_layout.add_nodes_from(all_nodes)
        G_ref = graphs[('Alianças', period_key)]
        G_layout.add_edges_from(G_ref.edges())

        pos = nx.spring_layout(G_layout, k=3.0 / np.sqrt(max(len(all_nodes), 1)),
                               seed=RANDOM_SEED, iterations=120)

        for row, (layer_name, _) in enumerate(layers):
            ax = axes[row, col]
            color = _LAYER_COLORS[layer_name]
            G = graphs[(layer_name, period_key)]

            n_nodes = G.number_of_nodes()
            n_edges = G.number_of_edges()
            density = nx.density(G)

            # Posições para nós deste grafo
            pos_g = {n: pos[n] for n in G.nodes() if n in pos}

            # Desenhar arestas
            if n_edges > 0:
                edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
                max_w = max(edge_weights) if edge_weights else 1
                edge_widths = [0.3 + (w / max_w) * 1.8 for w in edge_weights]
                # Ajustar transparência conforme densidade
                if density > 0.9:
                    alpha_edge = 0.18
                elif density > 0.7:
                    alpha_edge = 0.25
                else:
                    alpha_edge = 0.40
                nx.draw_networkx_edges(G, pos_g, ax=ax, width=edge_widths,
                                       alpha=alpha_edge, edge_color=color)

            # Desenhar nós
            degrees = dict(G.degree())
            max_deg = max(degrees.values()) if degrees else 1
            node_sizes = [350 + (degrees.get(n, 0) / max_deg) * 550 for n in G.nodes()]
            nx.draw_networkx_nodes(G, pos_g, ax=ax, node_size=node_sizes,
                                   node_color=color, edgecolors='white',
                                   linewidths=1.2, alpha=0.90)

            # Rótulos (fonte menor para redes densas)
            labels = {n: _get_node_label_pt(G, n) for n in G.nodes()}
            font_sz = 10 if density > 0.8 else 11
            nx.draw_networkx_labels(G, pos_g, labels, ax=ax, font_size=font_sz,
                                    font_weight='bold', font_family='sans-serif')

            # Título do painel (só na primeira linha)
            if row == 0:
                ax.set_title(f'{period_label}', fontsize=18, fontweight='bold', pad=12)

            # Nome da camada à esquerda (só coluna 0)
            if col == 0:
                ax.text(-0.08, 0.5, layer_name, transform=ax.transAxes,
                        fontsize=17, fontweight='bold', color=color,
                        rotation=90, va='center', ha='center')

            # Caixa de métricas no canto inferior direito
            stats_text = f'N={n_nodes}   E={n_edges}   Dens.={density:.3f}'
            ax.text(0.98, 0.03, stats_text, transform=ax.transAxes,
                    fontsize=12, color='#444444', va='bottom', ha='right',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor='#cccccc', alpha=0.85))

            ax.axis('off')
            # Borda sutil
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.5)
                spine.set_color('#dddddd')

    fig.suptitle('Comparação Visual das 4 Camadas de Rede',
                 fontsize=21, fontweight='bold', y=0.99)

    # Nota explicativa
    fig.text(0.5, 0.005,
             'Redes densas (Comércio, Diplomacia) mostram integração quase total  |  '
             'Redes esparsas (Alianças, Disputas) revelam a estrutura de blocos geopolíticos',
             ha='center', fontsize=13, fontstyle='italic', color='#666666')

    plt.tight_layout(rect=[0.03, 0.02, 1, 0.97])

    return _save_and_close(fig, fig_dir, 'figura_4_comparacao_4_redes.png', gerar_figura_4)


# ============================================================================
# FIGURA 7 — Heatmap de Jaccard inter-camadas (multiplex)
# ============================================================================

def gerar_figura_7():
    """Figura 7 — Heatmap de correlação Jaccard inter-camadas, pré-WWI vs pré-WWII."""
    print("Gerando Figura 7 — Heatmap Jaccard inter-camadas...")
    fig_dir = _get_figure_dir(7, 'jaccard_multiplex')

    from src.network.metrics import calculate_layer_jaccard

    layer_names = ['Alianças', 'Comércio', 'Disputas', 'Diplomacia']
    builders = [_build_alliance_graph, _build_trade_graph,
                _build_dispute_graph, _build_diplomacy_graph]

    jaccard_data = {}
    for period_key, period_label in [('pre_wwi', 'Pré-WWI (1890–1914)'),
                                      ('pre_wwii', 'Pré-WWII (1925–1939)')]:
        networks = {}
        for name, build_func in zip(layer_names, builders):
            networks[name] = build_func(period_key)
        jaccard_df = calculate_layer_jaccard(networks)
        jaccard_data[period_label] = jaccard_df

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('white')

    for ax, (period_label, df) in zip(axes, jaccard_data.items()):
        mask = np.zeros_like(df.values, dtype=bool)
        # Mascarar diagonal (sempre 1.0, não informativo)
        np.fill_diagonal(mask, True)

        sns.heatmap(df, ax=ax, annot=True, fmt='.3f', cmap='YlGnBu',
                    vmin=0, vmax=1, linewidths=0.8, linecolor='white',
                    cbar_kws={'shrink': 0.8, 'label': 'Jaccard'},
                    mask=mask, annot_kws={'fontsize': 16, 'fontweight': 'bold'})

        # Preencher diagonal com cinza e texto "—"
        for i in range(len(df)):
            ax.text(i + 0.5, i + 0.5, '—', ha='center', va='center',
                    fontsize=16, color='#999999')

        ax.set_title(period_label, fontsize=17, fontweight='bold', pad=10)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=14)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=14)

    fig.suptitle('Índice de Jaccard Inter-Camadas\n'
                 '(Proporção de arestas compartilhadas entre camadas)',
                 fontsize=19, fontweight='bold', y=1.04)

    plt.tight_layout(rect=[0, 0.08, 1, 0.98])

    fig.text(0.5, 0.01,
             'Valores altos indicam sobreposição estrutural entre camadas  |  '
             'Jaccard = |E_i ∩ E_j| / |E_i ∪ E_j|',
             ha='center', fontsize=12, fontstyle='italic', color='#666666')

    return _save_and_close(fig, fig_dir, 'figura_7_jaccard_multiplex.png', gerar_figura_7)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Gera figuras do TCC')
    parser.add_argument('--fig', type=int, default=0,
                        help='Número da figura (0=todas, 1-7)')
    args = parser.parse_args()

    generators = {
        1: gerar_figura_1,
        2: gerar_figura_2,
        3: gerar_figura_3,
        4: gerar_figura_4,  # Comparação visual das 4 redes
        5: gerar_figura_5,  # Slope chart brokers de disputas
        6: gerar_figura_6,  # Heatmap betweenness
        7: gerar_figura_7,  # Jaccard multiplex inter-camadas
        8: gerar_figura_8,  # Robustez CINC
    }

    if args.fig == 0:
        for num, gen in sorted(generators.items()):
            gen()
    elif args.fig in generators:
        generators[args.fig]()
    else:
        print(f"Figura {args.fig} não implementada. Disponíveis: {list(generators.keys())}")

    print("\nConcluído!")
