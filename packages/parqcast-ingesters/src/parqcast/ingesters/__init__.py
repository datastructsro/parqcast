from .base import BaseIngester as BaseIngester
from .v19 import (
    DistributionActorV19,
    OrderpointActorV19,
    ProductionActorV19,
    PurchaseActorV19,
    RescheduleActorV19,
)

ALL_INGESTERS = {
    "PO": PurchaseActorV19,
    "MO": ProductionActorV19,
    "DO": DistributionActorV19,
    "RESCHEDULE": RescheduleActorV19,
    "ORDERPOINT": OrderpointActorV19,
}
