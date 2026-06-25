"""Switch platform for HomeKit Guard."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from . import HomeKitGuardRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HomeKit Guard switch."""
    runtime: HomeKitGuardRuntime = hass.data[DOMAIN]["runtime"]
    async_add_entities([HomeKitGuardSwitch(runtime)])


class HomeKitGuardSwitch(SwitchEntity):
    """Switch for enabling or disabling HomeKit Guard."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_suggested_object_id = "homekit_guard_status"
    _attr_translation_key = "status"

    def __init__(self, runtime: HomeKitGuardRuntime) -> None:
        """Initialize the switch."""
        self._runtime = runtime
        self._attr_unique_id = f"{runtime.entry.entry_id}_status"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._runtime.entry.entry_id)},
            "name": "HomeKit Guard",
            "manufacturer": "HomeKit Guard",
        }

    @property
    def is_on(self) -> bool:
        """Return whether HomeKit Guard is enabled."""
        return self._runtime.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable HomeKit Guard."""
        await self._runtime.async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable HomeKit Guard."""
        await self._runtime.async_set_enabled(False)

    async def async_added_to_hass(self) -> None:
        """Register runtime state listener."""
        self.async_on_remove(
            self._runtime.async_add_listener(self._handle_runtime_update)
        )

    @callback
    def _handle_runtime_update(self) -> None:
        """Update Home Assistant when the runtime state changes."""
        self.async_write_ha_state()
