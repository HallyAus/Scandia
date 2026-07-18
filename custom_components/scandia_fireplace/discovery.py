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


def scan_lan(scantime: int = DEFAULT_SCAN_SECONDS) -> dict[str, str]:
    """Return a mapping of ``device_id -> ip`` for devices found on the LAN."""
    try:
        found = tinytuya.deviceScan(False, scantime)
    except Exception as err:  # noqa: BLE001 - discovery is best-effort
        _LOGGER.debug("Tuya LAN scan failed: %s", err)
        return {}

    result: dict[str, str] = {}
    if isinstance(found, dict):
        for ip, info in found.items():
            if not isinstance(info, dict):
                continue
            device_id = info.get("id") or info.get("gwId")
            if device_id:
                result[device_id] = info.get("ip") or ip
    _LOGGER.debug("Tuya LAN scan discovered %d device(s)", len(result))
    return result
