"""Unit tests for :mod:`parqcast.core.version_gate`.

No Odoo required — uses a stub cursor that returns configured rows.
"""

from __future__ import annotations

import pytest

from parqcast.core.registry import REGISTRY, VersionBundle
from parqcast.core.version import UnsupportedOdooVersionError
from parqcast.core.version_gate import assert_supported


class StubCursor:
    """Minimal cursor mimicking the two methods assert_supported calls."""

    def __init__(self, version_row: tuple[object, ...] | None) -> None:
        self._row = version_row
        self.executed: list[str] = []

    def execute(self, sql: str) -> None:
        self.executed.append(sql)

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row


def test_supported_version_returns_tag_v19():
    cr = StubCursor(("19.0.1.2.0",))
    assert assert_supported(cr) == "19"


def test_supported_version_returns_tag_v18():
    cr = StubCursor(("18.0.1.1.0",))
    assert assert_supported(cr) == "18"


def test_unknown_version_raises():
    cr = StubCursor(("17.0.0.0",))
    with pytest.raises(UnsupportedOdooVersionError) as exc:
        assert_supported(cr)
    message = str(exc.value)
    assert "Odoo 17" in message
    assert "'18'" in message
    assert "'19'" in message


def test_missing_module_row_raises():
    cr = StubCursor(None)
    with pytest.raises(UnsupportedOdooVersionError) as exc:
        assert_supported(cr)
    assert "<unknown>" in str(exc.value)


def test_empty_version_string_raises():
    cr = StubCursor(("",))
    with pytest.raises(UnsupportedOdooVersionError):
        assert_supported(cr)


def test_registry_bootstrap_has_supported_versions():
    """Sanity check: the bootstrap registry has entries for every supported major."""
    for version in ("18", "19"):
        assert version in REGISTRY, f"missing bootstrap entry for Odoo {version}"
        assert isinstance(REGISTRY[version], VersionBundle)


def test_bundles_are_populated_after_collector_import():
    """After importing parqcast.collectors and parqcast.ingesters, every
    supported bundle is fully assembled."""
    import parqcast.collectors  # noqa: F401 — side-effect: registers v18+v19 bundles
    import parqcast.ingesters  # noqa: F401 — side-effect: registers v18+v19 ingesters

    for version in ("18", "19"):
        bundle = REGISTRY[version]
        assert len(bundle.collectors) > 0, f"v{version} bundle has no collectors"
        assert len(bundle.suites) > 0, f"v{version} bundle has no suites"
        assert len(bundle.ingesters) > 0, f"v{version} bundle has no ingesters"
        assert bundle.probe_capabilities is not None, f"v{version} bundle missing probe callable"


def test_v18_and_v19_bundles_have_same_shape():
    """Both bundles should register the same number of collectors / suites /
    ingesters — v18 mirrors v19's surface by design (Snowflake contract)."""
    import parqcast.collectors  # noqa: F401
    import parqcast.ingesters  # noqa: F401

    b18 = REGISTRY["18"]
    b19 = REGISTRY["19"]
    assert len(b18.collectors) == len(b19.collectors), (
        f"v18 has {len(b18.collectors)} collectors, v19 has {len(b19.collectors)}"
    )
    assert len(b18.suites) == len(b19.suites), (
        f"v18 has {len(b18.suites)} suites, v19 has {len(b19.suites)}"
    )
    assert len(b18.ingesters) == len(b19.ingesters), (
        f"v18 has {len(b18.ingesters)} ingesters, v19 has {len(b19.ingesters)}"
    )
    # Suite names must match 1:1 (same module-gated groupings)
    assert {s.name for s in b18.suites} == {s.name for s in b19.suites}


def test_v18_and_v19_collectors_emit_identical_parquet_schemas():
    """Every collector-name present in both bundles must declare the same
    outbound Arrow schema. This is the static guarantee the Snowflake
    contract depends on — v18 and v19 produce byte-identical Parquet
    output, with columns in the same order and of the same type.

    Validation is purely static (reads ``cls.schema`` class attribute), so
    no database is needed. If a future collector redefines its own schema
    on one major only, this test catches it before runtime.
    """
    import parqcast.collectors  # noqa: F401
    import parqcast.ingesters  # noqa: F401

    b18 = REGISTRY["18"]
    b19 = REGISTRY["19"]

    schemas_18: dict[str, object] = {cls.name: cls.schema for cls in b18.collectors}
    schemas_19: dict[str, object] = {cls.name: cls.schema for cls in b19.collectors}

    assert schemas_18.keys() == schemas_19.keys(), (
        f"Collector-name mismatch — v18-only: {schemas_18.keys() - schemas_19.keys()}; "
        f"v19-only: {schemas_19.keys() - schemas_18.keys()}"
    )

    mismatches: list[str] = []
    for name in sorted(schemas_18):
        if schemas_18[name] != schemas_19[name]:
            mismatches.append(
                f"{name}: v18 schema != v19 schema\n  v18: {schemas_18[name]}\n  v19: {schemas_19[name]}"
            )
    assert not mismatches, "Collector schemas diverge between majors:\n" + "\n".join(mismatches)


def test_v18_and_v19_ingesters_have_same_decision_types():
    """Ingesters are keyed by ``decision_type`` string — the receiver dispatches
    on it. v18 and v19 must register actors for exactly the same set of
    decision types.
    """
    import parqcast.collectors  # noqa: F401
    import parqcast.ingesters  # noqa: F401

    dt_18 = {cls.decision_type for cls in REGISTRY["18"].ingesters}
    dt_19 = {cls.decision_type for cls in REGISTRY["19"].ingesters}
    assert dt_18 == dt_19, f"v18 ingester decision_types {dt_18} != v19 {dt_19}"


def test_unsupported_version_list_in_error_message():
    """The error message advertises which versions ARE supported."""
    cr = StubCursor(("20.0.0.0",))
    with pytest.raises(UnsupportedOdooVersionError) as exc:
        assert_supported(cr)
    message = str(exc.value)
    assert "Odoo 20" in message
    for v in REGISTRY:
        assert f"'{v}'" in message
