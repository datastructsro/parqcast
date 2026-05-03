# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Transport Registry for decoupling transport initialization from the Odoo addon."""

import importlib
from typing import TYPE_CHECKING, Protocol

from odoo.exceptions import ValidationError  # pyright: ignore[reportMissingImports]

_HAS_S3_TRANSPORT = importlib.util.find_spec("parqcast.transport_s3") is not None

if TYPE_CHECKING:
    from odoo.models import Environment

    from parqcast.transport.base import BaseTransport

    from ..models.parqcast_settings import ResConfigSettings


class TransportProvider(Protocol):
    """Protocol for building transports and testing connections from Odoo records."""

    def build_for_cron(self, env: "Environment") -> "BaseTransport":
        """Build the transport using saved configuration parameters."""
        ...

    def test_connection(self, settings: "ResConfigSettings") -> None:
        """Test reachability using transient configuration parameters.
        Raises an Exception on failure.
        """
        ...


class _Registry:
    def __init__(self) -> None:
        self._providers: dict[str, TransportProvider] = {}

    def register(self, code: str, provider: TransportProvider) -> None:
        """Register a new transport provider."""
        self._providers[code] = provider

    def build_for_cron(self, code: str, env: "Environment") -> "BaseTransport":
        """Build a transport using the given code."""
        provider = self._providers.get(code)
        if not provider:
            raise ValueError(f"Unknown transport type: {code}")
        return provider.build_for_cron(env)

    def test_connection(self, code: str, settings: "ResConfigSettings") -> None:
        """Test connection for a given code."""
        provider = self._providers.get(code)
        if not provider:
            raise ValidationError(settings.env._("Unknown transport type: ") + str(code))  # pyright: ignore[reportAttributeAccessIssue]
        provider.test_connection(settings)


transport_registry = _Registry()


# --- Default Providers ---


class LocalFSProvider:
    def build_for_cron(self, env: "Environment") -> "BaseTransport":
        from pathlib import Path

        from parqcast.transport.local_fs import LocalFSTransport

        ICP = env["ir.config_parameter"].sudo()
        path = ICP.get_param("parqcast.local_path", "/tmp/parqcast_export")
        return LocalFSTransport(Path(path))

    def test_connection(self, settings: "ResConfigSettings") -> None:
        # Local FS requires no active connection test in settings, just check if path is provided.
        if not settings.parqcast_local_path:
            raise ValidationError(settings.env._("Local Export Path is required."))  # pyright: ignore[reportAttributeAccessIssue]


class HttpProvider:
    def build_for_cron(self, env: "Environment") -> "BaseTransport":
        from parqcast.transport_http import HttpTransport

        ICP = env["ir.config_parameter"].sudo()
        return HttpTransport(
            server_url=ICP.get_param("parqcast.server_url", ""),
            api_key=ICP.get_param("parqcast.api_key", ""),
            namespace=ICP.get_param("parqcast.namespace", "parqcast"),
        )

    def test_connection(self, settings: "ResConfigSettings") -> None:
        from .transports import test_http_reachability

        if not settings.parqcast_server_url:
            raise ValidationError(settings.env._("Server URL is required."))  # pyright: ignore[reportAttributeAccessIssue]
        test_http_reachability(settings.parqcast_server_url, settings.parqcast_api_key)


class S3Provider:
    def build_for_cron(self, env: "Environment") -> "BaseTransport":
        from parqcast.transport_s3 import S3Transport  # pyright: ignore[reportMissingImports]

        ICP = env["ir.config_parameter"].sudo()
        return S3Transport(
            bucket=ICP.get_param("parqcast.s3_bucket", ""),
            prefix=ICP.get_param("parqcast.s3_prefix", "parqcast"),
            endpoint_url=ICP.get_param("parqcast.s3_endpoint_url") or None,
            aws_access_key_id=ICP.get_param("parqcast.s3_access_key_id") or None,
            aws_secret_access_key=ICP.get_param("parqcast.s3_secret_access_key") or None,
            region_name=ICP.get_param("parqcast.s3_region") or None,
        )

    def test_connection(self, settings: "ResConfigSettings") -> None:
        from .transports import test_s3_reachability

        if not settings.parqcast_s3_bucket:
            raise ValidationError(settings.env._("S3 Bucket is required."))  # pyright: ignore[reportAttributeAccessIssue]
        test_s3_reachability(
            bucket=settings.parqcast_s3_bucket,
            endpoint=settings.parqcast_s3_endpoint_url,
            access_key=settings.parqcast_s3_access_key_id,
            secret_key=settings.parqcast_s3_secret_access_key,
            region=settings.parqcast_s3_region,
        )


class AttachmentProvider:
    def build_for_cron(self, env: "Environment") -> "BaseTransport":
        from ..models.transport_attachment import AttachmentTransport

        return AttachmentTransport(env)

    def test_connection(self, settings: "ResConfigSettings") -> None:
        # Attachment uses Odoo's native filesystem, no connection to test
        pass


def has_s3_transport() -> bool:
    """Check if parqcast-transport-s3 package is installed."""
    return _HAS_S3_TRANSPORT


transport_registry.register("local", LocalFSProvider())
transport_registry.register("http", HttpProvider())
if _HAS_S3_TRANSPORT:
    transport_registry.register("s3", S3Provider())
transport_registry.register("attachment", AttachmentProvider())
