"""CLI entry point for Dependency Graph Visualizer (Variant 21)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .fetcher import FetchError, fetch_direct_dependencies, load_full_test_graph
from .graph import build_graph, load_order
from .visualizer import ascii_tree, render_svg, save_d2, to_d2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dependency Graph Visualizer (Variant 21)"
    )
    parser.add_argument(
        "--config",
        default="config.xml",
        help="Path to XML configuration file (default: config.xml)",
    )
    parser.add_argument(
        "--show-params",
        action="store_true",
        help="Print configuration parameters and exit (stage 1)",
    )
    parser.add_argument(
        "--show-direct",
        action="store_true",
        help="Print only direct dependencies (stage 2)",
    )
    parser.add_argument(
        "--show-load-order",
        action="store_true",
        help="Print load order of dependencies (stage 4)",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Also print ASCII tree",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # --- Stage 1: load & validate config ---
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    print("=== Configuration ===")
    print(cfg)
    print()

    if args.show_params:
        return 0

    # --- Stage 2: direct dependencies ---
    try:
        if cfg.test_mode:
            direct = fetch_direct_dependencies(
                cfg.package, cfg.version, cfg.repo_url, test_mode=True
            )
        else:
            direct = fetch_direct_dependencies(
                cfg.package, cfg.version, cfg.repo_url, test_mode=False
            )
    except FetchError as exc:
        print(f"Fetch error: {exc}", file=sys.stderr)
        return 1

    print(f"=== Direct dependencies of {cfg.package}=={cfg.version} ===")
    if direct:
        for d in direct:
            print(f"  - {d}")
    else:
        print("  (none)")
    print()

    if args.show_direct:
        return 0

    # Prepare fetch function / full graph for transitive build
    full_test_graph = None
    if cfg.test_mode:
        try:
            full_test_graph = load_full_test_graph(cfg.repo_url)
        except FetchError as exc:
            print(f"Fetch error: {exc}", file=sys.stderr)
            return 1

        def fetch_fn(pkg: str):
            return full_test_graph.get(pkg, [])
    else:
        def fetch_fn(pkg: str):
            # For real packages we only have version for the root;
            # transitive packages use latest / empty on error.
            try:
                return fetch_direct_dependencies(
                    pkg, "latest", cfg.repo_url, test_mode=False
                )
            except FetchError:
                return []

    # --- Stage 3: build graph (iterative DFS) ---
    graph, cycles = build_graph(
        root=cfg.package.upper() if cfg.test_mode else cfg.package,
        fetch_fn=fetch_fn,
        max_depth=cfg.max_depth,
        filter_substring=cfg.filter_substring,
        test_mode=cfg.test_mode,
        full_test_graph=full_test_graph,
    )

    print("=== Graph built ===")
    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {sum(len(v) for v in graph.adj.values())}")
    if cycles:
        print("Cycles detected:")
        for c in cycles:
            print(f"  {c}")
    else:
        print("No cycles detected.")
    print()

    # --- Stage 4: load order ---
    root_name = cfg.package.upper() if cfg.test_mode else cfg.package
    order = load_order(graph, root_name)
    print("=== Load order ===")
    for i, pkg in enumerate(order, 1):
        print(f"  {i}. {pkg}")
    print()

    if args.show_load_order:
        return 0

    # --- Stage 5: visualization ---
    d2_text = to_d2(graph, root_name)
    d2_path = save_d2(d2_text, cfg.output_file)
    print(f"D2 source written to: {d2_path}")

    svg_path = render_svg(d2_path, cfg.output_file)
    if svg_path:
        print(f"SVG image written to: {svg_path}")
    else:
        print(
            "Note: 'd2' CLI not found. Install from https://d2lang.com "
            "to render SVG automatically. D2 source is still available."
        )

    if args.ascii:
        print("\n=== ASCII tree ===")
        print(ascii_tree(graph, root_name, max_depth=cfg.max_depth))

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
