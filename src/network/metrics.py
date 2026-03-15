"""
Funções para cálculo de métricas de rede
"""

import networkx as nx
import numpy as np
import pandas as pd
from itertools import combinations
from typing import Dict, Any, List, Optional


def calculate_centrality_metrics(G: nx.Graph, weighted: bool = False) -> pd.DataFrame:
    """
    Calcula métricas de centralidade para todos os nós.

    Args:
        G: Grafo NetworkX
        weighted: Se True, considera pesos das arestas

    Returns:
        DataFrame com métricas por nó
    """
    weight_param = 'weight' if weighted and nx.is_weighted(G) else None

    metrics = {
        'degree': dict(G.degree()),
        'degree_centrality': nx.degree_centrality(G),
        'betweenness_centrality': nx.betweenness_centrality(G, weight=weight_param),
        'closeness_centrality': nx.closeness_centrality(G),
        'clustering_coefficient': nx.clustering(G),
    }

    # Eigenvector centrality pode falhar em grafos desconectados
    try:
        metrics['eigenvector_centrality'] = nx.eigenvector_centrality(
            G, max_iter=1000, weight=weight_param
        )
    except nx.PowerIterationFailedConvergence:
        # Para grafos desconectados, calcular por componente
        metrics['eigenvector_centrality'] = {}
        for component in nx.connected_components(G):
            subgraph = G.subgraph(component)
            if len(subgraph) > 1:
                eig = nx.eigenvector_centrality(subgraph, max_iter=1000, weight=weight_param)
                metrics['eigenvector_centrality'].update(eig)
            else:
                for node in component:
                    metrics['eigenvector_centrality'][node] = 0.0

    # PageRank
    try:
        metrics['pagerank'] = nx.pagerank(G, weight=weight_param)
    except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
        # Fallback for graphs where PageRank doesn't converge
        metrics['pagerank'] = {node: 0.0 for node in G.nodes()}

    # Criar DataFrame
    df = pd.DataFrame(metrics)
    df.index.name = 'node'

    # Adicionar nome do nó se disponível
    names = nx.get_node_attributes(G, 'name')
    if names:
        df['name'] = df.index.map(names)

    return df.sort_values('degree_centrality', ascending=False)


def calculate_global_metrics(G: nx.Graph) -> Dict[str, Any]:
    """
    Calcula métricas globais da rede.

    Args:
        G: Grafo NetworkX

    Returns:
        Dicionário com métricas globais
    """
    metrics = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'density': nx.density(G),
        'is_connected': nx.is_connected(G),
        'num_components': nx.number_connected_components(G),
        'average_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'average_clustering': nx.average_clustering(G),
    }

    # Métricas que requerem grafo conectado
    if nx.is_connected(G):
        metrics['diameter'] = nx.diameter(G)
        metrics['average_path_length'] = nx.average_shortest_path_length(G)
        metrics['radius'] = nx.radius(G)
    else:
        # Calcular para o maior componente
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        metrics['largest_component_size'] = len(largest_cc)
        metrics['largest_component_diameter'] = nx.diameter(subgraph)
        metrics['largest_component_avg_path'] = nx.average_shortest_path_length(subgraph)

    return metrics


def calculate_community_metrics(
    G: nx.Graph,
    algorithm: str = 'louvain'
) -> Dict[str, Any]:
    """
    Detecta comunidades e calcula métricas relacionadas.

    Args:
        G: Grafo NetworkX
        algorithm: Algoritmo de detecção ('louvain', 'greedy', 'label_propagation')

    Returns:
        Dicionário com comunidades e métricas
    """
    import community as community_louvain

    if algorithm == 'louvain':
        partition = community_louvain.best_partition(G)
        communities = {}
        for node, comm_id in partition.items():
            if comm_id not in communities:
                communities[comm_id] = []
            communities[comm_id].append(node)
        community_list = list(communities.values())
    elif algorithm == 'greedy':
        from networkx.algorithms.community import greedy_modularity_communities
        community_list = list(greedy_modularity_communities(G))
        partition = {}
        for i, comm in enumerate(community_list):
            for node in comm:
                partition[node] = i
    elif algorithm == 'label_propagation':
        from networkx.algorithms.community import label_propagation_communities
        community_list = list(label_propagation_communities(G))
        partition = {}
        for i, comm in enumerate(community_list):
            for node in comm:
                partition[node] = i
    else:
        raise ValueError(f"Algoritmo não suportado: {algorithm}")

    # Calcular modularidade
    from networkx.algorithms.community import modularity
    modularity_score = modularity(G, community_list)

    return {
        'partition': partition,
        'communities': community_list,
        'num_communities': len(community_list),
        'modularity': modularity_score,
        'community_sizes': [len(c) for c in community_list]
    }


