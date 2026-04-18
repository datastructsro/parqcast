from .base import BaseIngester as BaseIngester

# Importing v18 / v19 registers their ingesters into
# parqcast.core.registry.REGISTRY[version].ingesters.
from . import v18 as v18  # noqa: F401
from . import v19 as v19  # noqa: F401
from .v19 import (
    DistributionActorV19,
    OrderpointActorV19,
    ProductionActorV19,
    PurchaseActorV19,
    RescheduleActorV19,
)

# Legacy direct map used by parqcast.receiver (the sibling parqcast-server
# repo's entrypoint; predates the registry pattern). The receiver is
# version-agnostic; it picks actors by decision_type. Keep v19-keyed here —
# the receiver doesn't know about Odoo majors. Version-aware code paths
# should look up REGISTRY[version].ingesters instead.
ALL_INGESTERS = {
    "PO": PurchaseActorV19,
    "MO": ProductionActorV19,
    "DO": DistributionActorV19,
    "RESCHEDULE": RescheduleActorV19,
    "ORDERPOINT": OrderpointActorV19,
}
