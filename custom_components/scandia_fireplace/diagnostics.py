"""Diagnostics support for the Scandia Fireplace integration.

Downloading diagnostics reveals every raw data point (DP) the fireplace is
currently reporting, which is the easiest way to discover your unit's DP
mapping and correct it from the integration options if the defaults are wrong.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import ScandiaConfigEntry

TO_REDACT = {"local_key", "device_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ScandiaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "config": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "raw_data_points": coordinator.data or {},
    }
