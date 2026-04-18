from .base import BaseCollector as BaseCollector
from .base import CoreCollector as CoreCollector
from .base import MpsCollector as MpsCollector
from .base import MrpCollector as MrpCollector
from .base import PosCollector as PosCollector
from .base import PurchaseCollector as PurchaseCollector
from .base import QualityCollector as QualityCollector
from .base import SaleCollector as SaleCollector
from .base import StockCollector as StockCollector

# Importing v18 / v19 registers their bundles into
# parqcast.core.registry.REGISTRY. Consumers look up collectors/suites
# via REGISTRY[version_str] rather than importing a flat list from here.
from . import v18 as v18  # noqa: F401
from . import v19 as v19  # noqa: F401
