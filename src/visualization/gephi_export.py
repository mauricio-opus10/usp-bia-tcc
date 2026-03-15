"""
Funções para exportar redes para Gephi
"""

import logging
import networkx as nx
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger('tcc_redes')


def export_to_gexf(
    G: nx.Graph,
    filepath: str,
    include_metrics: bool = True
) -> None:
    """
    Exporta grafo para formato GEXF (Gephi).

    Args:
        G: Grafo NetworkX
        filepath: Caminho do arquivo de saída
        include_metrics: Se True, calcula e inclui métricas como atributos
    """
    # Criar cópia para não modificar original
    G_export = G.copy()

    if include_metrics:
        # Adicionar métricas de centralidade como atributos dos nós
        degree_cent = nx.degree_centrality(G_export)
        betweenness = nx.betweenness_centrality(G_export)
        closeness = nx.closeness_centrality(G_export)

        try:
            eigenvector = nx.eigenvector_centrality(G_export, max_iter=1000)
        except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
            # Fallback for disconnected graphs or convergence issues
            eigenvector = {n: 0.0 for n in G_export.nodes()}

        for node in G_export.nodes():
            G_export.nodes[node]['degree_centrality'] = round(degree_cent[node], 6)
            G_export.nodes[node]['betweenness_centrality'] = round(betweenness[node], 6)
            G_export.nodes[node]['closeness_centrality'] = round(closeness[node], 6)
            G_export.nodes[node]['eigenvector_centrality'] = round(eigenvector.get(node, 0), 6)
            G_export.nodes[node]['degree'] = G_export.degree(node)

        # Detectar comunidades
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G_export)
            for node in G_export.nodes():
                G_export.nodes[node]['community'] = partition[node]
        except (ImportError, KeyError, ValueError) as e:
            logger.debug(f"Community detection skipped in GEXF export: {e}")

    # Garantir que diretório existe
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # Converter listas em atributos de arestas para strings (GEXF não suporta listas)
    for u, v, data in G_export.edges(data=True):
        for key, value in list(data.items()):
            if isinstance(value, list):
                G_export[u][v][key] = ','.join(str(item) for item in value)

    # Exportar
    nx.write_gexf(G_export, filepath)
    print(f"Grafo exportado para: {filepath}")


def export_to_graphml(G: nx.Graph, filepath: str) -> None:
    """
    Exporta grafo para formato GraphML.

    Args:
        G: Grafo NetworkX
        filepath: Caminho do arquivo de saída
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, filepath)
    print(f"Grafo exportado para: {filepath}")


def export_edge_list(G: nx.Graph, filepath: str, include_weights: bool = True) -> None:
    """
    Exporta lista de arestas em CSV.

    Args:
        G: Grafo NetworkX
        filepath: Caminho do arquivo de saída
        include_weights: Se True, inclui coluna de peso
    """
    import pandas as pd

    edges_data = []
    for u, v, data in G.edges(data=True):
        edge = {
            'source': u,
            'target': v,
            'source_name': G.nodes[u].get('name', u),
            'target_name': G.nodes[v].get('name', v),
        }
        if include_weights:
            edge['weight'] = data.get('weight', 1)
        edges_data.append(edge)

    df = pd.DataFrame(edges_data)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Lista de arestas exportada para: {filepath}")


def export_node_list(G: nx.Graph, filepath: str) -> None:
    """
    Exporta lista de nós com atributos em CSV.

    Args:
        G: Grafo NetworkX
        filepath: Caminho do arquivo de saída
    """
    import pandas as pd

    nodes_data = []
    for node, attrs in G.nodes(data=True):
        node_data = {'id': node}
        node_data.update(attrs)
        nodes_data.append(node_data)

    df = pd.DataFrame(nodes_data)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Lista de nós exportada para: {filepath}")
