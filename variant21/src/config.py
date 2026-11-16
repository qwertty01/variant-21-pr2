"""XML configuration loader and validator."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    package: str
    repo_url: str
    test_mode: bool
    version: str
    output_file: str
    max_depth: int
    filter_substring: str

    def __str__(self) -> str:
        lines = [
            f"package = {self.package}",
            f"repo_url = {self.repo_url}",
            f"test_mode = {self.test_mode}",
            f"version = {self.version}",
            f"output_file = {self.output_file}",
            f"max_depth = {self.max_depth}",
            f"filter_substring = {self.filter_substring}",
        ]
        return "\n".join(lines)


class ConfigError(Exception):
    """Configuration validation error."""


def _get_text(root: ET.Element, tag: str, required: bool = True) -> str:
    elem = root.find(tag)
    if elem is None or elem.text is None:
        if required:
            raise ConfigError(f"Missing required parameter: {tag}")
        return ""
    return elem.text.strip()


def load_config(path: str | Path) -> Config:
    """Load and validate configuration from XML file."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ConfigError(f"Invalid XML: {exc}") from exc

    root = tree.getroot()
    if root.tag != "config":
        raise ConfigError("Root element must be <config>")

    package = _get_text(root, "package")
    if not package:
        raise ConfigError("Parameter 'package' must not be empty")

    repo_url = _get_text(root, "repo_url")
    if not repo_url:
        raise ConfigError("Parameter 'repo_url' must not be empty")

    test_mode_str = _get_text(root, "test_mode").lower()
    if test_mode_str not in ("true", "false", "1", "0", "yes", "no"):
        raise ConfigError(
            "Parameter 'test_mode' must be true/false (or 1/0/yes/no)"
        )
    test_mode = test_mode_str in ("true", "1", "yes")

    version = _get_text(root, "version")
    if not version:
        raise ConfigError("Parameter 'version' must not be empty")

    output_file = _get_text(root, "output_file")
    if not output_file:
        raise ConfigError("Parameter 'output_file' must not be empty")

    max_depth_str = _get_text(root, "max_depth")
    try:
        max_depth = int(max_depth_str)
    except ValueError as exc:
        raise ConfigError(
            f"Parameter 'max_depth' must be an integer, got: {max_depth_str}"
        ) from exc
    if max_depth < 0:
        raise ConfigError("Parameter 'max_depth' must be >= 0")

    filter_substring = _get_text(root, "filter_substring", required=False)

    return Config(
        package=package,
        repo_url=repo_url,
        test_mode=test_mode,
        version=version,
        output_file=output_file,
        max_depth=max_depth,
        filter_substring=filter_substring,
    )
