"""Graph visualization: D2 language + SVG + ASCII tree."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

from .graph import DependencyGraph


def to_d2(graph: DependencyGraph, root: str) -> str:
    """Generate D2 diagram text from the dependency graph."""
    lines: List[str] = [
        f"# Dependency graph for {root}",
        "direction: down",
        "",
    ]

    # Declare nodes with labels
    for node in sorted(graph.nodes):
        safe = _safe_id(node)
        lines.append(f'{safe}: "{node}"')

    lines.append("")

    # Edges
    seen_edges: Set[tuple] = set()
    for src, deps in graph.adj.items():
        for dst in deps:
            edge = (src, dst)
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            lines.append(f"{_safe_id(src)} -> {_safe_id(dst)}")

    return "\n".join(lines) + "\n"


def _safe_id(name: str) -> str:
    """Make a valid D2 identifier."""
    return (
        name.replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
        .replace("[", "")
        .replace("]", "")
    )


def save_d2(d2_text: str, output_base: str) -> Path:
    """Write D2 source to file. Returns path to .d2 file."""
    path = Path(f"{output_base}.d2")
    path.write_text(d2_text, encoding="utf-8")
    return path


def render_svg(d2_path: Path, output_base: str) -> Optional[Path]:
    """Try to render SVG using the `d2` CLI if available.

    Returns path to SVG or None if d2 is not installed.
    """
    d2_bin = shutil.which("d2")
    if not d2_bin:
        return None

    svg_path = Path(f"{output_base}.svg")
    try:
        subprocess.run(
            [d2_bin, str(d2_path), str(svg_path)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return svg_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None


def ascii_tree(graph: DependencyGraph, root: str, max_depth: int = 10) -> str:
    """Produce a simple ASCII tree representation."""
    lines: List[str] = []

    def _walk(node: str, prefix: str, depth: int, visited: Set[str]) -> None:
        if depth > max_depth:
            return
        marker = " (cycle)" if node in visited else ""
        lines.append(f"{prefix}{node}{marker}")
        if node in visited:
            return
        visited = visited | {node}
        children = graph.neighbors(node)
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            new_prefix = prefix + ("    " if is_last else "│   ")
            branch = "└── " if is_last else "├── "
            _walk(child, prefix + branch, depth + 1, visited)

    _walk(root, "", 0, set())
    return "\n".join(lines)
