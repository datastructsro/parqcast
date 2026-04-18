"""Project-local type stubs for the Odoo runtime.

The ``odoo`` package isn't pip-installable — it only exists inside a
running Odoo server. These stubs cover only the symbols parqcast's addon
actually imports, plus a small forward-compatibility margin (additional
api decorators and field types). They are NOT a comprehensive Odoo type
package; for that, see community projects like ``odoo-stubs`` on PyPI.

Lives at ``stubs/odoo-stubs/`` and is wired in via pyright's ``stubPath``
in ``pyproject.toml``. Not intended for distribution.
"""

from . import api as api
from . import fields as fields
from . import models as models
