"""LAN discovery of Tuya devices via their UDP broadcasts.

Used by local mode to resolve/confirm a device's IP and protocol version by
matching the device ID we already obtained from the cloud. Blocking — run
inside the executor.
"""

from __future__ import annotations

import logging

import tinytuya

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_SECONDS = 8


def scan_lan(scantime: int = DEFAULT_SCAN_SECONDS) -> dict[str, dict[str, str]]:
    """Discover Tuya devices on the LAN.

    Returns ``device_id -> {"ip": ..., "version": ...}``. Empty on failure.
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
    return result
