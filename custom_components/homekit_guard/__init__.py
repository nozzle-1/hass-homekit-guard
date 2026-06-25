"""HomeKit Guard custom integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import inspect
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_ALLOWED_SERVICES,
    CONF_BLOCKED_SERVICES,
    DEFAULT_ALLOWED_SERVICES,
    DEFAULT_BLOCKED_SERVICES,
    DOMAIN,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
)
from .guard import should_block_service

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}.state"
STORAGE_VERSION = 1

StateListener = Callable[[], None]


@dataclass
class HomeKitGuardRuntime:
    """Runtime state for HomeKit Guard."""

    hass: HomeAssistant
    entry: ConfigEntry
    store: Store
    enabled: bool = False
    listeners: list[StateListener] = field(default_factory=list)

    @property
    def blocked_services(self) -> set[str]:
        """Return configured blocked services."""
        return _normalize_service_names(
            self.entry.options.get(CONF_BLOCKED_SERVICES, DEFAULT_BLOCKED_SERVICES)
        )

    @property
    def allowed_services(self) -> set[str]:
        """Return configured allowed services."""
        return _normalize_service_names(
            self.entry.options.get(CONF_ALLOWED_SERVICES, DEFAULT_ALLOWED_SERVICES)
        )

    async def async_set_enabled(self, enabled: bool) -> None:
        """Set and persist the guard state."""
        if self.enabled == enabled:
            return

        self.enabled = enabled
        await self.store.async_save({"enabled": enabled})
        for listener in list(self.listeners):
            listener()

    @callback
    def async_add_listener(self, listener: StateListener) -> Callable[[], None]:
        """Register a listener for state changes."""
        self.listeners.append(listener)

        @callback
        def remove_listener() -> None:
            if listener in self.listeners:
                self.listeners.remove(listener)

        return remove_listener

    def should_block(self, service_name: str) -> bool:
        """Return whether a HomeKit-originating service call should be blocked."""
        normalized = _normalize_service_name(service_name)
        if not normalized or not self.enabled:
            return False

        return should_block_service(
            normalized,
            self.blocked_services,
            self.allowed_services,
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up HomeKit Guard."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HomeKit Guard from a config entry."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load() or {}

    runtime = HomeKitGuardRuntime(
        hass=hass,
        entry=entry,
        store=store,
        enabled=bool(stored.get("enabled", False)),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["runtime"] = runtime

    _patch_homekit_accessory(hass)
    _async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SWITCH])
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload HomeKit Guard."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [Platform.SWITCH])
    if not unload_ok:
        return False

    domain_data = hass.data.get(DOMAIN, {})
    domain_data.pop("runtime", None)
    _unpatch_homekit_accessory(hass)
    hass.services.async_remove(DOMAIN, SERVICE_ENABLE)
    hass.services.async_remove(DOMAIN, SERVICE_DISABLE)
    if not domain_data:
        hass.data.pop(DOMAIN, None)

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration service actions."""
    if hass.services.has_service(DOMAIN, SERVICE_ENABLE):
        return

    async def async_enable_guard(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        await runtime.async_set_enabled(True)

    async def async_disable_guard(call: ServiceCall) -> None:
        runtime = _get_runtime(hass)
        await runtime.async_set_enabled(False)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ENABLE,
        async_enable_guard,
        schema=vol.Schema({}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISABLE,
        async_disable_guard,
        schema=vol.Schema({}),
    )


def _get_runtime(hass: HomeAssistant) -> HomeKitGuardRuntime:
    """Return the active runtime."""
    return hass.data[DOMAIN]["runtime"]


def _patch_homekit_accessory(hass: HomeAssistant) -> None:
    """Patch HomeKit's HomeAccessory.async_call_service method."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("original_async_call_service") is not None:
        return

    try:
        from homeassistant.components.homekit.accessories import HomeAccessory
    except ImportError as err:
        _LOGGER.warning("Could not patch HomeKit accessory service calls: %s", err)
        return

    original = HomeAccessory.async_call_service

    def guarded_async_call_service(self: Any, *args: Any, **kwargs: Any) -> Any:
        runtime = hass.data.get(DOMAIN, {}).get("runtime")
        service_name = _extract_service_name(args, kwargs)

        if runtime is not None and service_name and runtime.should_block(service_name):
            _LOGGER.warning(
                "Blocked HomeKit service call %s from accessory %s because HomeKit Guard is enabled",
                service_name,
                getattr(self, "display_name", getattr(self, "aid", "unknown")),
            )
            return None
        if runtime is not None and runtime.enabled and service_name is None:
            _LOGGER.warning(
                "HomeKit Guard saw a HomeKit service call from accessory %s but could not determine the Home Assistant service name; allowing the call",
                getattr(self, "display_name", getattr(self, "aid", "unknown")),
            )

        result = original(self, *args, **kwargs)
        if inspect.isawaitable(result):
            hass.async_create_task(result)
            return None
        return result

    domain_data["original_async_call_service"] = original
    HomeAccessory.async_call_service = guarded_async_call_service
    _LOGGER.info("HomeKit Guard patched HomeAccessory.async_call_service")


def _unpatch_homekit_accessory(hass: HomeAssistant) -> None:
    """Restore HomeKit's original HomeAccessory.async_call_service method."""
    domain_data = hass.data.get(DOMAIN, {})
    original = domain_data.pop("original_async_call_service", None)
    if original is None:
        return

    try:
        from homeassistant.components.homekit.accessories import HomeAccessory
    except ImportError:
        return

    HomeAccessory.async_call_service = original
    _LOGGER.info("HomeKit Guard restored HomeAccessory.async_call_service")


def _extract_service_name(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str | None:
    """Extract a Home Assistant service name from a defensive method wrapper."""
    domain = kwargs.get("domain")
    service = kwargs.get("service")
    if isinstance(domain, str) and isinstance(service, str):
        return _normalize_service_name(f"{domain}.{service}")

    if isinstance(service, str):
        normalized = _normalize_service_name(service)
        if normalized:
            return normalized

    for value in kwargs.values():
        normalized = _service_name_from_value(value)
        if normalized:
            return normalized

    string_args = [value for value in args if isinstance(value, str)]
    for value in string_args:
        normalized = _normalize_service_name(value)
        if normalized:
            return normalized

    for index, value in enumerate(string_args[:-1]):
        next_value = string_args[index + 1]
        if "." not in value and "." not in next_value:
            normalized = _normalize_service_name(f"{value}.{next_value}")
            if normalized:
                return normalized

    for value in args:
        normalized = _service_name_from_value(value)
        if normalized:
            return normalized

    _LOGGER.debug(
        "Could not determine HomeKit service call from async_call_service arguments"
    )
    return None


def _service_name_from_value(value: Any) -> str | None:
    """Return a normalized service name from an arbitrary value."""
    if isinstance(value, str):
        return _normalize_service_name(value)

    if isinstance(value, dict):
        domain = value.get("domain")
        service = value.get("service")
        if isinstance(domain, str) and isinstance(service, str):
            return _normalize_service_name(f"{domain}.{service}")
        for dict_value in value.values():
            normalized = _service_name_from_value(dict_value)
            if normalized:
                return normalized

    domain = getattr(value, "domain", None)
    service = getattr(value, "service", None)
    if isinstance(domain, str) and isinstance(service, str):
        return _normalize_service_name(f"{domain}.{service}")

    return None


def _normalize_service_names(value: Any) -> set[str]:
    """Normalize service configuration from a list or comma-separated string."""
    if isinstance(value, str):
        raw_names = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_names = value
    else:
        raw_names = []

    normalized = {_normalize_service_name(str(item)) for item in raw_names}
    return {item for item in normalized if item}


def _normalize_service_name(value: str) -> str | None:
    """Normalize a Home Assistant service name."""
    normalized = value.strip().lower()
    if not normalized or "." not in normalized:
        return None

    domain, service = normalized.split(".", 1)
    if not domain or not service:
        return None
    return f"{domain}.{service}"
