"""Stubs for ``odoo.models``.

Design principle: every method that returns a record or recordset returns
``Any`` rather than a parameterised ``Recordset[T]``. This deliberately
leaks ``Any`` into the addon, sidestepping pyright's ``reportUnknown*``
family entirely. ``Any`` is fully known (it's ``Any``); a partially-typed
return like ``Recordset[Unknown]`` would force us to add casts at every
call site or suppress those rules globally — neither acceptable.

Pyright still catches:
  - missing methods (typo on a stubbed name like ``browseee``);
  - field declaration errors (handled in ``odoo.fields``);
  - imports of names that don't exist on this stub.

Pyright cannot catch (acceptable trade-off):
  - dynamic field access via ``__getattr__ -> Any``;
  - chained ORM expressions whose intermediate types are ``Any``.
"""

from collections.abc import Iterator
from typing import Any, ClassVar


class Environment:
    """Stub for ``odoo.api.Environment`` exposed via ``BaseModel.env``."""

    cr: Any
    company: Any

    def __getitem__(self, model_name: str) -> "BaseModel": ...
    def ref(self, xml_id: str, raise_if_not_found: bool = True) -> Any: ...


class BaseModel:
    """Common base for Model / AbstractModel / TransientModel.

    Class-level attributes are typed as ``ClassVar`` so subclasses set them
    by simple assignment (``_name = "parqcast.run"``) without pyright
    flagging instance-attribute shadowing.
    """

    _name: ClassVar[str]
    _description: ClassVar[str]
    _inherit: ClassVar[str | list[str]]
    _table: ClassVar[str]
    _order: ClassVar[str]
    _auto: ClassVar[bool]
    _fields: ClassVar[dict[str, Any]]

    env: Environment
    id: int

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    # Odoo's BaseModel._register_hook is an instance method on the registered
    # singleton, not a classmethod — overrides in addons (e.g.
    # ParqcastVersionGate) declare ``def _register_hook(self): ...``.
    def _register_hook(self) -> None: ...

    def init(self) -> None: ...
    def browse(self, ids: int | list[int]) -> Any: ...
    def search(self, domain: list[Any], **kwargs: Any) -> Any: ...
    def search_count(self, domain: list[Any]) -> int: ...
    def exists(self) -> Any: ...
    def ensure_one(self) -> Any: ...
    def sudo(self, flag: bool = True) -> Any: ...
    def create(self, vals: dict[str, Any] | list[dict[str, Any]]) -> Any: ...
    def write(self, vals: dict[str, Any]) -> bool: ...
    def unlink(self) -> bool: ...

    # res.config.settings inherits from TransientModel and exposes these two
    # hooks; addons override them via ``_inherit = "res.config.settings"``.
    # Modeling them on BaseModel keeps the stub small — it costs nothing on
    # other models because they're never called there.
    def set_values(self) -> Any: ...
    def get_values(self) -> dict[str, Any]: ...

    # Recordsets are iterable, sized, and truthy. Each iteration yields a
    # singleton record (typed as Any so attribute access is permissive).
    def __iter__(self) -> Iterator[Any]: ...
    def __len__(self) -> int: ...
    def __bool__(self) -> bool: ...
    def __or__(self, other: "BaseModel") -> Any: ...
    def __and__(self, other: "BaseModel") -> Any: ...
    def __sub__(self, other: "BaseModel") -> Any: ...

    def __getattr__(self, name: str) -> Any: ...


class Model(BaseModel): ...
class AbstractModel(BaseModel): ...
class TransientModel(BaseModel): ...
