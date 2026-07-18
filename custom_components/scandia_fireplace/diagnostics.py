"""Diagnostics support for the Scandia Fireplace integration.

Downloading diagnostics reveals every function code the fireplace currently
reports, which is the easiest way to discover your unit's code mapping and
correct it from the integration options if the defaults are wrong.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import ScandiaConfigEntry

TO_REDACT = {"token_info", "terminal_id", "user_code", "uid"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ScandiaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    device = coordinator.device
    return {
        "config": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "device": {
            "category": getattr(device, "category", None),
            "product_name": getattr(device, "product_name", None),
            "online": getattr(device, "online", None),
        }
        if device
        else None,
        "status_codes": coordinator.data or {},
    }
