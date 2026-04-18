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


def test_supported_version_returns_tag():
    cr = StubCursor(("19.0.1.2.0",))
    assert assert_supported(cr) == "19"


def test_unknown_version_raises():
    cr = StubCursor(("18.0.0.0",))
    with pytest.raises(UnsupportedOdooVersionError) as exc:
        assert_supported(cr)
    message = str(exc.value)
    assert "Odoo 18" in message
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


def test_registry_bootstrap_has_v19():
    """Sanity check: the bootstrap registry accepts '19' from day one."""
    assert "19" in REGISTRY
    assert isinstance(REGISTRY["19"], VersionBundle)


def test_v19_bundle_is_populated_after_collector_import():
    """After importing parqcast.collectors, REGISTRY['19'] is fully assembled."""
    import parqcast.collectors  # noqa: F401 — side-effect: registers v19 bundle
    import parqcast.ingesters  # noqa: F401 — side-effect: registers v19 ingesters

    bundle = REGISTRY["19"]
    assert len(bundle.collectors) > 0, "v19 bundle has no collectors"
    assert len(bundle.suites) > 0, "v19 bundle has no suites"
    assert len(bundle.ingesters) > 0, "v19 bundle has no ingesters"
    assert bundle.probe_capabilities is not None, "v19 bundle missing probe callable"


def test_unsupported_version_list_in_error_message():
    """The error message advertises which versions ARE supported."""
    cr = StubCursor(("20.0.0.0",))
    with pytest.raises(UnsupportedOdooVersionError) as exc:
        assert_supported(cr)
    message = str(exc.value)
    assert "Odoo 20" in message
    for v in REGISTRY:
        assert f"'{v}'" in message
