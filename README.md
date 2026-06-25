# HomeKit Guard

HomeKit Guard is a Home Assistant custom integration that can block selected HomeKit Bridge commands before they reach Home Assistant services.

It is designed for cases where HomeKit should be allowed to control some actions, such as closing or stopping covers, but should be prevented from running other actions, such as opening covers.

## What it does

- Adds a switch entity named `switch.homekit_guard_status`.
- Adds the service actions:
  - `homekit_guard.enable_homekit_guard`
  - `homekit_guard.disable_homekit_guard`
- Keeps the switch and service actions connected to the same internal guard state.
- Persists the guard state across Home Assistant restarts.
- Blocks only calls that pass through HomeKit Bridge's internal `HomeAccessory.async_call_service` path.
- Does not block Home Assistant automations, scripts, dashboard actions, MQTT, physical buttons, or direct service calls.

When HomeKit Guard is enabled, blocked HomeKit-originating service calls are skipped and a warning is written to the Home Assistant log.

## Default configuration

Blocked service calls:

- `cover.open_cover`
- `cover.set_cover_position`

Allowed service calls:

- `cover.close_cover`
- `cover.stop_cover`

Allowed service calls take precedence over blocked service calls.

## Installation

### HACS custom repository

1. Push this repository to GitHub.
2. In Home Assistant, open **HACS**.
3. Open the HACS menu and select **Custom repositories**.
4. Add the repository URL.
5. Select **Integration** as the category.
6. Install **HomeKit Guard**.
7. Restart Home Assistant.
8. Go to **Settings** > **Devices & services** > **Add integration**.
9. Search for **HomeKit Guard** and add it.

### Manual installation

1. Copy the `custom_components/homekit_guard` directory into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings** > **Devices & services**.
4. Select **Add integration**.
5. Search for **HomeKit Guard** and add it.

## Configuration

After adding the integration, open its options from **Settings** > **Devices & services**.

Configure blocked and allowed service calls from the multi-select lists. The lists are populated from the service actions currently registered in Home Assistant.

The selector allows custom values so you can keep or enter service calls that are not registered when the options screen is opened.

Examples:

- Blocked service calls: `cover.open_cover, cover.set_cover_position`
- Allowed service calls: `cover.close_cover, cover.stop_cover`

If your Home Assistant version does not support native select selectors in custom integration options, the integration falls back to text fields accepting comma-separated service names.

## Usage

Turn on `switch.homekit_guard_status` to enable blocking.

You can also call:

```yaml
service: homekit_guard.enable_homekit_guard
```

or:

```yaml
service: homekit_guard.disable_homekit_guard
```

## Important warning

HomeKit Guard monkey-patches Home Assistant internals:

```text
homeassistant.components.homekit.accessories.HomeAccessory.async_call_service
```

This is intentionally narrow so only HomeKit Bridge-originating calls are affected, but it depends on Home Assistant's private HomeKit implementation details. Home Assistant updates may change that method or its call signature, which can break this integration.

The integration includes defensive handling for unknown call signatures. If it cannot identify a HomeKit service call safely, it allows the original Home Assistant method to run.
