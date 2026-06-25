"""Config flow for HomeKit Guard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries

try:
    from homeassistant.helpers import selector
except ImportError:
    selector = None

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

        if _supports_select_selector():
            service_options = _service_options(
                self.hass,
                [
                    *_parse_services(blocked_services),
                    *_parse_services(allowed_services),
                ],
            )
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_BLOCKED_SERVICES,
                        default=_parse_services(blocked_services),
                    ): _service_select_selector(service_options),
                    vol.Required(
                        CONF_ALLOWED_SERVICES,
                        default=_parse_services(allowed_services),
                    ): _service_select_selector(service_options),
                }
            )
        else:
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_BLOCKED_SERVICES,
                        default=", ".join(_parse_services(blocked_services)),
                    ): str,
                    vol.Required(
                        CONF_ALLOWED_SERVICES,
                        default=", ".join(_parse_services(allowed_services)),
                    ): str,
                }
            )

        return self.async_show_form(step_id="init", data_schema=schema)


def _supports_select_selector() -> bool:
    """Return whether Home Assistant supports select selectors."""
    return selector is not None and hasattr(selector, "SelectSelector")


def _service_select_selector(service_options: list[str]) -> Any:
    """Return a multiple select selector for Home Assistant service names."""
    return selector.SelectSelector(
        {
            "options": service_options,
            "multiple": True,
            "custom_value": True,
            "mode": "dropdown",
        }
    )


def _service_options(hass: Any, selected_services: list[str]) -> list[str]:
    """Return available Home Assistant service names for selector options."""
    services = set(_parse_services(selected_services))
    for domain, domain_services in hass.services.async_services().items():
        for service in domain_services:
            services.add(f"{domain}.{service}")
    return sorted(services)


def _parse_services(value: Any) -> list[str]:
    """Parse Home Assistant service names."""
    if isinstance(value, str):
        raw_services = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        raw_services = value
    else:
        raw_services = []

    services: list[str] = []
    for raw_service in raw_services:
        service = str(raw_service).strip().lower()
        if service and "." in service and service not in services:
            services.append(service)
    return services
