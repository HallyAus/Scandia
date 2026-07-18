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


def _cloud_error_message(cloud: Any) -> str:
    """Extract a human-readable error from a tinytuya Cloud client."""
    err = getattr(cloud, "error", None)
    if isinstance(err, dict):
        for key in ("Payload", "msg", "Err", "Error"):
            if err.get(key):
                return str(err[key])
    return "Authentication failed — check the region, Access ID and Secret."


class TuyaCloud:
    """Minimal wrapper around tinytuya.Cloud for device discovery."""

    def __init__(
        self, region: str, api_key: str, api_secret: str, sample_device_id: str
    ) -> None:
        """Create a cloud client. A sample device ID bootstraps the account."""
        try:
            self._cloud = tinytuya.Cloud(
                apiRegion=region,
                apiKey=api_key,
                apiSecret=api_secret,
                apiDeviceID=sample_device_id,
            )
        except Exception as err:  # noqa: BLE001 - e.g. missing key/secret
            raise CloudError(str(err)) from err

        # On a bad login tinytuya leaves the token unset and stashes the API
        # error (keyed by 'msg'/'Payload'/'Err') on the client.
        if not getattr(self._cloud, "token", None):
            raise CloudError(_cloud_error_message(self._cloud))

    def list_devices(self) -> list[dict[str, Any]]:
        """Return all devices on the account, each with its local key.

        Each dict contains at least ``id``, ``name`` and ``key`` (the local
        key). Protocol version is not returned by the cloud, so it is detected
        from the LAN broadcast instead.
        """
        result = self._cloud.getdevices(verbose=False)
        if not isinstance(result, list):
            # tinytuya returns an error dict rather than a list on failure.
            message = "Unknown cloud error"
            if isinstance(result, dict):
                message = (
                    result.get("msg")
                    or result.get("Error")
                    or result.get("Payload")
                    or message
                )
            raise CloudError(str(message))
        return result

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        """Return a single device record by ID, or None if not found."""
        for device in self.list_devices():
            if device.get("id") == device_id:
                return device
        return None
