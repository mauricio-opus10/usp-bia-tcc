"""
Tests for src/utils module.

Tests utility functions and constants.
"""

import pytest
import logging
from pathlib import Path

from src.utils.helpers import (
    get_project_root,
    setup_logging,
    load_config,
    ensure_dir,
    format_number,
    get_data_path,
    get_output_path,
    ALLIANCE_WEIGHTS,
    TIME_WINDOWS,
    DEFAULT_CINC_THRESHOLD,
    MAJOR_POWERS,
    RANDOM_SEED,
)


class TestConstants:
    """Tests for centralized constants."""

    def test_alliance_weights_values(self):
        """Test that alliance weights have correct values."""
        assert ALLIANCE_WEIGHTS['defense'] == 4
        assert ALLIANCE_WEIGHTS['neutrality'] == 3
        assert ALLIANCE_WEIGHTS['nonaggression'] == 2
        assert ALLIANCE_WEIGHTS['entente'] == 1

    def test_alliance_weights_order(self):
        """Test that defense > neutrality > nonaggression > entente."""
        assert ALLIANCE_WEIGHTS['defense'] > ALLIANCE_WEIGHTS['neutrality']
        assert ALLIANCE_WEIGHTS['neutrality'] > ALLIANCE_WEIGHTS['nonaggression']
        assert ALLIANCE_WEIGHTS['nonaggression'] > ALLIANCE_WEIGHTS['entente']

    def test_time_windows_structure(self):
        """Test time windows structure."""
        assert 'pre_wwi' in TIME_WINDOWS
        assert 'pre_wwii' in TIME_WINDOWS

        assert TIME_WINDOWS['pre_wwi']['start'] == 1890
        assert TIME_WINDOWS['pre_wwi']['end'] == 1914
        assert TIME_WINDOWS['pre_wwii']['start'] == 1925
        assert TIME_WINDOWS['pre_wwii']['end'] == 1939

    def test_cinc_threshold(self):
        """Test default CINC threshold is 0.1%."""
        assert DEFAULT_CINC_THRESHOLD == 0.001

    def test_major_powers(self):
        """Test major powers codes."""
        assert MAJOR_POWERS['USA'] == 2
        assert MAJOR_POWERS['GBR'] == 200
        assert MAJOR_POWERS['FRN'] == 220
        assert MAJOR_POWERS['GMY'] == 255
        assert MAJOR_POWERS['RUS'] == 365

    def test_random_seed(self):
        """Test random seed is set for reproducibility."""
        assert RANDOM_SEED == 42


class TestGetProjectRoot:
    """Tests for get_project_root function."""

    def test_returns_path(self):
        """Test that function returns a Path object."""
        root = get_project_root()

        assert isinstance(root, Path)

    def test_path_exists(self):
        """Test that returned path exists."""
        root = get_project_root()

        assert root.exists()

    def test_contains_src(self):
        """Test that project root contains src directory."""
        root = get_project_root()

        assert (root / 'src').exists()


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_returns_logger(self):
        """Test that function returns a Logger object."""
        logger = setup_logging()

        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        """Test that logger has correct name."""
        logger = setup_logging()

        assert logger.name == 'tcc_redes'

    def test_log_level(self):
        """Test setting different log levels."""
        logger = setup_logging(level=logging.DEBUG)

        assert logger.level == logging.DEBUG

    def test_file_handler(self, tmp_path):
        """Test adding file handler."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file))

        # Log something
        logger.info("Test message")

        # File handler should be added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        config = load_config()

        assert isinstance(config, dict)

    def test_default_values(self):
        """Test that default values are present."""
        config = load_config()

        assert 'windows' in config
        assert 'cinc_threshold' in config
        assert 'alliance_weights' in config
        assert 'random_seed' in config

    def test_uses_centralized_constants(self):
        """Test that config uses centralized constants."""
        config = load_config()

        assert config['alliance_weights'] == ALLIANCE_WEIGHTS
        assert config['windows'] == TIME_WINDOWS
        assert config['random_seed'] == RANDOM_SEED

    def test_custom_config_file(self, tmp_path):
        """Test loading custom config file."""
        import json

        config_file = tmp_path / "config.json"
        custom_config = {'custom_key': 'custom_value'}
        config_file.write_text(json.dumps(custom_config))

        config = load_config(str(config_file))

        assert 'custom_key' in config
        assert config['custom_key'] == 'custom_value'

    def test_nonexistent_config_file(self):
        """Test that nonexistent config file uses defaults."""
        config = load_config('/nonexistent/path/config.json')

        # Should still return defaults
        assert 'windows' in config


class TestEnsureDir:
    """Tests for ensure_dir function."""

    def test_creates_directory(self, tmp_path):
        """Test that directory is created."""
        new_dir = tmp_path / "new_directory"
        result = ensure_dir(str(new_dir))

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_returns_path(self, tmp_path):
        """Test that function returns Path object."""
        new_dir = tmp_path / "another_dir"
        result = ensure_dir(str(new_dir))

        assert isinstance(result, Path)
        assert result == new_dir

    def test_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        nested = tmp_path / "a" / "b" / "c"
        ensure_dir(str(nested))

        assert nested.exists()

    def test_existing_directory(self, tmp_path):
        """Test that existing directory doesn't cause error."""
        existing = tmp_path / "existing"
        existing.mkdir()

        # Should not raise
        ensure_dir(str(existing))
        assert existing.exists()


class TestFormatNumber:
    """Tests for format_number function."""

    def test_default_precision(self):
        """Test default 4 decimal places."""
        result = format_number(3.14159265)

        assert result == "3.1416"

    def test_custom_precision(self):
        """Test custom precision."""
        result = format_number(3.14159265, precision=2)

        assert result == "3.14"

    def test_integer_input(self):
        """Test with integer input."""
        result = format_number(42, precision=2)

        assert result == "42.00"

    def test_small_numbers(self):
        """Test small numbers."""
        result = format_number(0.001234, precision=4)

        assert result == "0.0012"


class TestGetDataPath:
    """Tests for get_data_path function."""

    def test_returns_path(self):
        """Test that function returns Path object."""
        path = get_data_path()

        assert isinstance(path, Path)

    def test_base_data_path(self):
        """Test base data path without subdir."""
        path = get_data_path()

        assert path.name == 'data'

    def test_with_subdir(self):
        """Test data path with subdirectory."""
        path = get_data_path('raw')

        assert path.name == 'raw'
        assert 'data' in str(path)


class TestGetOutputPath:
    """Tests for get_output_path function."""

    def test_returns_path(self):
        """Test that function returns Path object."""
        path = get_output_path()

        assert isinstance(path, Path)

    def test_output_directory(self):
        """Test output directory path."""
        path = get_output_path()

        assert path.name == 'output'
        assert 'data' in str(path)

    def test_with_filename(self):
        """Test output path with filename."""
        path = get_output_path('test.csv')

        assert path.name == 'test.csv'
        assert 'output' in str(path)

    def test_creates_directory(self):
        """Test that output directory is created if needed."""
        path = get_output_path()

        # Directory should exist (function creates it)
        assert path.exists() or path.parent.exists()
