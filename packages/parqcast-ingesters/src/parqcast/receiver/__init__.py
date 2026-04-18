import json
import tempfile
from pathlib import Path

import pyarrow.parquet as pq

from parqcast.core.manifest import validate_manifest
from parqcast.core.protocols import JsonDict
from parqcast.ingesters import ALL_INGESTERS
from parqcast.ingesters.base import IngestResult
from parqcast.transport.base import BaseTransport


class Receiver:
    def __init__(self, env, transport: BaseTransport, company_id: int):
        self.env = env
        self.transport = transport
        self.company_id = company_id

    def run(self, remote_prefix: str, cleanup: bool = True) -> JsonDict:
        results = {}

        # Download manifest
        try:
            manifest_bytes = self.transport.download_file(remote_prefix, "manifest.json")
        except FileNotFoundError:
            return {"error": "No manifest.json found"}

        manifest = json.loads(manifest_bytes)

        # Download files to temp dir for validation
        with tempfile.TemporaryDirectory(prefix="parqcast_in_") as tmpdir:
            local = Path(tmpdir)
            for file_meta in manifest.get("files", []):
                filename = file_meta["file"]
                data = self.transport.download_file(remote_prefix, filename)
                (local / filename).write_bytes(data)

            # Write manifest for validation
            (local / "manifest.json").write_bytes(manifest_bytes)

            validation_errors = validate_manifest(manifest, local)
            if validation_errors:
                return {"error": "Manifest validation failed", "details": validation_errors}

            # Find decisions file
            decisions_path = local / "decisions.parquet"
            if not decisions_path.exists():
                return {"error": "No decisions.parquet found"}

            table = pq.read_table(decisions_path)
            type_col = table.column("decision_type").to_pylist()
            unique_types: set[str] = {t for t in type_col if isinstance(t, str)}

            for dtype in unique_types:
                ingester_cls = ALL_INGESTERS.get(dtype)
                if not ingester_cls:
                    results[dtype] = IngestResult(errors=1, messages=[f"Unknown decision type: {dtype}"])
                    continue

                mask = [t == dtype for t in type_col]
                filtered = table.filter(mask)

                ingester = ingester_cls()
                if cleanup:
                    ingester.cleanup_previous(self.env, self.company_id)

                results[dtype] = ingester.apply(filtered, self.env)

        return {k: repr(v) for k, v in results.items()}
