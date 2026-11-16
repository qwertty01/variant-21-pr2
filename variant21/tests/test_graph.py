"""Tests for graph construction and operations."""

from src.graph import DependencyGraph, build_graph, load_order


def test_build_simple_graph():
    full = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": [],
    }

    def fetch(pkg):
        return full.get(pkg, [])

    graph, cycles = build_graph(
        root="A",
        fetch_fn=fetch,
        max_depth=5,
        filter_substring="",
        test_mode=True,
        full_test_graph=full,
    )
    assert "A" in graph.nodes
    assert "B" in graph.nodes
    assert "D" in graph.nodes
    assert not cycles


def test_max_depth():
    full = {
        "A": ["B"],
        "B": ["C"],
        "C": ["D"],
        "D": [],
    }

    graph, _ = build_graph(
        root="A",
        fetch_fn=lambda p: full.get(p, []),
        max_depth=1,
        filter_substring="",
        test_mode=True,
        full_test_graph=full,
    )
    # depth 0 = A, depth 1 = B; C should not appear
    assert "A" in graph.nodes
    assert "B" in graph.nodes
    assert "C" not in graph.nodes


def test_filter_substring():
    full = {
        "A": ["B", "testlib", "C"],
        "B": [],
        "C": [],
        "testlib": [],
    }

    graph, _ = build_graph(
        root="A",
        fetch_fn=lambda p: full.get(p, []),
        max_depth=3,
        filter_substring="test",
        test_mode=True,
        full_test_graph=full,
    )
    assert "testlib" not in graph.nodes
    assert "B" in graph.nodes


def test_cycle_detection():
    full = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
    }

    graph, cycles = build_graph(
        root="A",
        fetch_fn=lambda p: full.get(p, []),
        max_depth=10,
        filter_substring="",
        test_mode=True,
        full_test_graph=full,
    )
    assert cycles  # at least one cycle reported


def test_load_order():
    g = DependencyGraph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    g.add_edge("C", "D")
    order = load_order(g, "A")
    # A must come first, D last
    assert order[0] == "A"
    assert order[-1] == "D"
    assert set(order) == {"A", "B", "C", "D"}
