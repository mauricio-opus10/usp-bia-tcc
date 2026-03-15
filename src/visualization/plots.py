"""
Funções para visualização de redes e métricas
"""

import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional, Dict, Any, List
import numpy as np


def plot_network(
    G: nx.Graph,
    layout: str = 'spring',
    node_size_attr: Optional[str] = None,
    node_color_attr: Optional[str] = None,
    title: str = '',
    figsize: tuple = (12, 10),
    save_path: Optional[str] = None,
    show_labels: bool = True,
    **kwargs
) -> plt.Figure:
    """
    Plota grafo com customizações.

    Args:
        G: Grafo NetworkX
        layout: Algoritmo de layout ('spring', 'kamada_kawai', 'circular', 'shell')
        node_size_attr: Atributo para tamanho dos nós (ou métrica como 'degree')
        node_color_attr: Atributo para cor dos nós (ou 'community')
        title: Título do gráfico
        figsize: Tamanho da figura
        save_path: Caminho para salvar imagem
        show_labels: Se True, mostra rótulos dos nós

    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Calcular layout
    if layout == 'spring':
        pos = nx.spring_layout(G, k=2/np.sqrt(G.number_of_nodes()), seed=42)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'shell':
        pos = nx.shell_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42)

    # Calcular tamanhos dos nós
    if node_size_attr == 'degree':
        degrees = dict(G.degree())
        node_sizes = [300 + degrees[n] * 100 for n in G.nodes()]
    elif node_size_attr and node_size_attr in nx.get_node_attributes(G, node_size_attr):
        attrs = nx.get_node_attributes(G, node_size_attr)
        node_sizes = [300 + attrs.get(n, 0) * 1000 for n in G.nodes()]
    else:
        node_sizes = 500

    # Calcular cores dos nós
    if node_color_attr == 'community':
        import community as community_louvain
        partition = community_louvain.best_partition(G)
        node_colors = [partition[n] for n in G.nodes()]
        cmap = plt.cm.Set3
    elif node_color_attr and node_color_attr in list(nx.get_node_attributes(G, node_color_attr).keys()):
        attrs = nx.get_node_attributes(G, node_color_attr)
        node_colors = [attrs.get(n, 0) for n in G.nodes()]
        cmap = plt.cm.viridis
    else:
        node_colors = 'lightblue'
        cmap = None

    # Desenhar rede
    nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
    nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=cmap,
        alpha=0.8,
        ax=ax
    )

    if show_labels:
        # Usar nomes se disponíveis
        labels = nx.get_node_attributes(G, 'name')
        if not labels:
            labels = {n: str(n) for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

    ax.set_title(title, fontsize=14)
    ax.axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_centrality_distribution(
    metrics_df: pd.DataFrame,
    metric: str = 'degree_centrality',
    title: str = '',
    figsize: tuple = (10, 6),
    top_n: int = 15,
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plota distribuição de uma métrica de centralidade.

    Args:
        metrics_df: DataFrame com métricas (de calculate_centrality_metrics)
        metric: Nome da métrica a plotar
        title: Título do gráfico
        figsize: Tamanho da figura
        top_n: Número de nós top a destacar
        save_path: Caminho para salvar

    Returns:
        Figura matplotlib
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Histograma
    axes[0].hist(metrics_df[metric], bins=30, edgecolor='black', alpha=0.7)
    axes[0].set_xlabel(metric)
    axes[0].set_ylabel('Frequência')
    axes[0].set_title(f'Distribuição de {metric}')

    # Top N barras
    top_data = metrics_df.nlargest(top_n, metric)
    labels = top_data['name'] if 'name' in top_data.columns else top_data.index.astype(str)

    bars = axes[1].barh(range(top_n), top_data[metric].values, color='steelblue')
    axes[1].set_yticks(range(top_n))
    axes[1].set_yticklabels(labels)
    axes[1].invert_yaxis()
    axes[1].set_xlabel(metric)
    axes[1].set_title(f'Top {top_n} por {metric}')

    if title:
        fig.suptitle(title, fontsize=14, y=1.02)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_network_comparison(
    G1: nx.Graph,
    G2: nx.Graph,
    label1: str = 'Rede 1',
    label2: str = 'Rede 2',
    figsize: tuple = (16, 8),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plota duas redes lado a lado para comparação.

    Args:
        G1, G2: Grafos a comparar
        label1, label2: Rótulos
        figsize: Tamanho da figura
        save_path: Caminho para salvar

    Returns:
        Figura matplotlib
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    for ax, G, label in [(axes[0], G1, label1), (axes[1], G2, label2)]:
        pos = nx.spring_layout(G, k=2/np.sqrt(max(G.number_of_nodes(), 1)), seed=42)

        # Colorir por comunidade
        import community as community_louvain
        partition = community_louvain.best_partition(G)
        node_colors = [partition[n] for n in G.nodes()]

        # Tamanho por grau
        degrees = dict(G.degree())
        node_sizes = [100 + degrees[n] * 50 for n in G.nodes()]

        nx.draw_networkx_edges(G, pos, alpha=0.2, ax=ax)
        nx.draw_networkx_nodes(
            G, pos,
            node_size=node_sizes,
            node_color=node_colors,
            cmap=plt.cm.Set3,
            alpha=0.8,
            ax=ax
        )

        ax.set_title(f'{label}\n(N={G.number_of_nodes()}, E={G.number_of_edges()})', fontsize=12)
        ax.axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def create_interactive_network(
    G: nx.Graph,
    output_path: str,
    height: str = '800px',
    width: str = '100%',
    title: str = ''
) -> None:
    """
    Cria visualização interativa com pyvis.

    Args:
        G: Grafo NetworkX
        output_path: Caminho do arquivo HTML de saída
        height, width: Dimensões
        title: Título
    """
    from pyvis.network import Network

    net = Network(height=height, width=width, bgcolor='#ffffff', font_color='black')
    net.from_nx(G)

    # Configurações de física
    net.set_options("""
    var options = {
      "nodes": {
        "font": {"size": 12}
      },
      "edges": {
        "color": {"inherit": true},
        "smooth": false
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based"
      }
    }
    """)

    net.save_graph(output_path)
