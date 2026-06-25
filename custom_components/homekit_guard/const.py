"""Constants for HomeKit Guard."""

DOMAIN = "homekit_guard"

CONF_BLOCKED_SERVICES = "blocked_services"
CONF_ALLOWED_SERVICES = "allowed_services"

DEFAULT_BLOCKED_SERVICES = ["cover.open_cover", "cover.set_cover_position"]
DEFAULT_ALLOWED_SERVICES = ["cover.close_cover", "cover.stop_cover"]

SERVICE_ENABLE = "enable_homekit_guard"
SERVICE_DISABLE = "disable_homekit_guard"

PLATFORMS = ["switch"]
