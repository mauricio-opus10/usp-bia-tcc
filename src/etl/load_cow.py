"""
Funções para carregar dados do Correlates of War (COW)
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger('tcc_redes')

# Caminho base para dados brutos
DATA_RAW_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "cow"

# Caminhos alternativos para dados originais (Arquivo 2025)
ARQUIVO_2025_PATH = Path(__file__).parent.parent.parent.parent / "Arquivo 2025" / "Dados" / "COW"


def _resolve_data_path(primary_path: Path, fallback_path: Path, dataset_name: str) -> Path:
    """
    Resolve o caminho do arquivo de dados, tentando o primário e depois o fallback.

    Args:
        primary_path: Caminho preferencial (dentro do repositório)
        fallback_path: Caminho alternativo (Arquivo 2025)
        dataset_name: Nome do dataset para mensagem de erro

    Returns:
        Path do arquivo encontrado

    Raises:
        FileNotFoundError: Se o arquivo não for encontrado em nenhum dos caminhos
    """
    if primary_path.exists():
        return primary_path
    if fallback_path.exists():
        return fallback_path

    raise FileNotFoundError(
        f"Dataset '{dataset_name}' não encontrado.\n"
        f"Caminhos verificados:\n"
        f"  - {primary_path}\n"
        f"  - {fallback_path}\n"
        f"Verifique se os dados foram copiados corretamente para o repositório."
    )


def _safe_read_csv(file_path: Path, dataset_name: str, **kwargs) -> pd.DataFrame:
    """
    Lê arquivo CSV com tratamento de erros contextualizado.

    Args:
        file_path: Caminho do arquivo CSV
        dataset_name: Nome do dataset para mensagens de erro
        **kwargs: Argumentos adicionais para pd.read_csv

    Returns:
        DataFrame carregado

    Raises:
        RuntimeError: Se a leitura falhar com mensagem contextualizada
    """
    try:
        return pd.read_csv(file_path, **kwargs)
    except pd.errors.EmptyDataError:
        raise RuntimeError(f"Dataset '{dataset_name}' está vazio: {file_path}")
    except pd.errors.ParserError as e:
        raise RuntimeError(f"Erro de parse no dataset '{dataset_name}' ({file_path}): {e}") from e
    except UnicodeDecodeError as e:
        raise RuntimeError(f"Erro de encoding no dataset '{dataset_name}' ({file_path}): {e}") from e
    except Exception as e:
        raise RuntimeError(f"Falha ao carregar dataset '{dataset_name}' de {file_path}: {e}") from e


def load_alliances(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    source_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carrega dados de alianças formais do COW v4.1.

    Args:
        start_year: Ano inicial para filtro (inclusive)
        end_year: Ano final para filtro (inclusive)
        source_path: Caminho alternativo para o arquivo

    Returns:
        DataFrame com alianças entre díades de Estados
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "alliances" / "alliance_v4.1_by_dyad.csv",
            ARQUIVO_2025_PATH / "Alianças Formais (v4.1)" / "version4.1_csv" / "alliance_v4.1_by_dyad.csv",
            "COW Alliances v4.1"
        )
    else:
        file_path = source_path

    df = _safe_read_csv(file_path, "COW Alliances v4.1")

    # Filtrar por período se especificado
    if start_year is not None:
        df = df[df['dyad_st_year'] <= end_year] if end_year else df
        df = df[(df['dyad_end_year'].isna()) | (df['dyad_end_year'] >= start_year)]

    return df


def load_trade(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    source_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carrega dados de comércio bilateral do COW v4.0.

    Args:
        start_year: Ano inicial para filtro (inclusive)
        end_year: Ano final para filtro (inclusive)
        source_path: Caminho alternativo para o arquivo

    Returns:
        DataFrame com fluxos comerciais bilaterais por ano
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "trade" / "Dyadic_COW_4.0.csv",
            ARQUIVO_2025_PATH / "Comércio Internacional 1870-2014 (v4.0)" / "COW_Trade_4.0" / "Dyadic_COW_4.0.csv",
            "COW Trade v4.0"
        )
    else:
        file_path = source_path

    df = _safe_read_csv(file_path, "COW Trade v4.0")

    # Filtrar por período
    if start_year is not None and end_year is not None:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]

    return df


def load_mids(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    source_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carrega dados de Militarized Interstate Disputes (MIDs) v5.0.

    Args:
        start_year: Ano inicial para filtro (inclusive)
        end_year: Ano final para filtro (inclusive)
        source_path: Caminho alternativo para o arquivo

    Returns:
        DataFrame com disputas militarizadas
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "mids" / "MIDA 5.0.csv",
            ARQUIVO_2025_PATH / "Disputas Interestaduais Militarizadas (v5.0)" / "MID-5-Data-and-Supporting-Materials" / "MIDA 5.0.csv",
            "COW MIDs v5.0 (MIDA)"
        )
    else:
        file_path = source_path

    df = _safe_read_csv(file_path, "COW MIDs v5.0 (MIDA)")

    # Filtrar por período
    if start_year is not None and end_year is not None:
        df = df[(df['styear'] >= start_year) & (df['styear'] <= end_year)]

    return df


def load_mids_participants(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    source_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carrega dados de participantes de MIDs (MIDB) v5.0.

    Este dataset é necessário para construir a rede de disputas,
    pois contém os códigos dos países participantes de cada disputa.

    Args:
        start_year: Ano inicial para filtro (inclusive)
        end_year: Ano final para filtro (inclusive)
        source_path: Caminho alternativo para o arquivo

    Returns:
        DataFrame com participantes das disputas militarizadas

    Colunas principais:
        - dispnum: número da disputa (chave para MIDA)
        - ccode: código COW do país participante
        - stday, stmon, styear: data de início
        - endday, endmon, endyear: data de término
        - sidea: lado na disputa (1=Side A, 0=Side B)
        - fatality: nível de fatalidade
        - hostlev: nível de hostilidade
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "mids" / "MIDB 5.0.csv",
            ARQUIVO_2025_PATH / "Disputas Interestaduais Militarizadas (v5.0)" / "MID-5-Data-and-Supporting-Materials" / "MIDB 5.0.csv",
            "COW MIDs v5.0 (MIDB - Participants)"
        )
    else:
        file_path = source_path

    df = _safe_read_csv(file_path, "COW MIDs v5.0 (MIDB)")

    # Filtrar por período
    if start_year is not None and end_year is not None:
        df = df[(df['styear'] >= start_year) & (df['styear'] <= end_year)]

    return df


def load_nmc(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    source_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carrega dados de National Material Capabilities (NMC) v5.0.

    Args:
        start_year: Ano inicial para filtro (inclusive)
        end_year: Ano final para filtro (inclusive)
        source_path: Caminho alternativo para o arquivo

    Returns:
        DataFrame com capacidades materiais dos Estados (inclui CINC score)
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "nmc" / "NMC_5_0.csv",
            ARQUIVO_2025_PATH / "Capacidades Nacionais de Materiais (v6.0)" / "NMC_5_0" / "NMC_5_0.csv",
            "COW NMC v5.0"
        )
    else:
        file_path = source_path

    df = _safe_read_csv(file_path, "COW NMC v5.0")

    # Filtrar por período
    if start_year is not None and end_year is not None:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]

    return df


def load_diplomatic(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    source_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carrega dados de Intercâmbio Diplomático do COW v2006.1.

    Args:
        start_year: Ano inicial para filtro (inclusive)
        end_year: Ano final para filtro (inclusive)
        source_path: Caminho alternativo para o arquivo

    Returns:
        DataFrame com relações diplomáticas por díade e ano

    Colunas:
        - ccode1, ccode2: códigos dos países
        - year: ano
        - DR_at_1: nível de representação diplomática do país 1 no país 2
        - DR_at_2: nível de representação diplomática do país 2 no país 1
        - DE: 1 se há troca diplomática, 0 caso contrário

    Níveis de representação (DR_at):
        0 = nenhum
        1 = chargé d'affaires
        2 = ministro
        3 = embaixador
        9 = outro/desconhecido
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "diplomatic" / "Diplomatic_Exchange_2006v1.csv",
            ARQUIVO_2025_PATH / "Intercâmbio Diplomático 1817-2005 (v2006.1)" / "Diplomatic_Exchange_2006.1" / "Diplomatic_Exchange_2006v1.csv",
            "COW Diplomatic Exchange v2006.1"
        )
    else:
        file_path = source_path

    df = _safe_read_csv(file_path, "COW Diplomatic Exchange v2006.1")

    # Filtrar por período
    if start_year is not None and end_year is not None:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]

    return df


def load_country_codes(source_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Carrega tabela de códigos de países COW.

    Returns:
        DataFrame com códigos e nomes de países
    """
    if source_path is None:
        file_path = _resolve_data_path(
            DATA_RAW_PATH / "COW-country-codes.csv",
            ARQUIVO_2025_PATH / "COW-country-codes.csv",
            "COW Country Codes"
        )
    else:
        file_path = source_path

    return _safe_read_csv(file_path, "COW Country Codes")
