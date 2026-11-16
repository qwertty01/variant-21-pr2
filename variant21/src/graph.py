"""Dependency graph construction and operations.

Uses iterative DFS (no recursion) as required by Variant 21.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


class DependencyGraph:
    """Directed graph of package dependencies."""

    def __init__(self) -> None:
        self.adj: Dict[str, List[str]] = defaultdict(list)
        self.nodes: Set[str] = set()

    def add_edge(self, src: str, dst: str) -> None:
        self.nodes.add(src)
        self.nodes.add(dst)
        if dst not in self.adj[src]:
            self.adj[src].append(dst)

    def add_node(self, node: str) -> None:
        self.nodes.add(node)
        if node not in self.adj:
            self.adj[node] = []

    def neighbors(self, node: str) -> List[str]:
        return list(self.adj.get(node, []))


def build_graph(
    root: str,
    fetch_fn,
    max_depth: int,
    filter_substring: str,
    test_mode: bool,
    full_test_graph: Optional[Dict[str, List[str]]] = None,
) -> Tuple[DependencyGraph, List[str]]:
    """Build transitive dependency graph using iterative DFS.

    Returns:
        (graph, cycles) where cycles is a list of detected cycle descriptions.
    """
    graph = DependencyGraph()
    graph.add_node(root)
    cycles: List[str] = []

    # stack items: (node, depth, path)
    stack: List[Tuple[str, int, Tuple[str, ...]]] = [(root, 0, (root,))]
    visited: Set[str] = set()

    while stack:
        node, depth, path = stack.pop()

        if node in visited:
            continue
        visited.add(node)

        if depth >= max_depth:
            continue

        # Obtain direct dependencies
        if test_mode and full_test_graph is not None:
            deps = full_test_graph.get(node, [])
        else:
            try:
                deps = fetch_fn(node)
            except Exception:
                deps = []

        for dep in deps:
            # Filter by substring
            if filter_substring and filter_substring.lower() in dep.lower():
                continue

            graph.add_edge(node, dep)

            # Cycle detection
            if dep in path:
                cycle_path = list(path) + [dep]
                cycles.append(" -> ".join(cycle_path))
                continue

            if dep not in visited:
                stack.append((dep, depth + 1, path + (dep,)))

    return graph, cycles


def load_order(graph: DependencyGraph, root: str) -> List[str]:
    """Compute a valid load order (topological) for the subgraph reachable from root.

    Uses Kahn's algorithm. Nodes involved in cycles are placed at the end.
    """
    # Build indegree for reachable nodes only
    reachable: Set[str] = set()
    q: deque[str] = deque([root])
    while q:
        n = q.popleft()
        if n in reachable:
            continue
        reachable.add(n)
        for neigh in graph.neighbors(n):
            q.append(neigh)

    indegree: Dict[str, int] = {n: 0 for n in reachable}
    for n in reachable:
        for neigh in graph.neighbors(n):
            if neigh in indegree:
                indegree[neigh] += 1

    # Kahn
    zero = deque([n for n in reachable if indegree[n] == 0])
    order: List[str] = []
    while zero:
        n = zero.popleft()
        order.append(n)
        for neigh in graph.neighbors(n):
            if neigh not in indegree:
                continue
            indegree[neigh] -= 1
            if indegree[neigh] == 0:
                zero.append(neigh)

    # Remaining nodes (cycles) appended
    remaining = [n for n in reachable if n not in order]
    order.extend(remaining)
    return order


def reverse_dependencies(graph: DependencyGraph, target: str) -> List[str]:
    """Return packages that depend on target (direct reverse edges)."""
    result = []
    for node, deps in graph.adj.items():
        if target in deps:
            result.append(node)
    return sorted(result)
