#!/usr/bin/env bash
#
# Generate README.rst from readme/ fragments using oca-gen-addon-readme.
#
# Requires: uv (uses uvx to run the tool without installing globally)
#
# Usage:
#   bash scripts/gen_readme.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

ADDON_DIR="packages/parqcast"

echo "=== Generating README.rst ==="
echo "  Addon: $ADDON_DIR"
echo ""

# oca-gen-addon-readme lives in the OCA/maintainer-tools repo on GitHub
uvx --from "git+https://github.com/OCA/maintainer-tools" oca-gen-addon-readme \
    --addon-dir "$ADDON_DIR" \
    --org-name datastructsro \
    --repo-name parqcast \
    --branch main

echo ""
echo "Done: $ADDON_DIR/README.rst"
