"""
Tests for src/network module.

Tests network construction and metric calculation functions.
"""

import pytest
import pandas as pd
import networkx as nx
import numpy as np

from src.network.build_network import (
    build_alliance_network,
    build_trade_network,
    build_dispute_network,
    merge_networks,
)
from src.network.metrics import (
    calculate_centrality_metrics,
    calculate_global_metrics,
    calculate_community_metrics,
    compare_networks,
)


class TestBuildAllianceNetwork:
    """Tests for build_alliance_network function."""

    def test_creates_graph(self, sample_edges_df):
        """Test that function returns a NetworkX Graph."""
        G = build_alliance_network(sample_edges_df)

        assert isinstance(G, nx.Graph)

    def test_correct_nodes(self, sample_edges_df):
        """Test that all unique nodes are in the graph."""
        G = build_alliance_network(sample_edges_df)

        expected_nodes = set(sample_edges_df['source']).union(set(sample_edges_df['target']))
        assert set(G.nodes()) == expected_nodes

    def test_correct_edges(self, sample_edges_df):
        """Test that all edges are created."""
        G = build_alliance_network(sample_edges_df)

        assert G.number_of_edges() == len(sample_edges_df)

    def test_weighted_edges(self, sample_edges_df):
        """Test that edge weights are preserved."""
        G = build_alliance_network(sample_edges_df, weighted=True)

        # Check first edge
        edge_data = G.get_edge_data(2, 200)
        assert 'weight' in edge_data
        assert edge_data['weight'] == 4  # defense alliance

    def test_unweighted_mode(self, sample_edges_df):
        """Test building without weights."""
        G = build_alliance_network(sample_edges_df, weighted=False)

        # Graph should still be created
        assert G.number_of_edges() == len(sample_edges_df)

    def test_node_names(self, sample_edges_df):
        """Test that node names are added as attributes."""
        G = build_alliance_network(sample_edges_df)

        assert G.nodes[2].get('name') == 'USA'
        assert G.nodes[200].get('name') == 'UKG'

    def test_alliance_type_attribute(self, sample_edges_df):
        """Test that alliance_type is preserved in edge attributes."""
        G = build_alliance_network(sample_edges_df)

        edge_data = G.get_edge_data(2, 200)
        assert edge_data.get('alliance_type') == 'defense'

    def test_node_attributes(self, sample_edges_df):
        """Test adding custom node attributes."""
        node_attrs = pd.DataFrame({
            'cinc': [0.15, 0.12, 0.08, 0.10],
        }, index=[2, 200, 220, 255])

        G = build_alliance_network(sample_edges_df, node_attributes=node_attrs)

        assert G.nodes[2].get('cinc') == 0.15
        assert G.nodes[200].get('cinc') == 0.12


class TestBuildTradeNetwork:
    """Tests for build_trade_network function."""

    def test_creates_graph(self, sample_edges_df):
        """Test that function returns a NetworkX Graph."""
        trade_edges = sample_edges_df.copy()
        trade_edges['weight'] = [1000, 500, 800, 600, 700]

        G = build_trade_network(trade_edges)
        assert isinstance(G, nx.Graph)

    def test_weight_normalization(self):
        """Test that weights are normalized by max value."""
        edges = pd.DataFrame({
            'source': [1, 2],
            'target': [10, 20],
            'weight': [100, 200],
        })

        G = build_trade_network(edges, normalize_weights=True)

        # Max weight is 200, so weights should be 0.5 and 1.0
        assert G[1][10]['weight'] == 0.5
        assert G[2][20]['weight'] == 1.0

    def test_no_normalization(self):
        """Test building without weight normalization."""
        edges = pd.DataFrame({
            'source': [1, 2],
            'target': [10, 20],
            'weight': [100, 200],
        })

        G = build_trade_network(edges, normalize_weights=False)

        assert G[1][10]['weight'] == 100
        assert G[2][20]['weight'] == 200


