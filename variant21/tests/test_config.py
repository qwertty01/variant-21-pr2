"""Tests for configuration loading."""

import pytest
from pathlib import Path

from src.config import ConfigError, load_config


def test_load_valid_config(tmp_path: Path):
    cfg_file = tmp_path / "cfg.xml"
    cfg_file.write_text(
        """<?xml version="1.0"?>
        <config>
            <package>requests</package>
            <repo_url>https://pypi.org/simple/</repo_url>
            <test_mode>false</test_mode>
            <version>2.31.0</version>
            <output_file>out</output_file>
            <max_depth>3</max_depth>
            <filter_substring>test</filter_substring>
        </config>
        """,
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg.package == "requests"
    assert cfg.test_mode is False
    assert cfg.max_depth == 3
    assert cfg.filter_substring == "test"


def test_missing_package(tmp_path: Path):
    cfg_file = tmp_path / "cfg.xml"
    cfg_file.write_text(
        """<?xml version="1.0"?>
        <config>
            <repo_url>https://example.com</repo_url>
            <test_mode>false</test_mode>
            <version>1.0</version>
            <output_file>out</output_file>
            <max_depth>2</max_depth>
        </config>
        """,
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="package"):
        load_config(cfg_file)


def test_invalid_max_depth(tmp_path: Path):
    cfg_file = tmp_path / "cfg.xml"
    cfg_file.write_text(
        """<?xml version="1.0"?>
        <config>
            <package>A</package>
            <repo_url>testdata/test_repo.txt</repo_url>
            <test_mode>true</test_mode>
            <version>1.0</version>
            <output_file>out</output_file>
            <max_depth>abc</max_depth>
        </config>
        """,
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="max_depth"):
        load_config(cfg_file)


def test_file_not_found():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/config.xml")
