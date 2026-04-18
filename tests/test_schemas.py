import pyarrow as pa

import parqcast.collectors  # noqa: F401 — populates REGISTRY['19']
from parqcast.core.registry import REGISTRY
from parqcast.schemas.inbound import DECISIONS_SCHEMA
from parqcast.schemas.outbound import ALL_OUTBOUND_SCHEMAS

ALL_COLLECTOR_CLASSES = list(REGISTRY["19"].collectors)


def test_all_outbound_schemas_are_valid():
    assert len(ALL_OUTBOUND_SCHEMAS) == 47
    for name, schema in ALL_OUTBOUND_SCHEMAS.items():
        assert isinstance(schema, pa.Schema), f"{name} is not a pa.Schema"
        assert len(schema) > 0, f"{name} has no fields"


def test_each_schema_can_create_empty_table():
    for schema in ALL_OUTBOUND_SCHEMAS.values():
        table = pa.table({f.name: [] for f in schema}, schema=schema)
        assert table.num_rows == 0
        assert table.num_columns == len(schema)


def test_decisions_schema_is_valid():
    assert isinstance(DECISIONS_SCHEMA, pa.Schema)
    assert len(DECISIONS_SCHEMA) == 23
    table = pa.table({f.name: [] for f in DECISIONS_SCHEMA}, schema=DECISIONS_SCHEMA)
    assert table.num_rows == 0


def test_all_collectors_have_matching_schema():
    schema_names = set(ALL_OUTBOUND_SCHEMAS.keys())
    collector_names = {c.name for c in ALL_COLLECTOR_CLASSES}
    assert collector_names == schema_names, (
        f"Mismatch: collectors only={collector_names - schema_names}, schemas only={schema_names - collector_names}"
    )


def test_all_collectors_have_schema_attribute():
    for cls in ALL_COLLECTOR_CLASSES:
        assert hasattr(cls, "schema"), f"{cls.__name__} missing schema"
        assert isinstance(cls.schema, pa.Schema), f"{cls.__name__}.schema is not pa.Schema"
        assert cls.schema == ALL_OUTBOUND_SCHEMAS[cls.name], (
            f"{cls.__name__}.schema doesn't match ALL_OUTBOUND_SCHEMAS[{cls.name!r}]"
        )


def test_id_columns_are_int64():
    for name, schema in ALL_OUTBOUND_SCHEMAS.items():
        for field in schema:
            if field.name.startswith("_odoo_") and field.name.endswith("_id"):
                assert field.type == pa.int64(), f"{name}.{field.name} should be int64 but is {field.type}"


def test_timestamp_columns_have_utc():
    for name, schema in ALL_OUTBOUND_SCHEMAS.items():
        for field in schema:
            if isinstance(field.type, pa.TimestampType):
                assert field.type.tz == "UTC", f"{name}.{field.name} timestamp should be UTC but is {field.type.tz}"


def test_collector_type_hierarchy():
    """Every collector must declare its tier via base class."""
    from parqcast.collectors.base import (
        CoreCollector,
        MpsCollector,
        MrpCollector,
        PosCollector,
        PurchaseCollector,
        QualityCollector,
        SaleCollector,
        StockCollector,
    )

    tier_bases = (
        CoreCollector,
        StockCollector,
        SaleCollector,
        PurchaseCollector,
        MrpCollector,
        PosCollector,
        MpsCollector,
        QualityCollector,
    )
    for cls in ALL_COLLECTOR_CLASSES:
        assert issubclass(cls, tier_bases), f"{cls.__name__} does not inherit from a tier base class"
