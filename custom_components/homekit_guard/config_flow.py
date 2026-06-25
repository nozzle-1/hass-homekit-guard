"""Config flow for HomeKit Guard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_ALLOWED_SERVICES,
    CONF_BLOCKED_SERVICES,
    DEFAULT_ALLOWED_SERVICES,
    DEFAULT_BLOCKED_SERVICES,
    DOMAIN,
)


class HomeKitGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HomeKit Guard."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="HomeKit Guard", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HomeKitGuardOptionsFlow:
        """Create the options flow."""
        return HomeKitGuardOptionsFlow(config_entry)


class HomeKitGuardOptionsFlow(config_entries.OptionsFlow):
    """Handle HomeKit Guard options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage HomeKit Guard options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_BLOCKED_SERVICES: _parse_services(
                        user_input[CONF_BLOCKED_SERVICES]
                    ),
                    CONF_ALLOWED_SERVICES: _parse_services(
                        user_input[CONF_ALLOWED_SERVICES]
                    ),
                },
            )

        blocked_services = self._config_entry.options.get(
            CONF_BLOCKED_SERVICES, DEFAULT_BLOCKED_SERVICES
        )
        allowed_services = self._config_entry.options.get(
            CONF_ALLOWED_SERVICES, DEFAULT_ALLOWED_SERVICES
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_BLOCKED_SERVICES,
                    default=", ".join(blocked_services),
                ): str,
                vol.Required(
                    CONF_ALLOWED_SERVICES,
                    default=", ".join(allowed_services),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


def _parse_services(value: str) -> list[str]:
    """Parse comma-separated Home Assistant service names."""
    services: list[str] = []
    for raw_service in value.split(","):
        service = raw_service.strip().lower()
        if service and "." in service and service not in services:
            services.append(service)
    return services
