#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Odoo 19 + Parqcast local dev runner
# ============================================
#
# First run:  bash scripts/olegrunit.sh --setup
# Start Odoo: bash scripts/olegrunit.sh
# Update addon: bash scripts/olegrunit.sh -u parqcast

ODOO_DIR="$HOME/partneship/odoo/odoo"
PARQCAST_ADDON="$(cd "$(dirname "$0")/.." && pwd)/packages"
VENV_DIR="$ODOO_DIR/.venv"
DB_NAME="thatoleg"
PORT=8069

# -- Setup venv + deps (run once) --
if [ "${1:-}" = "--setup" ]; then
    echo "=== Setting up Odoo 19 venv ==="

    # System deps (macOS)
    echo "[1/4] Checking brew deps..."
    for pkg in postgresql@16 libxml2 libxslt openssl libffi; do
        brew list "$pkg" &>/dev/null || brew install "$pkg"
    done

    # Create venv with Python 3.13 (Odoo 19 requires 3.10-3.13, greenlet breaks on 3.14)
    echo "[2/4] Creating venv at $VENV_DIR..."
    python3.13 -m venv "$VENV_DIR"

    echo "[3/4] Installing Odoo requirements..."
    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
    "$VENV_DIR/bin/pip" install -r "$ODOO_DIR/requirements.txt"

    # Install parqcast packages so Odoo can import them
    echo "[4/4] Installing parqcast packages into Odoo venv..."
    PARQCAST_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    "$VENV_DIR/bin/pip" install -e "$PARQCAST_ROOT/packages/parqcast-core"
    "$VENV_DIR/bin/pip" install -e "$PARQCAST_ROOT/packages/parqcast-collectors"
    "$VENV_DIR/bin/pip" install -e "$PARQCAST_ROOT/packages/parqcast-ingesters"

    echo ""
    echo "=== Setup complete ==="
    echo "Run: bash scripts/olegrunit.sh"
    exit 0
fi

# -- Check venv exists --
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "ERROR: No venv at $VENV_DIR"
    echo "Run first: bash scripts/olegrunit.sh --setup"
    exit 1
fi

# -- Start Odoo --
echo "Starting Odoo 19 on :$PORT (db=$DB_NAME)"
echo "  Addons: $ODOO_DIR/addons + $PARQCAST_ADDON"
echo ""

cd "$ODOO_DIR"
exec "$VENV_DIR/bin/python" odoo-bin \
    -d "$DB_NAME" \
    --addons-path="addons,$PARQCAST_ADDON" \
    -p "$PORT" \
    --workers=2 \
    --limit-time-real=600 \
    --limit-time-cpu=540 \
    "$@"