class TestBuildDisputeNetwork:
    """Tests for build_dispute_network function."""

    def test_creates_graph(self, sample_mids_df, sample_mids_participants_df):
        """Test that function returns a NetworkX Graph."""
        G = build_dispute_network(sample_mids_df, sample_mids_participants_df)

        assert isinstance(G, nx.Graph)

    def test_creates_edges_between_opponents(self, sample_mids_df, sample_mids_participants_df):
        """Test that edges are created between opposing sides."""
        G = build_dispute_network(sample_mids_df, sample_mids_participants_df)

        # Dispute 1: USA (ccode=2, Side A) vs UKG (ccode=200, Side B) -> edge between 2 and 200
        assert G.has_edge(2, 200)

    def test_no_edges_same_side(self, sample_mids_df, sample_mids_participants_df):
        """Test that edges are NOT created between states on the same side."""
        G = build_dispute_network(sample_mids_df, sample_mids_participants_df, opponents_only=True)

        # Dispute 2: GMY (255) and RUS (365) both on Side B -> no edge between them
        # UNLESS they are on opposite sides in another dispute
        # In our test data: dispute 2 has FRN(220) on Side A vs GMY(255), RUS(365) on Side B
        # So GMY and RUS should NOT have an edge (they're never opponents)
        assert not G.has_edge(255, 365)

    def test_opponents_only_flag(self, sample_mids_df, sample_mids_participants_df):
        """Test opponents_only=False creates edges between all co-participants."""
        G_opponents = build_dispute_network(
            sample_mids_df, sample_mids_participants_df, opponents_only=True
        )
        G_all = build_dispute_network(
            sample_mids_df, sample_mids_participants_df, opponents_only=False
        )

        # With opponents_only=False, more edges should be created
        # (includes same-side participants)
        assert G_all.number_of_edges() >= G_opponents.number_of_edges()

    def test_weighted_by_disputes(self, sample_mids_df, sample_mids_participants_df):
        """Test that edge weights reflect number of disputes."""
        G = build_dispute_network(sample_mids_df, sample_mids_participants_df, weighted=True)

        # All edges should have weight >= 1
        for u, v, data in G.edges(data=True):
            assert data.get('weight', 0) >= 1

    def test_dispute_count_attribute(self, sample_mids_df, sample_mids_participants_df):
        """Test that dispute_count attribute is set on edges."""
        G = build_dispute_network(sample_mids_df, sample_mids_participants_df)

        for u, v, data in G.edges(data=True):
            assert 'dispute_count' in data
            assert data['dispute_count'] >= 1

    def test_side_a_vs_side_b_specific(self):
        """Test specific Side A vs Side B scenario."""
        disputes = pd.DataFrame({
            'dispnum': [100],
            'styear': [1910],
        })
        participants = pd.DataFrame({
            'dispnum': [100, 100, 100, 100],
            'ccode': [1, 2, 10, 20],  # 1,2 on Side A; 10,20 on Side B
            'sidea': [1, 1, 0, 0],
        })

        G = build_dispute_network(disputes, participants, opponents_only=True)

        # Should have edges: 1-10, 1-20, 2-10, 2-20 (Side A vs Side B)
        assert G.has_edge(1, 10)
        assert G.has_edge(1, 20)
        assert G.has_edge(2, 10)
        assert G.has_edge(2, 20)

        # Should NOT have edges: 1-2 (both Side A), 10-20 (both Side B)
        assert not G.has_edge(1, 2)
        assert not G.has_edge(10, 20)


class TestMergeNetworks:
    """Tests for merge_networks function."""

    def test_merge_two_networks(self):
        """Test merging two simple networks."""
        G1 = nx.Graph()
        G1.add_edge('A', 'B', weight=1)

        G2 = nx.Graph()
        G2.add_edge('B', 'C', weight=2)

        merged = merge_networks({'layer1': G1, 'layer2': G2})

        assert merged.has_edge('A', 'B')
        assert merged.has_edge('B', 'C')
        assert merged.number_of_nodes() == 3

    def test_weight_combination_sum(self):
        """Test sum weight combination."""
        G1 = nx.Graph()
        G1.add_edge('A', 'B', weight=1)

        G2 = nx.Graph()
        G2.add_edge('A', 'B', weight=2)

        merged = merge_networks({'layer1': G1, 'layer2': G2}, combine_weights='sum')

        assert merged['A']['B']['weight'] == 3

    def test_weight_combination_max(self):
        """Test max weight combination."""
        G1 = nx.Graph()
        G1.add_edge('A', 'B', weight=1)

        G2 = nx.Graph()
        G2.add_edge('A', 'B', weight=5)

        merged = merge_networks({'layer1': G1, 'layer2': G2}, combine_weights='max')

        assert merged['A']['B']['weight'] == 5

    def test_layer_tracking(self):
        """Test that layers are tracked in edge attributes."""
        G1 = nx.Graph()
        G1.add_edge('A', 'B', weight=1)

        G2 = nx.Graph()
        G2.add_edge('A', 'B', weight=2)

        merged = merge_networks({'alliance': G1, 'trade': G2})

        layers = merged['A']['B'].get('layers', [])
        assert 'alliance' in layers
        assert 'trade' in layers


class TestCalculateCentralityMetrics:
    """Tests for calculate_centrality_metrics function."""

    def test_returns_dataframe(self, sample_graph):
        """Test that function returns a DataFrame."""
        metrics = calculate_centrality_metrics(sample_graph)

        assert isinstance(metrics, pd.DataFrame)

    def test_all_nodes_present(self, sample_graph):
        """Test that all nodes have metrics."""
        metrics = calculate_centrality_metrics(sample_graph)

        assert len(metrics) == sample_graph.number_of_nodes()

    def test_required_columns(self, sample_graph):
        """Test that required metric columns are present."""
        metrics = calculate_centrality_metrics(sample_graph)

        required = ['degree', 'degree_centrality', 'betweenness_centrality',
                    'closeness_centrality', 'clustering_coefficient']
        for col in required:
            assert col in metrics.columns, f"Missing column: {col}"

    def test_degree_values(self, sample_graph):
        """Test that degree values are correct."""
        metrics = calculate_centrality_metrics(sample_graph)

        # Node A has 3 connections (B, C, D)
        assert metrics.loc['A', 'degree'] == 3
        # Node D has 1 connection (A)
        assert metrics.loc['D', 'degree'] == 1

    def test_centrality_range(self, sample_graph):
        """Test that centrality values are in valid range [0, 1]."""
        metrics = calculate_centrality_metrics(sample_graph)

        for col in ['degree_centrality', 'betweenness_centrality', 'closeness_centrality']:
            assert metrics[col].min() >= 0
            assert metrics[col].max() <= 1

    def test_node_a_highest_centrality(self, sample_graph):
        """Test that node A has highest centrality (most connected)."""
        metrics = calculate_centrality_metrics(sample_graph)

        assert metrics['degree_centrality'].idxmax() == 'A'
        assert metrics['betweenness_centrality'].idxmax() == 'A'

    def test_disconnected_graph(self, disconnected_graph):
        """Test handling of disconnected graphs."""
        # Should not raise an error
        metrics = calculate_centrality_metrics(disconnected_graph)

        assert len(metrics) == disconnected_graph.number_of_nodes()


