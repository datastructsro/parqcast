import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from parqcast.core.manifest import (
    build_manifest,
    checksum_file,
    read_manifest,
    validate_manifest,
    write_manifest,
)


def test_build_manifest():
    m = build_manifest(
        files=[{"file": "test.parquet", "rows": 10, "bytes": 100, "checksum": "sha256:abc"}],
        company="Test Co",
        company_id=1,
    )
    assert m["company"] == "Test Co"
    assert m["company_id"] == 1
    assert len(m["files"]) == 1
    assert m["files"][0]["rows"] == 10
    assert m["errors"] == []
    assert m["warnings"] == []


def test_write_and_read_manifest():
    with tempfile.TemporaryDirectory() as d:
        m = build_manifest(files=[], company="X", company_id=42)
        p = Path(d) / "manifest.json"
        write_manifest(m, p)
        loaded = read_manifest(p)
        assert loaded["company"] == "X"
        assert loaded["company_id"] == 42


def test_checksum_file():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "test.bin"
        p.write_bytes(b"hello world")
        cs = checksum_file(p)
        assert cs.startswith("sha256:")
        assert len(cs) == 7 + 64  # "sha256:" + 64 hex chars


def test_validate_manifest_ok():
    with tempfile.TemporaryDirectory() as d:
        table = pa.table({"a": [1]})
        pq.write_table(table, Path(d) / "data.parquet")
        cs = checksum_file(Path(d) / "data.parquet")

        m = build_manifest(
            files=[{"file": "data.parquet", "rows": 1, "bytes": 100, "checksum": cs}],
            company="T",
            company_id=1,
        )
        errors = validate_manifest(m, Path(d))
        assert errors == []


def test_validate_manifest_missing_file():
    with tempfile.TemporaryDirectory() as d:
        m = build_manifest(
            files=[{"file": "missing.parquet", "rows": 1, "bytes": 100, "checksum": "sha256:xxx"}],
            company="T",
            company_id=1,
        )
        errors = validate_manifest(m, Path(d))
        assert len(errors) == 1
        assert "Missing file" in errors[0]


def test_validate_manifest_bad_checksum():
    with tempfile.TemporaryDirectory() as d:
        table = pa.table({"a": [1]})
        pq.write_table(table, Path(d) / "data.parquet")

        m = build_manifest(
            files=[{"file": "data.parquet", "rows": 1, "bytes": 100, "checksum": "sha256:wrong"}],
            company="T",
            company_id=1,
        )
        errors = validate_manifest(m, Path(d))
        assert len(errors) == 1
        assert "Checksum mismatch" in errors[0]
