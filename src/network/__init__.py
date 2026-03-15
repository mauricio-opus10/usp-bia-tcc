"""
Módulo Network - Construção e análise de redes

Funções para:
- Construir grafos NetworkX a partir dos dados
- Calcular métricas de centralidade e estrutura
- Detectar comunidades
"""

from .build_network import (
    build_alliance_network,
    build_trade_network,
    build_dispute_network,
    merge_networks,
)
from .metrics import (
    calculate_centrality_metrics,
    calculate_global_metrics,
    calculate_community_metrics,
    compare_networks,
)

__all__ = [
    # Network builders
    'build_alliance_network',
    'build_trade_network',
    'build_dispute_network',
    'merge_networks',
    # Metrics
    'calculate_centrality_metrics',
    'calculate_global_metrics',
    'calculate_community_metrics',
    'compare_networks',
]
