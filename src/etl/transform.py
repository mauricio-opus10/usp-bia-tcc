"""
Funções de transformação e limpeza de dados
"""

import pandas as pd
import numpy as np
from typing import List, Optional

from ..utils.helpers import ALLIANCE_WEIGHTS


def filter_by_year(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    year_column: str = 'year'
) -> pd.DataFrame:
    """
    Filtra DataFrame por intervalo de anos.

    Args:
        df: DataFrame a filtrar
        start_year: Ano inicial (inclusive)
        end_year: Ano final (inclusive)
        year_column: Nome da coluna de ano

    Returns:
        DataFrame filtrado
    """
    return df[(df[year_column] >= start_year) & (df[year_column] <= end_year)]


def filter_by_cinc(
    df: pd.DataFrame,
    nmc_df: pd.DataFrame,
    threshold: float = 0.001,
    ccode_column: str = 'ccode'
) -> pd.DataFrame:
    """
    Filtra Estados por capacidade material (CINC score).

    Args:
        df: DataFrame a filtrar
        nmc_df: DataFrame do NMC com scores CINC
        threshold: Limiar mínimo de CINC (default: 0.1%)
        ccode_column: Nome da coluna com código do país

    Returns:
        DataFrame filtrado para Estados acima do limiar
    """
    # Calcular média do CINC por país no período
    avg_cinc = nmc_df.groupby('ccode')['cinc'].mean().reset_index()
    relevant_states = avg_cinc[avg_cinc['cinc'] >= threshold]['ccode'].tolist()

    # Filtrar DataFrame original
    if ccode_column in df.columns:
        return df[df[ccode_column].isin(relevant_states)]
    elif 'ccode1' in df.columns and 'ccode2' in df.columns:
        # Para DataFrames de díades
        return df[
            (df['ccode1'].isin(relevant_states)) &
            (df['ccode2'].isin(relevant_states))
        ]
    else:
        raise ValueError(f"Coluna de código não encontrada: {ccode_column}")


def filter_states_by_cinc(
    nmc_df: pd.DataFrame,
    threshold: float = 0.01
) -> List[int]:
    """
    Retorna lista de códigos de Estados com CINC médio >= threshold.

    Args:
        nmc_df: DataFrame do NMC
        threshold: Limiar mínimo de CINC (default: 1%)

    Returns:
        Lista de códigos COW dos Estados acima do limiar
    """
    avg_cinc = nmc_df.groupby('ccode')['cinc'].mean().reset_index()
    return avg_cinc[avg_cinc['cinc'] >= threshold]['ccode'].tolist()


def prepare_alliance_edges(
    df: pd.DataFrame,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    alliance_types: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Prepara arestas de aliança para construção de grafo.

    Args:
        df: DataFrame de alianças (alliance_v4.1_by_dyad)
        start_year: Ano inicial do período (None = sem filtro)
        end_year: Ano final do período (None = sem filtro)
        alliance_types: Lista de tipos a incluir ['defense', 'neutrality', 'nonaggression', 'entente']

    Returns:
        DataFrame com colunas: source, target, weight, alliance_type
    """
    if alliance_types is None:
        alliance_types = ['defense', 'neutrality', 'nonaggression', 'entente']

    # Filtrar por período se especificado
    if start_year is not None and end_year is not None:
        df = df[
            (df['dyad_st_year'] <= end_year) &
            ((df['dyad_end_year'].isna()) | (df['dyad_end_year'] >= start_year))
        ]
    elif start_year is not None:
        df = df[
            ((df['dyad_end_year'].isna()) | (df['dyad_end_year'] >= start_year))
        ]
    elif end_year is not None:
        df = df[df['dyad_st_year'] <= end_year]

    # Criar coluna de tipo de aliança mais forte (vectorized for performance)
    df = df.copy()
    conditions = [
        df['defense'] == 1,
        df['neutrality'] == 1,
        df['nonaggression'] == 1,
        df['entente'] == 1
    ]
    choices = ['defense', 'neutrality', 'nonaggression', 'entente']
    df['alliance_type'] = np.select(conditions, choices, default='unknown')

    # Filtrar por tipos solicitados
    df = df[df['alliance_type'].isin(alliance_types)]

    # Calcular peso usando constantes centralizadas
    df['weight'] = df['alliance_type'].map(ALLIANCE_WEIGHTS)

    # Preparar formato de arestas
    edges = df[['ccode1', 'ccode2', 'state_name1', 'state_name2', 'weight', 'alliance_type']].copy()
    edges = edges.rename(columns={
        'ccode1': 'source',
        'ccode2': 'target',
        'state_name1': 'source_name',
        'state_name2': 'target_name'
    })

    # Remover duplicatas mantendo a aliança mais forte (maior peso)
    edges = edges.sort_values('weight', ascending=False)
    edges = edges.drop_duplicates(subset=['source', 'target'], keep='first')

    return edges


def prepare_trade_edges(
    df: pd.DataFrame,
    year: Optional[int] = None,
    min_trade: float = 0
) -> pd.DataFrame:
    """
    Prepara arestas de comércio para construção de grafo.

    Args:
        df: DataFrame de comércio (Dyadic_COW_4.0)
        year: Ano específico (obrigatório para comércio)
        min_trade: Valor mínimo de comércio para criar aresta

    Returns:
        DataFrame com colunas: source, target, weight (total trade)
    """
    if year is not None:
        df = df[df['year'] == year]

    df = df.copy()

    # Calcular comércio total (flow1 + flow2), tratando valores faltantes (-9)
    df['flow1'] = df['flow1'].replace(-9, 0)
    df['flow2'] = df['flow2'].replace(-9, 0)
    df['total_trade'] = df['flow1'] + df['flow2']

    # Filtrar por mínimo
    df = df[df['total_trade'] > min_trade]

    # Preparar formato de arestas
    edges = df[['ccode1', 'ccode2', 'importer1', 'importer2', 'total_trade', 'year']].copy()
    edges = edges.rename(columns={
        'ccode1': 'source',
        'ccode2': 'target',
        'importer1': 'source_name',
        'importer2': 'target_name',
        'total_trade': 'weight'
    })

    return edges
