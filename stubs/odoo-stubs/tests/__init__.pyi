"""Stubs for ``odoo.tests``.

Re-exports ``TransactionCase`` from ``odoo.tests.common`` so addon
tests can ``from odoo.tests import TransactionCase`` (the real Odoo
runtime hoists the same symbol to this module).
"""

from .common import BaseCase as BaseCase
from .common import TransactionCase as TransactionCase
