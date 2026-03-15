#!/usr/bin/env python3
"""
Gera dados de centralidade da rede de diplomacia e atualiza CSVs existentes.
Preenche a lacuna: diplomacia era a única camada sem métricas exportadas.

Uso:
    python3 gerar_dados_diplomacia.py
"""

import sys
import os
import csv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import networkx as nx
import pandas as pd
import numpy as np
import community as community_louvain

from src.etl.load_cow import load_diplomatic, load_nmc
from src.etl.transform import filter_states_by_cinc
from src.utils.helpers import TIME_WINDOWS, RANDOM_SEED

DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'output')

# Nomes abreviados COW
COW_ABB = {
    2: 'USA', 140: 'BRA', 200: 'UKG', 211: 'BEL', 220: 'FRN',
    230: 'SPN', 255: 'GMY', 290: 'POL', 300: 'AUH', 315: 'CZE',
    325: 'ITA', 365: 'RUS', 640: 'TUR', 710: 'CHN', 740: 'JPN',
}


def build_diplomacy_network(df_diplo: pd.DataFrame, relevant_states: list) -> nx.Graph:
    """Constrói rede de diplomacia: aresta se há troca diplomática (DE=1)."""
    # Filtrar para Estados relevantes
    df = df_diplo[
        (df_diplo['ccode1'].isin(relevant_states)) &
        (df_diplo['ccode2'].isin(relevant_states))
    ].copy()

    # Agregar: se houve troca diplomática em qualquer ano do período, cria aresta
    # Peso = nível máximo de representação (max de DR_at_1 e DR_at_2)
    edges = df.groupby(['ccode1', 'ccode2']).agg(
        has_exchange=('DE', 'max'),
        max_level_1=('DR_at_1', 'max'),
        max_level_2=('DR_at_2', 'max'),
    ).reset_index()

    # Filtrar apenas díades com troca diplomática
    edges = edges[edges['has_exchange'] == 1]

    # Peso = média dos níveis máximos (simétrico)
    edges['weight'] = (edges['max_level_1'] + edges['max_level_2']) / 2.0
    # Excluir nível 9 (desconhecido) do peso
    edges.loc[edges['max_level_1'] == 9, 'weight'] = edges['max_level_2']
    edges.loc[edges['max_level_2'] == 9, 'weight'] = edges['max_level_1']

    G = nx.Graph()
    # Adicionar todos os estados relevantes como nós
    for state in relevant_states:
        G.add_node(state)

    for _, row in edges.iterrows():
        G.add_edge(int(row['ccode1']), int(row['ccode2']),
                    weight=row['weight'])

    return G


def compute_metrics(G: nx.Graph) -> dict:
    """Calcula métricas globais e por nó."""
    n = G.number_of_nodes()
    m = G.number_of_edges()

    # Métricas globais
    density = nx.density(G)
    avg_degree = sum(dict(G.degree()).values()) / n if n > 0 else 0
    avg_clustering = nx.average_clustering(G)

    if nx.is_connected(G):
        diameter = nx.diameter(G)
        avg_path = nx.average_shortest_path_length(G)
    else:
        # Para grafos desconexos, usar o maior componente
        largest_cc = max(nx.connected_components(G), key=len)
        subG = G.subgraph(largest_cc)
        diameter = nx.diameter(subG)
        avg_path = nx.average_shortest_path_length(subG)

    partition = community_louvain.best_partition(G, random_state=RANDOM_SEED)
    modularity = community_louvain.modularity(partition, G)
    n_communities = len(set(partition.values()))

    # Métricas por nó
    degree = dict(G.degree())
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {n: 0.0 for n in G.nodes()}

    node_metrics = {}
    for node in G.nodes():
        node_metrics[node] = {
            'degree': degree[node],
            'betweenness': round(betweenness[node], 4),
            'closeness': round(closeness[node], 4),
            'eigenvector': round(eigenvector[node], 4),
        }

    return {
        'global': {
            'nodes': n,
            'edges': m,
            'density': density,
            'avg_degree': avg_degree,
            'avg_clustering': avg_clustering,
            'diameter': diameter,
            'avg_path_length': avg_path,
            'modularity': modularity,
            'n_communities': n_communities,
        },
        'nodes': node_metrics,
    }


