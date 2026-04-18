import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast

from parqcast.core.protocols import ChunkMetadata, JsonDict


def checksum_file(path: Path) -> str:
    return f"sha256:{sha256(path.read_bytes()).hexdigest()}"


def build_manifest(
    files: list[ChunkMetadata],
    company: str,
    company_id: int,
    odoo_version: str = "17.0",
    parqcast_version: str = "0.1.0",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    total_duration: float = 0.0,
) -> JsonDict:
    return {
        "version": parqcast_version,
        "schema_version": datetime.now(UTC).strftime("%Y-%m-%d"),
        "timestamp": datetime.now(UTC).isoformat(),
        "company": company,
        "company_id": company_id,
        "odoo_version": odoo_version,
        "parqcast_version": parqcast_version,
        "export_mode": "full",
        "files": files,
        "errors": errors or [],
        "warnings": warnings or [],
        "total_duration_seconds": total_duration,
    }


def write_manifest(manifest: JsonDict, path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, default=str))


def read_manifest(path: Path) -> JsonDict:
    return json.loads(path.read_text())


def validate_manifest(manifest: JsonDict, directory: Path) -> list[str]:
    errors: list[str] = []
    files_raw: object = manifest.get("files", [])
    if not isinstance(files_raw, list):
        return ["manifest['files'] must be a list"]
    files = cast("list[object]", files_raw)
    for f in files:
        if not isinstance(f, dict):
            errors.append(f"Expected dict in manifest['files'], got {type(f).__name__}")
            continue
        entry = cast("dict[str, object]", f)
        file_name = entry.get("file")
        if not isinstance(file_name, str):
            errors.append("manifest['files'][].file must be a string")
            continue
        fpath = directory / file_name
        if not fpath.exists():
            errors.append(f"Missing file: {file_name}")
            continue
        actual = checksum_file(fpath)
        expected = entry.get("checksum")
        if actual != expected:
            errors.append(f"Checksum mismatch for {file_name}: expected {expected!r}, got {actual}")
    return errors
