"""Diagnostics support for the Scandia Fireplace integration.

Downloading diagnostics reveals every address (Tuya code or data point) the
fireplace currently reports, which is the easiest way to discover your unit's
mapping and correct it from the integration options if the defaults are wrong.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import ScandiaConfigEntry
from .const import CONF_MODE

TO_REDACT = {"token_info", "terminal_id", "user_code", "uid", "local_key"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ScandiaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "mode": entry.data.get(CONF_MODE),
        "config": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "address_map": coordinator.addr,
        "raw_status": coordinator.data or {},
    }
