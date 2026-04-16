from .base import BaseIngester as BaseIngester
from .distribution_actor import DistributionActor
from .orderpoint_actor import OrderpointActor
from .production_actor import ProductionActor
from .purchase_actor import PurchaseActor
from .reschedule_actor import RescheduleActor

ALL_INGESTERS = {
    "PO": PurchaseActor,
    "MO": ProductionActor,
    "DO": DistributionActor,
    "RESCHEDULE": RescheduleActor,
    "ORDERPOINT": OrderpointActor,
}
