#!/usr/bin/env bash
#
# Generate i18n/parqcast.pot from Python and XML source files.
#
# This uses xgettext for Python strings and a lightweight XML extractor
# for Odoo view attributes (string=, help=, confirm=).
#
# For full accuracy, use Odoo's built-in i18n export instead:
#   Settings → Translations → Export Translation → parqcast → PO File
#
# Usage:
#   bash scripts/gen_pot.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

ADDON_DIR="packages/parqcast"
POT_FILE="$ADDON_DIR/i18n/parqcast.pot"

mkdir -p "$ADDON_DIR/i18n"

echo "=== Generating $POT_FILE ==="

# Step 1: Extract from Python files
PY_POT=$(mktemp)
find "$ADDON_DIR" -name '*.py' -not -path '*__pycache__*' | sort | \
    xargs xgettext \
        --language=Python \
        --keyword=_ \
        --from-code=UTF-8 \
        --no-wrap \
        --sort-output \
        --package-name=parqcast \
        --package-version=19.0.1.0.0 \
        --output="$PY_POT" 2>/dev/null || true

echo "  Python strings extracted"

# Step 2: Extract translatable attributes from XML files
XML_POT=$(mktemp)
python3 - "$ADDON_DIR" "$XML_POT" <<'PYEOF'
import sys, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone

addon_dir = sys.argv[1]
output = sys.argv[2]

# Attributes that carry translatable strings in Odoo XML
ATTRS = ("string", "help", "confirm", "placeholder", "sum", "avg")
entries = {}  # msgid -> set of file:line references

for root, dirs, files in os.walk(addon_dir):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fname in sorted(files):
        if not fname.endswith(".xml"):
            continue
        fpath = os.path.join(root, fname)
        relpath = os.path.relpath(fpath)
        try:
            tree = ET.parse(fpath)
        except ET.ParseError:
            continue
        for elem in tree.iter():
            for attr in ATTRS:
                val = elem.get(attr)
                if val and not val.startswith("%(") and len(val) > 1:
                    entries.setdefault(val, set()).add(relpath)
            # <field name="name">Text</field> inside ir.ui.view records
            if elem.tag == "field" and elem.get("name") == "name" and elem.text:
                text = elem.text.strip()
                if text and not text.startswith("parqcast.") and not text.startswith("res."):
                    entries.setdefault(text, set()).add(relpath)

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M+0000")
with open(output, "w") as f:
    f.write(f'# Translation template for parqcast.\n')
    f.write(f'# Copyright 2025 DataStruct s.r.o.\n')
    f.write(f'# This file is distributed under the same license as the parqcast package.\n')
    f.write(f'#\n')
    f.write(f'msgid ""\n')
    f.write(f'msgstr ""\n')
    f.write(f'"Project-Id-Version: parqcast 19.0.1.0.0\\n"\n')
    f.write(f'"Report-Msgid-Bugs-To: \\n"\n')
    f.write(f'"POT-Creation-Date: {now}\\n"\n')
    f.write(f'"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n')
    f.write(f'"Last-Translator: \\n"\n')
    f.write(f'"Language-Team: \\n"\n')
    f.write(f'"MIME-Version: 1.0\\n"\n')
    f.write(f'"Content-Type: text/plain; charset=UTF-8\\n"\n')
    f.write(f'"Content-Transfer-Encoding: 8bit\\n"\n')
    f.write(f'\n')
    for msgid in sorted(entries):
        refs = ", ".join(sorted(entries[msgid]))
        escaped = msgid.replace("\\", "\\\\").replace('"', '\\"')
        f.write(f'#: {refs}\n')
        f.write(f'msgid "{escaped}"\n')
        f.write(f'msgstr ""\n\n')

print(f"  XML strings extracted ({len(entries)} entries)")
PYEOF

# Step 3: Merge Python + XML into final .pot
if [ -s "$PY_POT" ] && [ -s "$XML_POT" ]; then
    msgcat --no-wrap --sort-output "$PY_POT" "$XML_POT" -o "$POT_FILE" 2>/dev/null || \
        cat "$PY_POT" "$XML_POT" > "$POT_FILE"
elif [ -s "$PY_POT" ]; then
    cp "$PY_POT" "$POT_FILE"
elif [ -s "$XML_POT" ]; then
    cp "$XML_POT" "$POT_FILE"
fi

rm -f "$PY_POT" "$XML_POT"

ENTRIES=$(grep -c '^msgid ' "$POT_FILE" 2>/dev/null || echo 0)
echo ""
echo "Done: $POT_FILE ($ENTRIES msgid entries)"
