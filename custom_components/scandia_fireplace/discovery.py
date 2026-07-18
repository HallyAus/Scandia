"""LAN discovery of Tuya devices via their UDP broadcasts.

Tuya devices continuously advertise themselves on the local network (UDP ports
6666/6667/7000). This lets us resolve a device's IP address automatically by
matching the device ID we already obtained from the cloud, so the user doesn't
have to look it up in their router. Blocking — run inside the executor.
"""

from __future__ import annotations

import logging

import tinytuya

_LOGGER = logging.getLogger(__name__)

# Broadcasts arrive every few seconds; a short listen window is usually enough.
DEFAULT_SCAN_SECONDS = 8


def scan_lan(scantime: int = DEFAULT_SCAN_SECONDS) -> dict[str, dict[str, str]]:
    """Discover Tuya devices on the LAN.

    Returns a mapping of ``device_id -> {"ip": ..., "version": ...}``. The IP
    and (authoritative) protocol version come from the device's own broadcast,
    so both can be pre-filled during setup. Empty on failure.
    """
    try:
        found = tinytuya.deviceScan(False, scantime)
    except Exception as err:  # noqa: BLE001 - discovery is best-effort
        _LOGGER.debug("Tuya LAN scan failed: %s", err)
        return {}

    result: dict[str, dict[str, str]] = {}
    if isinstance(found, dict):
        for ip, info in found.items():
            if not isinstance(info, dict):
                continue
            device_id = info.get("id") or info.get("gwId")
            if not device_id:
                continue
            entry: dict[str, str] = {"ip": info.get("ip") or ip}
            if info.get("version"):
                entry["version"] = str(info["version"])
            result[device_id] = entry
    _LOGGER.debug("Tuya LAN scan discovered %d device(s)", len(result))
    return result
