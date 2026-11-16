#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

CONFIG="${1:-config.xml}"

echo "Running Dependency Graph Visualizer (Variant 21)"
echo "Config: $CONFIG"
echo

python -m src.main --config "$CONFIG"
