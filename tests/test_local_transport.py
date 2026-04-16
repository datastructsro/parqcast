import io
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from parqcast.transport.local_fs import LocalFSTransport


def test_upload_and_download_round_trip():
    with tempfile.TemporaryDirectory() as base:
        transport = LocalFSTransport(base)

        table = pa.table({"x": [1, 2, 3], "y": ["a", "b", "c"]})
        buf = io.BytesIO()
        pq.write_table(table, buf)
        parquet_bytes = buf.getvalue()

        transport.upload_file("run/2026-04-11", "test.parquet", io.BytesIO(parquet_bytes))
        transport.upload_file("run/2026-04-11", "meta.json", io.BytesIO(b'{"ok": true}'))

        downloaded_parquet = transport.download_file("run/2026-04-11", "test.parquet")
        downloaded_json = transport.download_file("run/2026-04-11", "meta.json")

        downloaded_table = pq.read_table(io.BytesIO(downloaded_parquet))
        assert downloaded_table.equals(table)
        assert downloaded_json == b'{"ok": true}'


def test_list_files():
    with tempfile.TemporaryDirectory() as base:
        transport = LocalFSTransport(base)

        transport.upload_file("run/latest", "a.parquet", io.BytesIO(b"data_a"))
        transport.upload_file("run/latest", "b.parquet", io.BytesIO(b"data_b"))
        transport.upload_file("run/latest", "manifest.json", io.BytesIO(b"{}"))

        files = transport.list_files("run/latest")
        assert files == ["a.parquet", "b.parquet", "manifest.json"]


def test_list_files_empty():
    with tempfile.TemporaryDirectory() as base:
        transport = LocalFSTransport(base)
        assert transport.list_files("nonexistent") == []


def test_upload_file_creates_dirs():
    with tempfile.TemporaryDirectory() as base:
        transport = LocalFSTransport(base)
        transport.upload_file("deep/nested/prefix", "data.parquet", io.BytesIO(b"parquet"))

        result = transport.download_file("deep/nested/prefix", "data.parquet")
        assert result == b"parquet"


def test_download_file_not_found():
    with tempfile.TemporaryDirectory() as base:
        transport = LocalFSTransport(base)
        with pytest.raises(FileNotFoundError):
            transport.download_file("missing", "file.parquet")
