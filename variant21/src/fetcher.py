"""Dependency data fetcher for pip packages and test repositories.

Does NOT use package managers or third-party dependency libraries.
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional


class FetchError(Exception):
    """Error while fetching package metadata."""


def fetch_direct_dependencies(
    package: str,
    version: str,
    repo_url: str,
    test_mode: bool,
) -> List[str]:
    """Return list of direct dependency names for the given package version."""
    if test_mode:
        return _fetch_from_test_repo(package, repo_url)
    return _fetch_from_pypi(package, version, repo_url)


def _fetch_from_test_repo(package: str, repo_path: str) -> List[str]:
    """Parse test repository file.

    Format:
        PACKAGE -> DEP1, DEP2, ...
    """
    path = Path(repo_path)
    if not path.exists():
        raise FetchError(f"Test repository file not found: {repo_path}")

    graph: Dict[str, List[str]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                continue
            left, right = line.split("->", 1)
            pkg = left.strip().upper()
            deps_str = right.strip()
            if not deps_str:
                graph[pkg] = []
            else:
                deps = [d.strip().upper() for d in deps_str.split(",") if d.strip()]
                graph[pkg] = deps

    package = package.upper()
    if package not in graph:
        raise FetchError(f"Package '{package}' not found in test repository")
    return graph[package]


def _fetch_from_pypi(package: str, version: str, repo_url: str) -> List[str]:
    """Fetch package metadata from PyPI JSON API (public, no auth).

    Uses only urllib (stdlib). Does not invoke pip.
    """
    # Normalize package name for URL (PEP 503)
    name = package.lower().replace("_", "-")
    # Prefer the simple JSON endpoint
    url = f"https://pypi.org/pypi/{name}/{version}/json"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FetchError(
                f"Package '{package}' version '{version}' not found on PyPI"
            ) from exc
        raise FetchError(f"HTTP error while fetching metadata: {exc}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FetchError(f"Invalid JSON from PyPI: {exc}") from exc

    requires = data.get("info", {}).get("requires_dist") or []
    deps: List[str] = []
    for req in requires:
        if not req:
            continue
        # Skip environment markers that make the dep optional for us
        # Simple parse: take name before any version specifier or marker
        name_part = re.split(r"[;<>=!~(\s]", req, maxsplit=1)[0].strip()
        if name_part and name_part.lower() != package.lower():
            deps.append(name_part)
    return deps


def load_full_test_graph(repo_path: str) -> Dict[str, List[str]]:
    """Load entire test repository as adjacency list."""
    path = Path(repo_path)
    if not path.exists():
        raise FetchError(f"Test repository file not found: {repo_path}")

    graph: Dict[str, List[str]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                continue
            left, right = line.split("->", 1)
            pkg = left.strip().upper()
            deps_str = right.strip()
            if not deps_str:
                graph[pkg] = []
            else:
                deps = [d.strip().upper() for d in deps_str.split(",") if d.strip()]
                graph[pkg] = deps
    return graph
