"""Services for the Scandia Fireplace integration.

``scandia_fireplace.set_state`` applies several settings in one go — the point
being that it reaches the fireplace as a *single* write rather than a series of
separate button presses, so a scene like "game day" lands at once instead of
visibly stepping through colours.

Preset values may be given either as the friendly label shown in Home Assistant
("Colour 4") or as the raw device value ("L04"), matched case-insensitively.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import ATTR_DEVICE_ID, ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    FN_FLAME_EFFECT,
    FN_FLAME_LOG,
    FN_HEAT,
    FN_POWER,
    FN_TIMER,
    FN_TOP_LIGHT,
)
from .coordinator import ScandiaBaseCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_STATE = "set_state"

# Service field -> semantic function. Every field is optional; only the ones
# supplied are written.
PRESET_FIELDS: dict[str, str] = {
    "flame_colour": FN_FLAME_EFFECT,
    "flame_log_colour": FN_FLAME_LOG,
    "top_light": FN_TOP_LIGHT,
    "heater": FN_HEAT,
    "timer": FN_TIMER,
}

# Seconds to wait between switching the fireplace on and sending presets to a
# device that was off. A board that has just woken up can drop colour values
# that arrive in the same breath as the power command.
POWER_SETTLE = 1.0

SET_STATE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional("power"): cv.boolean,
        **{vol.Optional(field): cv.string for field in PRESET_FIELDS},
    }
)


def _resolve_preset(
    coordinator: ScandiaBaseCoordinator, function: str, given: str
) -> Any:
    """Turn a friendly label or raw value into the value the device expects."""
    labels = coordinator.option_labels(function)
    if not labels:
        raise ServiceValidationError(
            f"'{function}' is not available on this fireplace. Colour and heater "
            "controls need local mode and a matching device profile."
        )

    # Raw values win outright, then labels, then a case-insensitive fallback.
    if given in labels:
        return given
    lookup = {label.casefold(): raw for raw, label in labels.items()}
    lookup.update({raw.casefold(): raw for raw in labels})
    match = lookup.get(given.casefold())
    if match is None:
        choices = ", ".join(f"'{label}'" for label in labels.values())
        raise ServiceValidationError(
            f"'{given}' is not a valid value for {function}. Choose one of: {choices}."
        )
    return match


def _target_coordinators(
    hass: HomeAssistant, call: ServiceCall
) -> list[ScandiaBaseCoordinator]:
    """Resolve the service target to the fireplaces it refers to."""
    loaded: dict[str, ScandiaBaseCoordinator] = hass.data.get(DOMAIN, {})
    entry_ids: set[str] = set()

    device_reg = dr.async_get(hass)
    for device_id in call.data.get(ATTR_DEVICE_ID, []):
        device = device_reg.async_get(device_id)
        if device is None:
            raise ServiceValidationError(f"Unknown device ID '{device_id}'.")
        entry_ids.update(device.config_entries)

    entity_reg = er.async_get(hass)
    for entity_id in call.data.get(ATTR_ENTITY_ID, []):
        entity = entity_reg.async_get(entity_id)
        if entity is None or entity.config_entry_id is None:
            raise ServiceValidationError(f"Unknown entity ID '{entity_id}'.")
        entry_ids.add(entity.config_entry_id)

    # No target at all means "the fireplace" — fine while there is only one.
    if not entry_ids:
        entry_ids = set(loaded)

    coordinators = [loaded[entry_id] for entry_id in entry_ids if entry_id in loaded]
    if not coordinators:
        raise ServiceValidationError(
            "No loaded Scandia Fireplace was found for that target."
        )
    return coordinators


async def _async_apply(coordinator: ScandiaBaseCoordinator, call: ServiceCall) -> None:
    """Write the requested settings to one fireplace."""
    values: dict[str, Any] = {}
    if "power" in call.data:
        values[FN_POWER] = call.data["power"]
    for field, function in PRESET_FIELDS.items():
        if field in call.data:
            values[function] = _resolve_preset(coordinator, function, call.data[field])

    if not values:
        raise ServiceValidationError("Supply at least one setting to apply.")

    presets = {fn: value for fn, value in values.items() if fn != FN_POWER}
    turning_on = values.get(FN_POWER) is True and not coordinator.read(FN_POWER)
    if turning_on and presets:
        # Wake the fireplace first, then send the presets a moment later.
        await coordinator.async_write({FN_POWER: True})
        await asyncio.sleep(POWER_SETTLE)
        await coordinator.async_write(presets)
        return

    await coordinator.async_write(values)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's services (once per Home Assistant run)."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_STATE):
        return

    async def _handle_set_state(call: ServiceCall) -> None:
        for coordinator in _target_coordinators(hass, call):
            await _async_apply(coordinator, call)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_STATE, _handle_set_state, schema=SET_STATE_SCHEMA
    )
