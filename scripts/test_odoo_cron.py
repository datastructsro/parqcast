"""
Test the parqcast cron export from within Odoo via XML-RPC.

This calls parqcast.cron.run_export() exactly as Odoo's ir.cron scheduler would.
Run with: python3 scripts/test_odoo_cron.py
"""

import pprint
import xmlrpc.client

URL = "http://127.0.0.1:8069"
DB = "thatoleg"
USER = "admin"
PASS = "admin"

# Authenticate
transport = xmlrpc.client.Transport()
transport.timeout = 600  # 10 minute timeout for long-running exports

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", transport=transport)
uid = common.authenticate(DB, USER, PASS, {})
print(f"Authenticated as uid={uid}")

# Call the cron method
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", transport=transport)

print("\nCalling parqcast.cron.run_export()...")
print("(This runs the full orchestrator pipeline inside Odoo's process)\n")

try:
    result = models.execute_kw(
        DB,
        uid,
        PASS,
        "parqcast.cron",
        "run_export",
        [],
    )
    print("=== Result ===")
    pprint.pprint(result)

    if isinstance(result, dict):
        state = result.get("state", "done" if "files" in result else "unknown")
        print(f"\nState: {state}")
        if "files" in result:
            print(f"Files: {len(result['files'])}")
            print(f"Errors: {result.get('errors', [])}")
            print(f"Duration: {result.get('total_duration_seconds', '?')}s")
            total_rows = sum(f.get("rows", 0) for f in result["files"])
            total_bytes = sum(f.get("bytes", 0) for f in result["files"])
            print(f"Total rows: {total_rows:,}")
            print(f"Total bytes: {total_bytes:,} ({total_bytes / 1024 / 1024:.1f} MB)")
        elif "pending" in result:
            print(f"Pending chunks: {result['pending']}")
            print("(Run again to continue — the orchestrator resumes from where it left off)")
except xmlrpc.client.Fault as e:
    print(f"XML-RPC Fault: {e.faultCode}")
    print(f"Message: {e.faultString}")
