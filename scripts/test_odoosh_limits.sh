#!/usr/bin/env bash
#
# Simulate Odoo.sh memory constraints for testing.
#
# Odoo.sh production defaults:
#   limit_memory_soft = 2048 MiB (worker recycles after request)
#   limit_memory_hard = 2560 MiB (worker killed immediately)
#
# This script sets RLIMIT_AS (address space) via Python's resource module
# before running the test suite. On Linux this is enforced; on macOS it's
# best-effort (kernel doesn't enforce RLIMIT_AS on Darwin).
#
# Usage:
#   ./scripts/test_odoosh_limits.sh                    # full suite
#   ./scripts/test_odoosh_limits.sh test_full_orchestrator_run  # single test
#

set -euo pipefail
cd "$(dirname "$0")/.."

SOFT_MB=2048
HARD_MB=2560
SOFT_BYTES=$((SOFT_MB * 1024 * 1024))
HARD_BYTES=$((HARD_MB * 1024 * 1024))

OS=$(uname -s)

echo "=== Odoo.sh Memory Constraint Test ==="
echo "  Soft limit: ${SOFT_MB} MiB"
echo "  Hard limit: ${HARD_MB} MiB"
echo "  Platform:   ${OS}"
echo ""

if [ "$OS" = "Darwin" ]; then
    echo "  WARNING: macOS does not enforce RLIMIT_AS. Memory limits are"
    echo "  advisory only. For accurate testing, use Linux or Docker."
    echo ""
fi

# Build the test selector
TEST_SELECTOR=""
if [ $# -gt 0 ]; then
    TEST_SELECTOR="-k $1"
fi

# Run tests with memory limits set via Python resource module
exec uv run python -c "
import resource
import subprocess
import sys
import os

soft = ${SOFT_BYTES}
hard = ${HARD_BYTES}

# Set address space limit (RLIMIT_AS)
try:
    resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
    current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
    print(f'  RLIMIT_AS set: soft={current_soft // (1024*1024)} MiB, hard={current_hard // (1024*1024)} MiB')
except (ValueError, OSError) as e:
    print(f'  RLIMIT_AS not available: {e}')

# Also set RSS limit (best-effort)
try:
    resource.setrlimit(resource.RLIMIT_RSS, (soft, hard))
    print(f'  RLIMIT_RSS set: soft={soft // (1024*1024)} MiB, hard={hard // (1024*1024)} MiB')
except (ValueError, OSError) as e:
    print(f'  RLIMIT_RSS not available: {e}')

print()

# Run pytest as subprocess (inherits limits)
# Skip test_run_all_compatible_collectors — it uses the non-streaming collect()
# path which loads 10M+ rows in-memory (intentionally tests backward compat,
# not Odoo.sh safety). The orchestrator test uses streaming.
cmd = [
    sys.executable, '-m', 'pytest',
    'tests/test_live_db.py',
    '-v', '-s',
    '--tb=short',
    '--deselect=tests/test_live_db.py::test_run_all_compatible_collectors',
]

# Append test selector if provided (overrides default deselect)
selector = '${TEST_SELECTOR}'.strip()
if selector:
    # When a specific test is selected, drop the deselect
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/test_live_db.py',
        '-v', '-s',
        '--tb=short',
    ]
    cmd.extend(selector.split())

print(f'  Running: {\" \".join(cmd)}')
print('=' * 60)
print()

result = subprocess.run(cmd)

# Report memory usage
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
peak_mb = usage.ru_maxrss
# On macOS ru_maxrss is in bytes; on Linux it's in KB
if sys.platform == 'darwin':
    peak_mb = peak_mb / (1024 * 1024)
else:
    peak_mb = peak_mb / 1024

print()
print('=' * 60)
print(f'  Peak RSS (children): {peak_mb:.0f} MiB')
print(f'  Odoo.sh soft limit:  ${SOFT_MB} MiB')
print(f'  Odoo.sh hard limit:  ${HARD_MB} MiB')

if peak_mb > ${HARD_MB}:
    print(f'  FAIL: Would be killed on Odoo.sh ({peak_mb:.0f} > ${HARD_MB} MiB)')
    sys.exit(1)
elif peak_mb > ${SOFT_MB}:
    print(f'  WARN: Would trigger worker recycle ({peak_mb:.0f} > ${SOFT_MB} MiB)')
else:
    print(f'  OK: Within Odoo.sh limits')

sys.exit(result.returncode)
"
