"""Tests for test-repository fetcher."""

from pathlib import Path

import pytest

from src.fetcher import FetchError, fetch_direct_dependencies, load_full_test_graph


def test_load_test_repo():
    repo = Path(__file__).resolve().parent.parent / "testdata" / "test_repo.txt"
    graph = load_full_test_graph(str(repo))
    assert "A" in graph
    assert "B" in graph["A"]
    assert "C" in graph["A"]
    assert graph["F"] == []


def test_fetch_direct_test_mode():
    repo = Path(__file__).resolve().parent.parent / "testdata" / "test_repo.txt"
    deps = fetch_direct_dependencies("A", "1.0", str(repo), test_mode=True)
    assert "B" in deps
    assert "C" in deps


def test_missing_package():
    repo = Path(__file__).resolve().parent.parent / "testdata" / "test_repo.txt"
    with pytest.raises(FetchError, match="not found"):
        fetch_direct_dependencies("ZZZ", "1.0", str(repo), test_mode=True)
