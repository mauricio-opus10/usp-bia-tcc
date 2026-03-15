"""
Módulo ETL - Extract, Transform, Load

Funções para carregar e processar dados das fontes:
- COW (Correlates of War)
- ATOP (Alliance Treaty Obligations and Provisions)
- Maddison Project Database
"""

from .load_cow import (
    load_alliances,
    load_trade,
    load_mids,
    load_mids_participants,
    load_nmc,
    load_diplomatic,
    load_country_codes,
)
from .transform import (
    filter_by_year,
    filter_by_cinc,
    filter_states_by_cinc,
    prepare_alliance_edges,
    prepare_trade_edges,
)

__all__ = [
    # Data loaders
    'load_alliances',
    'load_trade',
    'load_mids',
    'load_mids_participants',
    'load_nmc',
    'load_diplomatic',
    'load_country_codes',
    # Transformations
    'filter_by_year',
    'filter_by_cinc',
    'filter_states_by_cinc',
    'prepare_alliance_edges',
    'prepare_trade_edges',
]
