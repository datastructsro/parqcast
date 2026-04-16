import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path


def checksum_file(path: Path) -> str:
    return f"sha256:{sha256(path.read_bytes()).hexdigest()}"


def build_manifest(
    files: list[dict],
    company: str,
    company_id: int,
    odoo_version: str = "17.0",
    parqcast_version: str = "0.1.0",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    total_duration: float = 0.0,
) -> dict:
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


def write_manifest(manifest: dict, path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, default=str))


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_manifest(manifest: dict, directory: Path) -> list[str]:
    errors = []
    for f in manifest.get("files", []):
        fpath = directory / f["file"]
        if not fpath.exists():
            errors.append(f"Missing file: {f['file']}")
            continue
        actual = checksum_file(fpath)
        if actual != f.get("checksum"):
            errors.append(f"Checksum mismatch for {f['file']}: expected {f.get('checksum')}, got {actual}")
    return errors
