"""
Tests for src/etl module.

Tests data loading and transformation functions.
"""

import pytest
import pandas as pd
import numpy as np

from src.etl.transform import (
    filter_by_year,
    filter_by_cinc,
    filter_states_by_cinc,
    prepare_alliance_edges,
    prepare_trade_edges,
)
from src.utils.helpers import ALLIANCE_WEIGHTS


class TestFilterByYear:
    """Tests for filter_by_year function."""

    def test_filter_basic(self):
        """Test basic year filtering."""
        df = pd.DataFrame({
            'year': [1900, 1905, 1910, 1915, 1920],
            'value': [1, 2, 3, 4, 5]
        })
        result = filter_by_year(df, 1905, 1915)

        assert len(result) == 3
        assert list(result['year']) == [1905, 1910, 1915]

    def test_filter_inclusive(self):
        """Test that boundaries are inclusive."""
        df = pd.DataFrame({'year': [1900, 1910, 1920], 'value': [1, 2, 3]})
        result = filter_by_year(df, 1900, 1920)

        assert len(result) == 3

    def test_filter_custom_column(self):
        """Test filtering with custom year column name."""
        df = pd.DataFrame({
            'styear': [1900, 1905, 1910],
            'value': [1, 2, 3]
        })
        result = filter_by_year(df, 1900, 1905, year_column='styear')

        assert len(result) == 2

    def test_filter_empty_result(self):
        """Test filtering that returns empty DataFrame."""
        df = pd.DataFrame({'year': [1900, 1905], 'value': [1, 2]})
        result = filter_by_year(df, 1950, 1960)

        assert len(result) == 0


class TestFilterByCinc:
    """Tests for filter_by_cinc function."""

    def test_filter_single_ccode(self, sample_nmc_df):
        """Test filtering DataFrame with single ccode column."""
        df = pd.DataFrame({
            'ccode': [2, 200, 220, 255, 365, 999],
            'value': [1, 2, 3, 4, 5, 6]
        })
        # With threshold 0.05, all major powers should pass
        result = filter_by_cinc(df, sample_nmc_df, threshold=0.05)

        assert len(result) == 5  # 999 should be filtered out
        assert 999 not in result['ccode'].values

    def test_filter_dyadic(self, sample_nmc_df):
        """Test filtering dyadic DataFrame (ccode1, ccode2)."""
        df = pd.DataFrame({
            'ccode1': [2, 2, 999],
            'ccode2': [200, 999, 200],
            'value': [1, 2, 3]
        })
        result = filter_by_cinc(df, sample_nmc_df, threshold=0.05)

        # Only first row should remain (both 2 and 200 pass threshold)
        assert len(result) == 1
        assert result.iloc[0]['ccode1'] == 2
        assert result.iloc[0]['ccode2'] == 200

    def test_filter_threshold(self, sample_nmc_df):
        """Test different threshold values."""
        df = pd.DataFrame({
            'ccode': [2, 200, 220, 255, 365],
            'value': [1, 2, 3, 4, 5]
        })

        # High threshold should filter more
        result_high = filter_by_cinc(df, sample_nmc_df, threshold=0.15)
        # Low threshold should filter less
        result_low = filter_by_cinc(df, sample_nmc_df, threshold=0.05)

        assert len(result_high) <= len(result_low)


class TestFilterStatesByCinc:
    """Tests for filter_states_by_cinc function."""

    def test_returns_list(self, sample_nmc_df):
        """Test that function returns a list of ccodes."""
        result = filter_states_by_cinc(sample_nmc_df, threshold=0.05)

        assert isinstance(result, list)
        assert all(isinstance(x, (int, np.integer)) for x in result)

    def test_threshold_filtering(self, sample_nmc_df):
        """Test that threshold is applied correctly."""
        # USA has highest CINC (0.15-0.18 avg ~0.165)
        result_high = filter_states_by_cinc(sample_nmc_df, threshold=0.15)
        result_low = filter_states_by_cinc(sample_nmc_df, threshold=0.05)

        assert 2 in result_high  # USA should always pass
        assert len(result_high) <= len(result_low)


