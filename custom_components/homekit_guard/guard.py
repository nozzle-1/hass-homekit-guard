"""Pure guard decision helpers."""

from __future__ import annotations


def should_block_service(
    service_name: str,
    blocked_services: set[str],
    allowed_services: set[str],
) -> bool:
    """Return whether a normalized service should be blocked."""
    if not blocked_services and not allowed_services:
        return False
    if allowed_services and not blocked_services:
        return service_name not in allowed_services
    if service_name in allowed_services:
        return False
    return service_name in blocked_services
