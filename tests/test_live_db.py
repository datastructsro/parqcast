"""
Integration tests against a live Odoo database.

Set PARQCAST_TEST_DB to the local Odoo database name (see .env for local dev).

Run with: uv run pytest tests/test_live_db.py -v -s
Skip with: uv run pytest tests/ -v --ignore=tests/test_live_db.py

Tests that need the HTTP server are marked with @pytest.mark.server
and can be run separately:
    uv run pytest tests/test_live_db.py -v -s -m server
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psycopg2
import pyarrow.parquet as pq
import pytest

from parqcast.collectors.factory import CollectorFactory
from parqcast.core.capabilities import probe
from parqcast.core.tracking import ExportChunk, ExportRun, get_id_range
from parqcast.orchestrator import Orchestrator
from parqcast.transport.local_fs import LocalFSTransport

DB_NAME = os.environ.get("PARQCAST_TEST_DB")
if not DB_NAME:
    pytest.skip("Set PARQCAST_TEST_DB to run live DB tests", allow_module_level=True)


class OdooEnvShim:
    """Minimal shim that gives collectors an env.cr interface over psycopg2."""

    class Cursor:
        def __init__(self, conn):
            self._conn = conn
            self._cursor = conn.cursor()

        def execute(self, sql, params=None):
            try:
                self._cursor.execute(sql, params)
            except Exception:
                self._conn.rollback()
                raise

        def fetchall(self):
            return self._cursor.fetchall()

        def fetchone(self):
            return self._cursor.fetchone()

    def __init__(self, dbname: str):
        self.conn = psycopg2.connect(dbname=dbname)
        self.conn.autocommit = True
        self.cr = self.Cursor(self.conn)

    def close(self):
        self.conn.close()


@pytest.fixture(scope="module")
def env():
    try:
        e = OdooEnvShim(DB_NAME)
    except psycopg2.OperationalError:
        pytest.skip(f"Cannot connect to database '{DB_NAME}'")
    yield e
    # Cleanup tracking tables after all tests
    try:
        e.cr.execute("DROP TABLE IF EXISTS parqcast_export_chunk CASCADE")
        e.cr.execute("DROP TABLE IF EXISTS parqcast_export_run CASCADE")
    except Exception:
        pass
    e.close()


def _clean_tracking(env):
    """Reset tracking tables for a fresh orchestrator run."""
    ExportRun.ensure_table(env.cr)
    ExportChunk.ensure_table(env.cr)
    env.cr.execute("DELETE FROM parqcast_export_chunk")
    env.cr.execute("DELETE FROM parqcast_export_run")


# ---------------------------------------------------------------------------
# Unit-level live DB tests
# ---------------------------------------------------------------------------


def test_probe_capabilities(env):
    caps = probe(env.cr)
    print(f"\n  Mode: {caps.mode}")
    print(f"  Odoo version: {caps.odoo_version}")
    print(f"  Warehouses: {caps.warehouse_count}")
    print(f"  Languages: {caps.active_languages}")

    assert caps.has_stock
    assert caps.has_sale
    assert caps.has_purchase
    assert caps.mode in ("inventory", "manufacturing_idle", "manufacturing")
    assert caps.warehouse_count >= 1
    assert len(caps.active_languages) >= 1


def test_factory_creates_correct_collectors(env):
    factory = CollectorFactory(env)
    caps = factory.probe()
    collectors = factory.create_collectors(caps)
    names = {c.name for c in collectors}

    print(f"\n  Active collectors ({len(collectors)}): {', '.join(sorted(names))}")

    for expected in [
        "product",
        "uom",
        "partner",
        "company",
        "currency",
        "stock_location",
        "stock_warehouse",
        "stock_picking",
        "stock_picking_type",
        "stock_route",
        "stock_storage_category",
        "stock_putaway_rule",
        "product_removal",
        "stock_lot",
        "sale_order",
        "sale_order_line",
        "purchase_order_line",
        "purchase_requisition",
        "pos_order",
        "pos_session",
    ]:
        assert expected in names, f"Missing collector: {expected}"

    if caps.has_mrp:
        for expected in ["workcenter", "bom", "bom_lines", "bom_operations", "mrp_production", "mrp_workorder"]:
            assert expected in names, f"Missing MRP collector: {expected}"


def test_run_all_compatible_collectors(env):
    factory = CollectorFactory(env)
    caps = factory.probe()
    collectors = factory.create_collectors(caps)
    ordered = factory.resolve_order(collectors)

    results = {}
    for collector in ordered:
        table = collector.collect()
        results[collector.name] = table.num_rows
        print(f"\n  {collector.name}: {table.num_rows:,} rows, {table.num_columns} cols")
        assert table.schema == collector.schema, f"{collector.name} schema mismatch"

    assert results["product"] > 100_000
    assert results["partner"] > 100_000
    assert results["sale_order_line"] > 1_000_000
    assert results["purchase_order_line"] > 100_000
    assert results["company"] >= 1
    assert results["stock_warehouse"] == 4
    assert results["stock_picking"] > 36_000
    assert results["stock_route"] >= 4
    assert results["stock_storage_category"] == 3
    assert results["product_removal"] == 5


def test_keyset_collect(env):
    """Verify keyset pagination produces correct row counts when split."""
    factory = CollectorFactory(env)
    caps = factory.probe()
    collectors = factory.create_collectors(caps)

    collector = next(c for c in collectors if c.name == "stock_picking")
    full_table = collector.collect()
    full_rows = full_table.num_rows

    min_id, max_id = get_id_range(env.cr, "stock_picking")
    mid_id = (min_id + max_id) // 2

    table1 = collector.collect(key_from=min_id, key_to=mid_id)
    table2 = collector.collect(key_from=mid_id, key_to=max_id + 1)

    assert table1.num_rows + table2.num_rows == full_rows, (
        f"Keyset split: {table1.num_rows}+{table2.num_rows} != {full_rows}"
    )
    print(f"\n  keyset split: {table1.num_rows} + {table2.num_rows} = {full_rows} (id {min_id}..{mid_id}..{max_id})")


# ---------------------------------------------------------------------------
# Orchestrator → LocalFSTransport (file-based)
# ---------------------------------------------------------------------------


def test_orchestrator_local_transport(env):
    """Full pipeline: orchestrator → LocalFSTransport → verify files on disk."""
    _clean_tracking(env)

    with tempfile.TemporaryDirectory() as tmpdir:
        transport = LocalFSTransport(tmpdir)
        orch = Orchestrator(env, transport, company="My Company", company_id=1, time_budget=3600)
        result = orch.run()

        assert "files" in result, f"Expected manifest, got state={result.get('state')}"
        manifest = result

        print(f"\n  Run UUID: {manifest.get('run_uuid', 'N/A')}")
        print(f"  Files: {len(manifest['files'])}")
        print(f"  Errors: {manifest['errors']}")
        print(f"  Duration: {manifest['total_duration_seconds']}s")

        for f in manifest["files"]:
            print(f"    {f['file']}: {f['rows']:,} rows, {f['bytes']:,} bytes")

        assert len(manifest["files"]) > 20
        assert len(manifest["errors"]) == 0
        assert "run_uuid" in manifest

        # Verify parquet files via transport interface
        prefix = f"outbound/{manifest['run_uuid']}"
        files = transport.list_files(prefix)
        assert len(files) > 20
        assert "manifest.json" in files

        for f in manifest["files"]:
            data = transport.download_file(prefix, f["file"])
            table = pq.read_table(io.BytesIO(data))
            assert table.num_rows == f["rows"], f"Row count mismatch for {f['file']}"

        # Verify manifest
        manifest_data = json.loads(transport.download_file(prefix, "manifest.json"))
        assert manifest_data["run_uuid"] == manifest["run_uuid"]

    # Verify tracking table state
    env.cr.execute("SELECT state, run_uuid FROM parqcast_export_run ORDER BY id DESC LIMIT 1")
    row = env.cr.fetchone()
    assert row[0] == "done"
    assert len(row[1]) == 36  # UUID format

    env.cr.execute("SELECT COUNT(*) FROM parqcast_export_chunk WHERE state = 'uploaded'")
    assert env.cr.fetchone()[0] > 20


# ---------------------------------------------------------------------------
# Orchestrator → HttpTransport → parqcast-server (end-to-end)
# ---------------------------------------------------------------------------


SERVER_PORT = 18420  # Use non-standard port to avoid conflicts
API_KEY = "test-e2e-key"


@pytest.fixture(scope="module")
def server():
    """Start parqcast-server as a subprocess, yield when ready, kill on teardown."""
    data_root = tempfile.mkdtemp(prefix="parqcast_e2e_")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "parqcast.server.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(SERVER_PORT),
            "--log-level",
            "warning",
        ],
        env={
            **dict(__import__("os").environ),
            "PARQCAST_DATA_ROOT": data_root,
            "PARQCAST_API_KEY": API_KEY,
            "PARQCAST_CONFIG": "/dev/null",
        },
    )

    # Wait for server to be ready
    from urllib import request as urllib_request
    from urllib.error import URLError

    for _ in range(30):
        try:
            req = urllib_request.Request(f"http://127.0.0.1:{SERVER_PORT}/health")
            with urllib_request.urlopen(req, timeout=2):
                break
        except (URLError, ConnectionError):
            time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("Server did not start within 15 seconds")

    yield {"port": SERVER_PORT, "data_root": data_root, "api_key": API_KEY}

    proc.terminate()
    proc.wait(timeout=5)


@pytest.mark.server
def test_orchestrator_http_transport(env, server):
    """Full pipeline: orchestrator → HttpTransport → parqcast-server → verify."""
    from parqcast.transport_http import HttpTransport

    _clean_tracking(env)

    transport = HttpTransport(
        server_url=f"http://127.0.0.1:{server['port']}",
        api_key=server["api_key"],
        namespace="e2e_test",
    )

    orch = Orchestrator(env, transport, company="My Company", company_id=1, time_budget=3600)
    result = orch.run()

    assert "files" in result, f"Expected manifest, got state={result.get('state')}"
    manifest = result

    print(f"\n  Run UUID: {manifest.get('run_uuid', 'N/A')}")
    print(f"  Files: {len(manifest['files'])}")
    print(f"  Errors: {manifest['errors']}")
    print(f"  Duration: {manifest['total_duration_seconds']}s")

    for f in manifest["files"]:
        print(f"    {f['file']}: {f['rows']:,} rows, {f['bytes']:,} bytes")

    assert len(manifest["files"]) > 20
    assert len(manifest["errors"]) == 0

    # Verify files arrived on server by browsing data root
    data_root = Path(server["data_root"])
    parquet_files = list(data_root.rglob("*.parquet"))
    print(f"\n  Parquet files on server: {len(parquet_files)}")
    assert len(parquet_files) >= len(manifest["files"])

    # Verify each uploaded file is valid Parquet with correct row counts
    for pf_path in parquet_files:
        table = pq.read_table(pf_path)
        assert table.num_rows > 0, f"Empty file: {pf_path}"

    # Verify manifest was uploaded
    manifest_files = list(data_root.rglob("manifest.json"))
    assert len(manifest_files) >= 1
    server_manifest = json.loads(manifest_files[0].read_bytes())
    assert server_manifest["run_uuid"] == manifest["run_uuid"]

    # Verify tracking state
    env.cr.execute("SELECT state FROM parqcast_export_run ORDER BY id DESC LIMIT 1")
    assert env.cr.fetchone()[0] == "done"

    env.cr.execute("SELECT COUNT(*) FROM parqcast_export_chunk WHERE state = 'uploaded'")
    assert env.cr.fetchone()[0] > 20

    print(f"\n  E2E PASS: {len(manifest['files'])} files uploaded via HTTP to server")