class TestPrepareAllianceEdges:
    """Tests for prepare_alliance_edges function."""

    def test_basic_preparation(self, sample_alliance_df):
        """Test basic edge preparation."""
        edges = prepare_alliance_edges(sample_alliance_df)

        assert 'source' in edges.columns
        assert 'target' in edges.columns
        assert 'weight' in edges.columns
        assert 'alliance_type' in edges.columns

    def test_weight_assignment(self, sample_alliance_df):
        """Test that weights are correctly assigned based on alliance type."""
        edges = prepare_alliance_edges(sample_alliance_df)

        for _, row in edges.iterrows():
            expected_weight = ALLIANCE_WEIGHTS.get(row['alliance_type'], 0)
            assert row['weight'] == expected_weight, \
                f"Weight mismatch for {row['alliance_type']}: expected {expected_weight}, got {row['weight']}"

    def test_defense_highest_weight(self, sample_alliance_df):
        """Test that defense alliances get highest weight (4)."""
        edges = prepare_alliance_edges(sample_alliance_df)
        defense_edges = edges[edges['alliance_type'] == 'defense']

        assert all(defense_edges['weight'] == 4)

    def test_year_filtering(self, sample_alliance_df):
        """Test filtering by year range."""
        # Filter to 1900-1910 should exclude some alliances
        edges = prepare_alliance_edges(sample_alliance_df, start_year=1900, end_year=1910)

        assert len(edges) > 0
        assert len(edges) <= len(sample_alliance_df)

    def test_alliance_type_filtering(self, sample_alliance_df):
        """Test filtering by alliance types."""
        edges = prepare_alliance_edges(
            sample_alliance_df,
            alliance_types=['defense']
        )

        assert all(edges['alliance_type'] == 'defense')

    def test_no_duplicates(self, sample_alliance_df):
        """Test that duplicate edges are removed (keeping strongest)."""
        edges = prepare_alliance_edges(sample_alliance_df)

        # Check no duplicate source-target pairs
        edge_pairs = edges[['source', 'target']].apply(tuple, axis=1)
        assert len(edge_pairs) == len(edge_pairs.unique())

    def test_vectorized_alliance_type(self):
        """Test that vectorized np.select correctly assigns alliance types."""
        df = pd.DataFrame({
            'ccode1': [1, 2, 3, 4, 5],
            'ccode2': [10, 20, 30, 40, 50],
            'state_name1': ['A', 'B', 'C', 'D', 'E'],
            'state_name2': ['X', 'Y', 'Z', 'W', 'V'],
            'dyad_st_year': [1900] * 5,
            'dyad_end_year': [1920] * 5,
            'defense': [1, 0, 0, 0, 0],
            'neutrality': [0, 1, 0, 0, 0],
            'nonaggression': [0, 0, 1, 0, 0],
            'entente': [0, 0, 0, 1, 0],
        })
        edges = prepare_alliance_edges(df)

        types = edges.set_index(['source', 'target'])['alliance_type'].to_dict()
        assert types.get((1, 10)) == 'defense'
        assert types.get((2, 20)) == 'neutrality'
        assert types.get((3, 30)) == 'nonaggression'
        assert types.get((4, 40)) == 'entente'


class TestPrepareTradeEdges:
    """Tests for prepare_trade_edges function."""

    def test_basic_preparation(self, sample_trade_df):
        """Test basic trade edge preparation."""
        edges = prepare_trade_edges(sample_trade_df, year=1910)

        assert 'source' in edges.columns
        assert 'target' in edges.columns
        assert 'weight' in edges.columns

    def test_total_trade_calculation(self, sample_trade_df):
        """Test that total trade is sum of flow1 and flow2."""
        edges = prepare_trade_edges(sample_trade_df, year=1910)

        # First row: flow1=1000, flow2=1200, total=2200
        first_edge = edges[
            (edges['source'] == 2) & (edges['target'] == 200)
        ]
        assert first_edge['weight'].values[0] == 2200

    def test_missing_value_handling(self):
        """Test that -9 (missing) values are treated as 0."""
        df = pd.DataFrame({
            'ccode1': [1, 2],
            'ccode2': [10, 20],
            'year': [1910, 1910],
            'importer1': ['A', 'B'],
            'importer2': ['X', 'Y'],
            'flow1': [100, -9],
            'flow2': [-9, 200],
        })
        edges = prepare_trade_edges(df, year=1910)

        # Row 1: 100 + 0 = 100
        # Row 2: 0 + 200 = 200
        assert edges[edges['source'] == 1]['weight'].values[0] == 100
        assert edges[edges['source'] == 2]['weight'].values[0] == 200

    def test_min_trade_filter(self, sample_trade_df):
        """Test filtering by minimum trade value."""
        edges_all = prepare_trade_edges(sample_trade_df, year=1910, min_trade=0)
        edges_filtered = prepare_trade_edges(sample_trade_df, year=1910, min_trade=1500)

        assert len(edges_filtered) < len(edges_all)

    def test_year_filtering(self, sample_trade_df):
        """Test filtering by specific year."""
        edges = prepare_trade_edges(sample_trade_df, year=1910)
        assert len(edges) == 5

        # Non-existent year should return empty
        edges_empty = prepare_trade_edges(sample_trade_df, year=1900)
        assert len(edges_empty) == 0
