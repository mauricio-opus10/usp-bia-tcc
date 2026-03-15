"""
Funções para construção de redes (grafos) a partir dos dados
"""

import networkx as nx
import pandas as pd
from typing import Optional, Dict, Any


def _apply_node_names(G: nx.Graph, edges_df: pd.DataFrame) -> None:
    """Sets node name attributes from source_name/target_name columns."""
    if 'source_name' in edges_df.columns:
        name_map = {}
        for row in edges_df[['source', 'source_name', 'target', 'target_name']].itertuples(index=False):
            name_map[row.source] = row.source_name
            name_map[row.target] = row.target_name
        nx.set_node_attributes(G, name_map, 'name')


def _apply_node_attributes(G: nx.Graph, node_attributes: Optional[pd.DataFrame]) -> None:
    """Sets node attributes from a DataFrame indexed by node ID."""
    if node_attributes is not None:
        for node in G.nodes():
            if node in node_attributes.index:
                for col in node_attributes.columns:
                    G.nodes[node][col] = node_attributes.loc[node, col]


def build_alliance_network(
    edges_df: pd.DataFrame,
    weighted: bool = True,
    node_attributes: Optional[pd.DataFrame] = None
) -> nx.Graph:
    """
    Constrói grafo de alianças a partir de DataFrame de arestas.

    Args:
        edges_df: DataFrame com colunas source, target, weight (opcional)
        weighted: Se True, usa coluna 'weight' para peso das arestas
        node_attributes: DataFrame com atributos dos nós (ccode como índice)

    Returns:
        Grafo NetworkX não-direcionado
    """
    # Determine edge attributes to include
    edge_attr_cols = ['alliance_type'] if 'alliance_type' in edges_df.columns else []
    if weighted and 'weight' in edges_df.columns:
        edge_attr_cols.append('weight')

    # Use vectorized graph creation (much faster than iterrows)
    if edge_attr_cols:
        G = nx.from_pandas_edgelist(
            edges_df,
            source='source',
            target='target',
            edge_attr=edge_attr_cols
        )
    else:
        G = nx.from_pandas_edgelist(edges_df, source='source', target='target')

    _apply_node_names(G, edges_df)
    _apply_node_attributes(G, node_attributes)

    return G


def build_trade_network(
    edges_df: pd.DataFrame,
    normalize_weights: bool = True,
    node_attributes: Optional[pd.DataFrame] = None
) -> nx.Graph:
    """
    Constrói grafo de comércio a partir de DataFrame de arestas.

    Args:
        edges_df: DataFrame com colunas source, target, weight (trade volume)
        normalize_weights: Se True, normaliza pesos pelo máximo
        node_attributes: DataFrame com atributos dos nós

    Returns:
        Grafo NetworkX não-direcionado ponderado
    """
    # Normalizar pesos se solicitado (vectorized)
    if normalize_weights and 'weight' in edges_df.columns:
        max_weight = edges_df['weight'].max()
        edges_df = edges_df.copy()
        edges_df['weight'] = edges_df['weight'] / max_weight

    # Use vectorized graph creation
    edge_attr = ['weight'] if 'weight' in edges_df.columns else None
    G = nx.from_pandas_edgelist(
        edges_df,
        source='source',
        target='target',
        edge_attr=edge_attr
    )

    _apply_node_names(G, edges_df)
    _apply_node_attributes(G, node_attributes)

    return G


def build_dispute_network(
    disputes_df: pd.DataFrame,
    participants_df: pd.DataFrame,
    weighted: bool = True,
    opponents_only: bool = True
) -> nx.Graph:
    """
    Constrói grafo de disputas militarizadas.

    Cria arestas entre Estados que participaram de disputas militarizadas.
    Por padrão, apenas Estados em lados opostos (Side A vs Side B) são conectados.

    Args:
        disputes_df: DataFrame de disputas (MIDA) com coluna 'dispnum'
        participants_df: DataFrame de participantes (MIDB) com colunas:
            - dispnum: número da disputa
            - ccode: código COW do país
            - sidea: 1 = Side A (iniciador), 0 = Side B (alvo)
        weighted: Se True, peso = número de disputas entre a díade
        opponents_only: Se True, apenas cria arestas entre oponentes (Side A vs Side B).
                       Se False, cria arestas entre todos os co-participantes.

    Returns:
        Grafo NetworkX não-direcionado onde:
        - Nós = Estados participantes de disputas
        - Arestas = Conflitos entre Estados (peso = frequência)
    """
    G = nx.Graph()

    dispute_counts: Dict[tuple, int] = {}

    # Filtrar participantes para disputas relevantes (single pass via groupby)
    valid_disputes = set(disputes_df['dispnum'].unique())
    relevant = participants_df[participants_df['dispnum'].isin(valid_disputes)]

    for dispnum, participants in relevant.groupby('dispnum'):
        if opponents_only and 'sidea' in participants.columns:
            # Separar participantes por lado
            side_a = participants.loc[participants['sidea'] == 1, 'ccode'].unique()
            side_b = participants.loc[participants['sidea'] == 0, 'ccode'].unique()

            # Criar arestas APENAS entre lados opostos (Side A vs Side B)
            for s1 in side_a:
                for s2 in side_b:
                    edge = tuple(sorted([s1, s2]))
                    dispute_counts[edge] = dispute_counts.get(edge, 0) + 1
        else:
            # Fallback: criar arestas entre todos os participantes
            states = participants['ccode'].unique()
            for i, s1 in enumerate(states):
                for s2 in states[i+1:]:
                    edge = tuple(sorted([s1, s2]))
                    dispute_counts[edge] = dispute_counts.get(edge, 0) + 1

    # Adicionar arestas ao grafo
    for (s1, s2), count in dispute_counts.items():
        G.add_edge(s1, s2, weight=count if weighted else 1, dispute_count=count)

    return G


def merge_networks(
    networks: Dict[str, nx.Graph],
    combine_weights: str = 'sum'
) -> nx.Graph:
    """
    Combina múltiplas redes em uma única rede multilayer.

    Args:
        networks: Dicionário {nome_camada: grafo}
        combine_weights: Método para combinar pesos ('sum', 'max', 'mean')

    Returns:
        Grafo combinado com atributos de camada
    """
    G = nx.Graph()

    for layer_name, layer_graph in networks.items():
        for u, v, data in layer_graph.edges(data=True):
            if G.has_edge(u, v):
                # Combinar pesos
                existing_weight = G[u][v].get('weight', 0)
                new_weight = data.get('weight', 1)

                if combine_weights == 'sum':
                    G[u][v]['weight'] = existing_weight + new_weight
                elif combine_weights == 'max':
                    G[u][v]['weight'] = max(existing_weight, new_weight)
                elif combine_weights == 'mean':
                    # Track count for correct running average across >2 layers
                    n_layers = len(G[u][v].get('layers', [])) + 1
                    G[u][v]['weight'] = (existing_weight * (n_layers - 1) + new_weight) / n_layers

                # Adicionar camada à lista
                G[u][v]['layers'] = G[u][v].get('layers', []) + [layer_name]
            else:
                G.add_edge(u, v, weight=data.get('weight', 1), layers=[layer_name])

        # Copiar atributos dos nós
        for node, attrs in layer_graph.nodes(data=True):
            if node not in G:
                G.add_node(node, **attrs)
            else:
                G.nodes[node].update(attrs)

    return G