def compare_networks(G1: nx.Graph, G2: nx.Graph, label1: str = "G1", label2: str = "G2") -> pd.DataFrame:
    """
    Compara métricas entre duas redes.

    Args:
        G1, G2: Grafos a comparar
        label1, label2: Rótulos para as redes

    Returns:
        DataFrame comparativo
    """
    metrics1 = calculate_global_metrics(G1)
    metrics2 = calculate_global_metrics(G2)

    # Adicionar métricas de comunidade
    comm1 = calculate_community_metrics(G1)
    comm2 = calculate_community_metrics(G2)

    metrics1['num_communities'] = comm1['num_communities']
    metrics1['modularity'] = comm1['modularity']
    metrics2['num_communities'] = comm2['num_communities']
    metrics2['modularity'] = comm2['modularity']

    # Criar DataFrame comparativo
    comparison = pd.DataFrame({
        label1: metrics1,
        label2: metrics2
    })

    comparison['diff'] = comparison[label2] - comparison[label1]
    # Vectorized percentage calculation (avoids division by zero)
    safe_denom = comparison[label1].replace(0, np.nan)
    comparison['diff_pct'] = (comparison['diff'] / safe_denom * 100).round(2).fillna(0.0)

    return comparison


# =========================================================================
# MÉTRICAS MULTIPLEX (CROSS-LAYER)
# =========================================================================


def calculate_edge_overlap(networks: Dict[str, nx.Graph]) -> pd.DataFrame:
    """
    Calcula sobreposição de arestas entre camadas.

    Para cada par de nós (u, v) conectado em qualquer camada, conta em
    quantas camadas a aresta existe.

    Args:
        networks: Dicionário {nome_camada: grafo NetworkX}

    Returns:
        DataFrame com colunas: node1, node2, n_layers, layers
    """
    all_edges: set = set()
    for G in networks.values():
        all_edges.update(frozenset(e) for e in G.edges())

    rows: List[Dict] = []
    for edge in all_edges:
        u, v = tuple(edge)
        present_in = [name for name, G in networks.items() if G.has_edge(u, v)]
        rows.append({
            'node1': u,
            'node2': v,
            'n_layers': len(present_in),
            'layers': ', '.join(sorted(present_in)),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values('n_layers', ascending=False).reset_index(drop=True)
    return df


def calculate_layer_jaccard(networks: Dict[str, nx.Graph]) -> pd.DataFrame:
    """
    Calcula índice de Jaccard entre cada par de camadas.

    Jaccard(i, j) = |E_i ∩ E_j| / |E_i ∪ E_j|

    Args:
        networks: Dicionário {nome_camada: grafo NetworkX}

    Returns:
        DataFrame matriz simétrica (nomes das camadas como index e colunas)
    """
    names = list(networks.keys())
    edge_sets = {
        name: set(frozenset(e) for e in G.edges())
        for name, G in networks.items()
    }

    n = len(names)
    matrix = np.ones((n, n))  # diagonal = 1.0

    for (i, name_i), (j, name_j) in combinations(enumerate(names), 2):
        intersection = len(edge_sets[name_i] & edge_sets[name_j])
        union = len(edge_sets[name_i] | edge_sets[name_j])
        jaccard = intersection / union if union > 0 else 0.0
        matrix[i, j] = jaccard
        matrix[j, i] = jaccard

    return pd.DataFrame(matrix, index=names, columns=names)


def calculate_multiplex_profile(networks: Dict[str, nx.Graph]) -> pd.DataFrame:
    """
    Calcula perfil multiplex por país.

    Para cada nó: grau e betweenness em cada camada, número de camadas
    em que está conectado (grau > 0) e número de camadas em que é broker
    (betweenness > 0).

    Args:
        networks: Dicionário {nome_camada: grafo NetworkX}

    Returns:
        DataFrame com colunas por camada (grau, betweenness) + resumo
    """
    # Pré-calcular betweenness por camada
    bc_by_layer: Dict[str, Dict] = {}
    for name, G in networks.items():
        bc_by_layer[name] = nx.betweenness_centrality(G)

    all_nodes: set = set()
    for G in networks.values():
        all_nodes.update(G.nodes())

    rows: List[Dict] = []
    for node in sorted(all_nodes):
        profile: Dict[str, Any] = {'node': node}
        n_connected = 0
        n_broker = 0
        for name, G in networks.items():
            if node in G:
                deg = G.degree(node)
                bc = bc_by_layer[name].get(node, 0.0)
                profile[f'{name}_degree'] = deg
                profile[f'{name}_betw'] = round(bc, 4)
                if deg > 0:
                    n_connected += 1
                if bc > 0:
                    n_broker += 1
            else:
                profile[f'{name}_degree'] = 0
                profile[f'{name}_betw'] = 0.0
        profile['n_layers_connected'] = n_connected
        profile['n_layers_broker'] = n_broker
        rows.append(profile)

    df = pd.DataFrame(rows).set_index('node')
    return df.sort_values('n_layers_broker', ascending=False)