class TestCalculateGlobalMetrics:
    """Tests for calculate_global_metrics function."""

    def test_returns_dict(self, sample_graph):
        """Test that function returns a dictionary."""
        metrics = calculate_global_metrics(sample_graph)

        assert isinstance(metrics, dict)

    def test_required_keys(self, sample_graph):
        """Test that required metrics are present."""
        metrics = calculate_global_metrics(sample_graph)

        required = ['num_nodes', 'num_edges', 'density', 'is_connected',
                    'average_degree', 'average_clustering']
        for key in required:
            assert key in metrics, f"Missing key: {key}"

    def test_node_edge_counts(self, sample_graph):
        """Test that node and edge counts are correct."""
        metrics = calculate_global_metrics(sample_graph)

        assert metrics['num_nodes'] == 4
        assert metrics['num_edges'] == 4

    def test_density_calculation(self, complete_graph):
        """Test density calculation on complete graph (should be 1.0)."""
        metrics = calculate_global_metrics(complete_graph)

        assert metrics['density'] == 1.0

    def test_connected_metrics(self, sample_graph):
        """Test metrics specific to connected graphs."""
        metrics = calculate_global_metrics(sample_graph)

        assert metrics['is_connected'] == True
        assert 'diameter' in metrics
        assert 'average_path_length' in metrics

    def test_disconnected_metrics(self, disconnected_graph):
        """Test metrics for disconnected graphs."""
        metrics = calculate_global_metrics(disconnected_graph)

        assert metrics['is_connected'] == False
        assert 'largest_component_size' in metrics


class TestCalculateCommunityMetrics:
    """Tests for calculate_community_metrics function."""

    def test_returns_dict(self, sample_graph):
        """Test that function returns a dictionary."""
        result = calculate_community_metrics(sample_graph)

        assert isinstance(result, dict)

    def test_required_keys(self, sample_graph):
        """Test that required keys are present."""
        result = calculate_community_metrics(sample_graph)

        required = ['partition', 'communities', 'num_communities', 'modularity']
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_partition_covers_all_nodes(self, sample_graph):
        """Test that partition includes all nodes."""
        result = calculate_community_metrics(sample_graph)

        assert set(result['partition'].keys()) == set(sample_graph.nodes())

    def test_modularity_range(self, sample_graph):
        """Test that modularity is in valid range [-0.5, 1]."""
        result = calculate_community_metrics(sample_graph)

        assert -0.5 <= result['modularity'] <= 1.0

    def test_louvain_algorithm(self, sample_graph):
        """Test Louvain algorithm explicitly."""
        result = calculate_community_metrics(sample_graph, algorithm='louvain')

        assert result['num_communities'] >= 1

    def test_greedy_algorithm(self, sample_graph):
        """Test greedy modularity algorithm."""
        result = calculate_community_metrics(sample_graph, algorithm='greedy')

        assert result['num_communities'] >= 1

    def test_invalid_algorithm(self, sample_graph):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError):
            calculate_community_metrics(sample_graph, algorithm='invalid')


class TestCompareNetworks:
    """Tests for compare_networks function."""

    def test_returns_dataframe(self, sample_graph):
        """Test that function returns a DataFrame."""
        G2 = sample_graph.copy()
        result = compare_networks(sample_graph, G2)

        assert isinstance(result, pd.DataFrame)

    def test_comparison_columns(self, sample_graph):
        """Test that comparison has expected columns."""
        G2 = sample_graph.copy()
        result = compare_networks(sample_graph, G2, label1='Net1', label2='Net2')

        assert 'Net1' in result.columns
        assert 'Net2' in result.columns
        assert 'diff' in result.columns

    def test_identical_networks(self, sample_graph):
        """Test comparing identical networks."""
        G2 = sample_graph.copy()
        result = compare_networks(sample_graph, G2)

        # Differences should be 0 for identical networks
        assert all(result['diff'] == 0)

    def test_different_networks(self, sample_graph, complete_graph):
        """Test comparing different networks."""
        result = compare_networks(sample_graph, complete_graph)

        # Should have some non-zero differences
        assert any(result['diff'] != 0)
