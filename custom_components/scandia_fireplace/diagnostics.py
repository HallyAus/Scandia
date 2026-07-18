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
from .const import CONF_DEVICE_ID, CONF_MODE, CONF_TOKEN_INFO
from .coordinator import ScandiaCloudCoordinator, TokenListener, build_manager

TO_REDACT = {"token_info", "terminal_id", "user_code", "uid", "local_key"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ScandiaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    diagnostics: dict[str, Any] = {
        "mode": entry.data.get(CONF_MODE),
        "config": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "address_map": coordinator.addr,
        "raw_status": coordinator.data or {},
    }
    spec = await _async_endpoint_spec(hass, entry, coordinator)
    if spec:
        diagnostics["endpoint_spec"] = spec
    return diagnostics


async def _async_endpoint_spec(
    hass: HomeAssistant, entry: ScandiaConfigEntry, coordinator: Any
) -> dict[str, Any] | None:
    """Fetch the full Tuya function/status spec (every endpoint) from the cloud.

    Works in local mode too, using the stored cloud token. Best-effort — any
    failure just omits the extra detail rather than breaking diagnostics.
    """
    device = None
    try:
        if isinstance(coordinator, ScandiaCloudCoordinator):
            device = coordinator.device
        elif entry.data.get(CONF_TOKEN_INFO):
            manager = build_manager(entry, TokenListener(hass, None))
            await hass.async_add_executor_job(manager.update_device_cache)
            device = manager.device_map.get(entry.data[CONF_DEVICE_ID])
    except Exception:  # noqa: BLE001 - diagnostics must never raise
        return None

    if device is None:
        return None
    return {
        "product_name": getattr(device, "product_name", None),
        "category": getattr(device, "category", None),
        "functions": _serialise_spec(getattr(device, "function", None)),
        "status_range": _serialise_spec(getattr(device, "status_range", None)),
        "cloud_status": dict(getattr(device, "status", {}) or {}),
    }


def _serialise_spec(spec_map: Any) -> dict[str, Any]:
    """Turn a Tuya function/status-range map into plain JSON-safe dicts."""
    result: dict[str, Any] = {}
    for code, item in (spec_map or {}).items():
        result[code] = {
            "type": getattr(item, "type", None),
            "values": getattr(item, "values", None),
        }
    return result
