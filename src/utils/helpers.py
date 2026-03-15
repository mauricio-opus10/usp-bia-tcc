"""
Funções utilitárias gerais
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json


# =============================================================================
# CENTRALIZED CONSTANTS
# =============================================================================

# Alliance type weights (higher = stronger commitment)
ALLIANCE_WEIGHTS: Dict[str, int] = {
    'defense': 4,
    'neutrality': 3,
    'nonaggression': 2,
    'entente': 1
}

# Time windows for analysis
TIME_WINDOWS: Dict[str, Dict[str, int]] = {
    'pre_wwi': {'start': 1890, 'end': 1914},
    'pre_wwii': {'start': 1925, 'end': 1939}
}

# Default CINC threshold (0.1% of global capabilities)
DEFAULT_CINC_THRESHOLD: float = 0.001

# Major powers COW codes
MAJOR_POWERS: Dict[str, int] = {
    'GBR': 200,   # United Kingdom
    'FRN': 220,   # France
    'GMY': 255,   # Germany
    'AUH': 300,   # Austria-Hungary
    'RUS': 365,   # Russia
    'ITA': 325,   # Italy
    'USA': 2,     # United States
    'JPN': 740    # Japan
}

# Random seed for reproducibility
RANDOM_SEED: int = 42


def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).parent.parent.parent


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura logging para o projeto.

    Args:
        level: Nível de logging
        log_file: Caminho opcional para arquivo de log

    Returns:
        Logger configurado
    """
    logger = logging.getLogger('tcc_redes')
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Carrega configurações do projeto.

    Args:
        config_path: Caminho para arquivo de configuração JSON

    Returns:
        Dicionário de configuração
    """
    # Use centralized constants
    default_config = {
        'windows': TIME_WINDOWS,
        'cinc_threshold': DEFAULT_CINC_THRESHOLD,
        'alliance_weights': ALLIANCE_WEIGHTS,
        'major_powers': MAJOR_POWERS,
        'random_seed': RANDOM_SEED
    }

    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            default_config.update(user_config)

    return default_config


def ensure_dir(path: str) -> Path:
    """
    Garante que um diretório existe, criando se necessário.

    Args:
        path: Caminho do diretório

    Returns:
        Path do diretório
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def format_number(n: float, precision: int = 4) -> str:
    """Formata número com precisão especificada."""
    return f"{n:.{precision}f}"


def get_data_path(subdir: str = '') -> Path:
    """
    Retorna caminho para diretório de dados.

    Args:
        subdir: Subdiretório dentro de data/

    Returns:
        Path completo
    """
    root = get_project_root()
    data_path = root / 'data' / subdir
    return data_path


def get_output_path(filename: str = '') -> Path:
    """
    Retorna caminho para diretório de output.

    Args:
        filename: Nome do arquivo (opcional)

    Returns:
        Path completo
    """
    root = get_project_root()
    output_path = root / 'data' / 'output'
    output_path.mkdir(parents=True, exist_ok=True)

    if filename:
        return output_path / filename
    return output_path
