"""Tuya Cloud helper — used to auto-discover devices and fetch local keys.

This wraps ``tinytuya.Cloud`` so the config flow can pull each fireplace's
local key and protocol version straight from the Tuya IoT cloud, instead of the
user extracting them by hand. The key is then used for fast local LAN control.

All calls here are blocking and must run inside the executor.
"""

from __future__ import annotations

import logging
from typing import Any

import tinytuya

_LOGGER = logging.getLogger(__name__)


class CloudError(Exception):
    """Raised when the Tuya cloud request fails."""


class TuyaCloud:
    """Minimal wrapper around tinytuya.Cloud for device discovery."""

    def __init__(
        self, region: str, api_key: str, api_secret: str, sample_device_id: str
    ) -> None:
        """Create a cloud client. A sample device ID bootstraps the account."""
        self._cloud = tinytuya.Cloud(
            apiRegion=region,
            apiKey=api_key,
            apiSecret=api_secret,
            apiDeviceID=sample_device_id,
        )
        # tinytuya reports a bad login by storing an error dict on the token.
        token = getattr(self._cloud, "token", None)
        if isinstance(token, dict) and token.get("Error"):
            raise CloudError(token.get("Error", "Unknown cloud error"))

    def list_devices(self) -> list[dict[str, Any]]:
        """Return all devices on the account, each with its local key.

        Each dict contains at least ``id``, ``name``, ``key`` and (usually)
        ``version``.
        """
        result = self._cloud.getdevices(verbose=False)
        if not isinstance(result, list):
            # tinytuya returns an error dict rather than a list on failure.
            message = "Unknown cloud error"
            if isinstance(result, dict):
                message = result.get("Error") or result.get("Payload") or message
            raise CloudError(str(message))
        return result

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        """Return a single device record by ID, or None if not found."""
        for device in self.list_devices():
            if device.get("id") == device_id:
                return device
        return None
