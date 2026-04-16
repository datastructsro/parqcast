#!/usr/bin/env bash
#
# Lint the parqcast Odoo addon against OCA standards.
#
# Runs:
#   1. pylint-odoo  — Odoo-specific lint (missing access rights, manifest keys, etc.)
#   2. Structure checks — required files and manifest fields
#   3. ruff — Python lint + format check
#
# Requires: uv (uses uvx for pylint-odoo)
#
# Usage:
#   bash scripts/oca_lint.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

ADDON_DIR="packages/parqcast"
ERRORS=0

header() { printf "\n=== %s ===\n" "$1"; }

# ---------- 1. Structure checks ----------
header "Structure checks"

REQUIRED_FILES=(
    "__init__.py"
    "__manifest__.py"
    "security/ir.model.access.csv"
    "static/description/icon.png"
    "readme/DESCRIPTION.md"
    "LICENSE"
    "tests/__init__.py"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$ADDON_DIR/$f" ]; then
        echo "  OK   $f"
    else
        echo "  MISS $f"
        ERRORS=$((ERRORS + 1))
    fi
done

# ---------- 2. Manifest field checks ----------
header "Manifest checks"

REQUIRED_KEYS=("name" "version" "license" "author" "summary" "depends" "website" "development_status")

for key in "${REQUIRED_KEYS[@]}"; do
    if grep -q "\"$key\"" "$ADDON_DIR/__manifest__.py"; then
        echo "  OK   $key"
    else
        echo "  MISS $key"
        ERRORS=$((ERRORS + 1))
    fi
done

# Version format check (should be X.0.Y.Z.W)
VERSION=$(python3 -c "
import ast, sys
with open('$ADDON_DIR/__manifest__.py') as f:
    text = f.read()
    # strip comment lines
    lines = [l for l in text.splitlines() if not l.strip().startswith('#')]
    d = ast.literal_eval('\n'.join(lines))
    print(d.get('version', ''))
")
if [[ "$VERSION" =~ ^[0-9]+\.0\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "  OK   version format: $VERSION"
else
    echo "  FAIL version format: $VERSION (expected X.0.Y.Z.W)"
    ERRORS=$((ERRORS + 1))
fi

# License header check
header "License headers"
for pyfile in $(find "$ADDON_DIR" -name '*.py' -not -path '*__pycache__*' | sort); do
    if head -2 "$pyfile" | grep -q "# License"; then
        echo "  OK   $(basename "$pyfile")"
    else
        echo "  MISS $(basename "$pyfile")"
        ERRORS=$((ERRORS + 1))
    fi
done

# ---------- 3. pylint-odoo ----------
header "pylint-odoo"

if uvx --from pylint-odoo pylint \
    --load-plugins=pylint_odoo \
    --class-naming-style=any \
    --disable=all \
    --enable=odoolint \
    "$ADDON_DIR" 2>/dev/null; then
    echo "  pylint-odoo: passed"
else
    echo "  pylint-odoo: issues found (see above)"
    ERRORS=$((ERRORS + 1))
fi

# ---------- 4. ruff ----------
header "ruff"

if uv run ruff check "$ADDON_DIR" --no-fix; then
    echo "  ruff check: passed"
else
    echo "  ruff check: issues found"
    ERRORS=$((ERRORS + 1))
fi

if uv run ruff format --check "$ADDON_DIR" 2>/dev/null; then
    echo "  ruff format: passed"
else
    echo "  ruff format: issues found"
    ERRORS=$((ERRORS + 1))
fi

# ---------- Summary ----------
header "Summary"
if [ "$ERRORS" -eq 0 ]; then
    echo "  All checks passed"
else
    echo "  $ERRORS issue(s) found"
    exit 1
fi