def main():
    print("=" * 60)
    print("Gerando dados de centralidade — Rede de Diplomacia")
    print("=" * 60)

    periods = {
        'pre_wwi': ('Pré-WWI', 1890, 1914),
        'pre_wwii': ('Pré-WWII', 1925, 1939),
    }

    all_global = []
    all_node = []

    for period_key, (label, start, end) in periods.items():
        print(f"\n--- {label} ({start}–{end}) ---")

        # Carregar dados
        df_diplo = load_diplomatic(start_year=start, end_year=end)
        df_nmc = load_nmc(start_year=start, end_year=end)
        relevant_states = filter_states_by_cinc(df_nmc, threshold=0.01)

        print(f"  Estados relevantes (CINC >= 1%): {len(relevant_states)}")
        print(f"  Registros diplomáticos: {len(df_diplo)}")

        # Construir rede
        G = build_diplomacy_network(df_diplo, relevant_states)
        print(f"  Rede: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

        # Calcular métricas
        metrics = compute_metrics(G)
        g = metrics['global']

        print(f"  Densidade: {g['density']:.4f}")
        print(f"  Grau médio: {g['avg_degree']:.2f}")
        print(f"  Clustering: {g['avg_clustering']:.4f}")
        print(f"  Modularidade: {g['modularity']:.4f} ({g['n_communities']} comunidades)")

        # Guardar métricas globais
        all_global.append({
            'period': label,
            'layer': 'diplomacy',
            'nodes': g['nodes'],
            'edges': g['edges'],
            'density': g['density'],
            'avg_degree': g['avg_degree'],
            'avg_clustering': g['avg_clustering'],
            'diameter': g['diameter'],
            'avg_path_length': g['avg_path_length'],
            'modularity': g['modularity'],
            'n_communities': g['n_communities'],
        })

        # Guardar métricas por nó (ordenadas por grau)
        for ccode, nm in sorted(metrics['nodes'].items(),
                                 key=lambda x: x[1]['degree'], reverse=True):
            abb = COW_ABB.get(ccode, str(ccode))
            all_node.append({
                'ccode': ccode,
                'name': abb,
                'layer': 'diplomacy',
                'degree': nm['degree'],
                'betweenness': nm['betweenness'],
                'closeness': nm['closeness'],
                'eigenvector': nm['eigenvector'],
                'period': period_key,
            })

        # Imprimir ranking
        print(f"\n  Ranking de centralidade (grau):")
        for ccode, nm in sorted(metrics['nodes'].items(),
                                 key=lambda x: x[1]['degree'], reverse=True):
            abb = COW_ABB.get(ccode, str(ccode))
            print(f"    {abb:4s}: grau={nm['degree']:2d}  betw={nm['betweenness']:.4f}  "
                  f"close={nm['closeness']:.4f}  eigen={nm['eigenvector']:.4f}")

    # === Atualizar metricas_multilayer.csv ===
    print("\n\nAtualizando CSVs...")

    # 1. Adicionar diplomacia ao metricas_multilayer.csv
    ml_path = os.path.join(DATA_DIR, 'metricas_multilayer.csv')
    df_ml = pd.read_csv(ml_path)
    # Remover linhas de diplomacia existentes (se houver)
    df_ml = df_ml[df_ml['layer'] != 'diplomacy']
    # Adicionar novas
    df_new = pd.DataFrame(all_global)
    df_ml = pd.concat([df_ml, df_new], ignore_index=True)
    df_ml.to_csv(ml_path, index=False)
    print(f"  Atualizado: {ml_path}")

    # 2. Adicionar diplomacia ao centralidade_novas.csv
    comp_dir = os.path.join(DATA_DIR, 'comparison')
    os.makedirs(comp_dir, exist_ok=True)
    cn_path = os.path.join(comp_dir, 'centralidade_novas.csv')
    df_cn = pd.read_csv(cn_path)
    # Remover linhas de diplomacia existentes (se houver)
    df_cn = df_cn[df_cn['layer'] != 'diplomacy']
    # Adicionar novas
    df_node_new = pd.DataFrame(all_node)
    df_cn = pd.concat([df_cn, df_node_new], ignore_index=True)
    df_cn.to_csv(cn_path, index=False)
    print(f"  Atualizado: {cn_path}")

    print("\nConcluído!")


if __name__ == '__main__':
    main()
