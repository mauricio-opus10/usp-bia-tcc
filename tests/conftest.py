"""
Pytest fixtures for TCC test suite.

Provides sample data and common test utilities.
"""

import pytest
import pandas as pd
import networkx as nx
import numpy as np


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_alliance_df():
    """Sample alliance data mimicking COW alliance_v4.1_by_dyad format."""
    return pd.DataFrame({
        'version4id': [1, 2, 3, 4, 5],
        'ccode1': [2, 2, 200, 200, 220],
        'state_name1': ['United States', 'United States', 'United Kingdom', 'United Kingdom', 'France'],
        'ccode2': [200, 220, 220, 255, 255],
        'state_name2': ['United Kingdom', 'France', 'France', 'Germany', 'Germany'],
        'dyad_st_year': [1900, 1905, 1904, 1890, 1894],
        'dyad_end_year': [1920, 1918, 1914, 1914, 1914],
        'defense': [1, 0, 1, 0, 0],
        'neutrality': [0, 1, 0, 0, 1],
        'nonaggression': [0, 0, 0, 1, 0],
        'entente': [0, 0, 0, 0, 0],
    })


@pytest.fixture
def sample_trade_df():
    """Sample trade data mimicking COW Dyadic_COW_4.0 format."""
    return pd.DataFrame({
        'ccode1': [2, 2, 200, 200, 220],
        'ccode2': [200, 220, 220, 255, 255],
        'year': [1910, 1910, 1910, 1910, 1910],
        'importer1': ['United States', 'United States', 'United Kingdom', 'United Kingdom', 'France'],
        'importer2': ['United Kingdom', 'France', 'France', 'Germany', 'Germany'],
        'flow1': [1000, 500, 800, 600, 700],
        'flow2': [1200, 400, 900, 500, 650],
    })


@pytest.fixture
def sample_nmc_df():
    """Sample NMC data with CINC scores."""
    return pd.DataFrame({
        'ccode': [2, 2, 200, 200, 220, 220, 255, 255, 365, 365],
        'stateabb': ['USA', 'USA', 'UKG', 'UKG', 'FRN', 'FRN', 'GMY', 'GMY', 'RUS', 'RUS'],
        'year': [1900, 1910, 1900, 1910, 1900, 1910, 1900, 1910, 1900, 1910],
        'cinc': [0.15, 0.18, 0.12, 0.11, 0.08, 0.07, 0.10, 0.12, 0.09, 0.10],
    })


@pytest.fixture
def sample_mids_df():
    """Sample MIDs dispute data (MIDA format)."""
    return pd.DataFrame({
        'dispnum': [1, 2, 3],
        'styear': [1905, 1908, 1912],
        'stmon': [3, 7, 1],
        'stday': [15, 20, 5],
        'endyear': [1905, 1909, 1912],
        'endmon': [6, 2, 3],
        'endday': [30, 15, 10],
        'outcome': [1, 2, 3],
        'fatality': [0, 1, 2],
        'hostlev': [3, 4, 5],
    })


@pytest.fixture
def sample_mids_participants_df():
    """Sample MIDs participant data (MIDB format) with Side A/B information."""
    return pd.DataFrame({
        'dispnum': [1, 1, 2, 2, 2, 3, 3],
        'ccode': [2, 200, 220, 255, 365, 200, 255],
        'stateabb': ['USA', 'UKG', 'FRN', 'GMY', 'RUS', 'UKG', 'GMY'],
        'styear': [1905, 1905, 1908, 1908, 1908, 1912, 1912],
        'endyear': [1905, 1905, 1909, 1909, 1909, 1912, 1912],
        'sidea': [1, 0, 1, 0, 0, 1, 0],  # 1 = Side A, 0 = Side B
        'fatality': [0, 0, 1, 1, 0, 2, 1],
        'hostlev': [3, 3, 4, 4, 3, 5, 4],
    })


@pytest.fixture
def sample_edges_df():
    """Pre-processed edge DataFrame ready for network construction."""
    return pd.DataFrame({
        'source': [2, 2, 200, 200, 220],
        'target': [200, 220, 220, 255, 255],
        'source_name': ['USA', 'USA', 'UKG', 'UKG', 'FRN'],
        'target_name': ['UKG', 'FRN', 'FRN', 'GMY', 'GMY'],
        'weight': [4, 3, 4, 2, 3],
        'alliance_type': ['defense', 'neutrality', 'defense', 'nonaggression', 'neutrality'],
    })


@pytest.fixture
def sample_graph():
    """Simple test graph with known properties."""
    G = nx.Graph()
    # Create a small network with known structure
    # Triangle: A-B-C-A plus D connected only to A
    G.add_edge('A', 'B', weight=1.0)
    G.add_edge('B', 'C', weight=2.0)
    G.add_edge('C', 'A', weight=1.5)
    G.add_edge('A', 'D', weight=0.5)

    # Add node names
    nx.set_node_attributes(G, {
        'A': 'Node A',
        'B': 'Node B',
        'C': 'Node C',
        'D': 'Node D'
    }, 'name')

    return G


@pytest.fixture
def disconnected_graph():
    """Graph with multiple components for edge case testing."""
    G = nx.Graph()
    # Component 1: A-B-C
    G.add_edge('A', 'B')
    G.add_edge('B', 'C')
    # Component 2: D-E (disconnected)
    G.add_edge('D', 'E')
    return G


@pytest.fixture
def complete_graph():
    """Complete graph K5 for testing dense networks."""
    return nx.complete_graph(5)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

@pytest.fixture
def temp_csv(tmp_path):
    """Factory fixture for creating temporary CSV files."""
    def _create_csv(df, filename):
        filepath = tmp_path / filename
        df.to_csv(filepath, index=False)
        return filepath
    return _create_csv
