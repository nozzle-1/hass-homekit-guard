# HomeKit Guard

Block selected HomeKit Bridge actions on demand before they reach Home Assistant.

HomeKit Guard is useful when Siri/HomePod voice control is convenient most of the time, but too exposed in specific situations. For example: if a window facing the street is open, you may not want someone outside to shout a command at your HomePod and open covers, unlock something, or trigger another sensitive action.

Turn the guard on when you need that extra barrier. Turn it off when normal HomeKit voice control is fine again.

## Why use it

- Block risky HomePod/Siri actions while keeping safer actions available.
- Temporarily protect exposed rooms, street-facing windows, guests, rentals, or outdoor areas.
- Keep Home Assistant automations, dashboards, scripts, MQTT, and physical controls working.
- Control the guard from a switch, an automation, or two service actions.
- Persist the guard state across Home Assistant restarts.

## Example use cases

- **Street-facing window open**: block `cover.open_cover` so someone outside cannot open blinds or shutters by voice.
- **Night mode**: allow closing covers, but block opening covers until morning.
- **Guest mode**: disable sensitive HomeKit voice actions while visitors are home.
- **Outdoor HomePod**: block actions you never want triggered from a garden, balcony, or terrace.
- **Temporary lockdown**: use an automation to enable the guard when a contact sensor, alarm mode, or presence state says the home is more exposed.

## How it works

HomeKit Guard patches Home Assistant's HomeKit Bridge service-call path:

```text
homeassistant.components.homekit.accessories.HomeAccessory.async_call_service
```

When the guard is enabled, matching HomeKit-originating service calls are skipped and a warning is written to the Home Assistant log.

It does **not** block Home Assistant automations, scripts, dashboard actions, MQTT, physical buttons, or direct service calls. The block is intentionally narrow: only commands passing through HomeKit Bridge are affected.

## Default behavior

By default, HomeKit Guard blocks opening covers while still allowing closing or stopping them.

Blocked:

- `cover.open_cover`
- `cover.set_cover_position`

Allowed:

- `cover.close_cover`
- `cover.stop_cover`

You can change these lists from the integration options.

## Blocking rules

When HomeKit Guard is enabled:

- If only allowed services are configured, every other HomeKit service call is blocked.
- If only blocked services are configured, only those service calls are blocked.
- If both lists are configured, allowed services take priority.
- If both lists are empty, nothing is blocked.

## Installation

### HACS custom repository

1. In Home Assistant, open **HACS**.
2. Open **Custom repositories** from the HACS menu.
3. Add this repository URL.
4. Select **Integration** as the category.
5. Install **HomeKit Guard**.
6. Restart Home Assistant.
7. Go to **Settings** > **Devices & services** > **Add integration**.
8. Search for **HomeKit Guard** and add it.

### Manual installation

1. Copy `custom_components/homekit_guard` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings** > **Devices & services** > **Add integration**.
4. Search for **HomeKit Guard** and add it.

## Configuration

Open **Settings** > **Devices & services** > **HomeKit Guard** > **Options**.

Configure:

- **Blocked services**: Home Assistant service calls to block when the guard is enabled.
- **Allowed services**: service calls that should remain available from HomeKit.

Examples:

- Blocked services: `cover.open_cover`, `cover.set_cover_position`
- Allowed services: `cover.close_cover`, `cover.stop_cover`

The options form is populated from services currently registered in Home Assistant and also accepts custom service names. On older Home Assistant versions, it falls back to comma-separated text fields.

## Usage

Enable or disable the guard with:

- `switch.homekit_guard_status`
- `homekit_guard.enable_homekit_guard`
- `homekit_guard.disable_homekit_guard`

Example automation action:

```yaml
service: homekit_guard.enable_homekit_guard
```

## Important note

HomeKit Guard depends on Home Assistant's private HomeKit Bridge internals. Home Assistant updates may change that implementation and break this integration.

The integration handles unknown call signatures defensively: if it cannot safely identify a HomeKit service call, it allows the original Home Assistant method to run.
