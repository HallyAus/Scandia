"""Local Tuya communication and update coordinator for Scandia Fireplace."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import tinytuya

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_SCAN_INTERVAL,
    DEFAULT_PROTOCOL_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ScandiaDevice:
    """Thin, thread-safe wrapper around a tinytuya local device.

    tinytuya is blocking, so every call is expected to run inside the executor
    (via ``hass.async_add_executor_job``). A persistent socket is reused so we
    avoid the reconnect penalty on every poll.
    """

    def __init__(
        self,
        device_id: str,
        host: str,
        local_key: str,
        protocol_version: str,
    ) -> None:
        """Initialise the underlying tinytuya device."""
        self._device = tinytuya.Device(device_id, host, local_key)
        try:
            self._device.set_version(float(protocol_version))
        except (TypeError, ValueError):
            self._device.set_version(float(DEFAULT_PROTOCOL_VERSION))
        # Keep the connection open between polls for snappy updates.
        self._device.set_socketPersistent(True)
        self._device.set_socketTimeout(5)

    def status(self) -> dict[str, Any]:
        """Return the raw ``dps`` mapping reported by the device."""
        data = self._device.status()
        if not isinstance(data, dict) or "dps" not in data:
            raise UpdateFailed(f"Unexpected response from fireplace: {data!r}")
        return data["dps"]

    def set_dp(self, dp: str, value: Any) -> dict[str, Any]:
        """Set a single data point and return the device response."""
        _LOGGER.debug("Setting DP %s = %r", dp, value)
        return self._device.set_value(dp, value, nowait=False)

    def set_multiple(self, values: dict[str, Any]) -> dict[str, Any]:
        """Set several data points in a single command."""
        _LOGGER.debug("Setting DPs %r", values)
        return self._device.set_multiple_values(values, nowait=False)

    def close(self) -> None:
        """Close the persistent socket."""
        try:
            self._device.close()
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass


class ScandiaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the fireplace and cache the current data points."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Set up the coordinator from a config entry."""
        self.entry = entry
        options = {**entry.data, **entry.options}
        scan_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        self.device = ScandiaDevice(
            device_id=entry.data[CONF_DEVICE_ID],
            host=entry.data[CONF_HOST],
            local_key=entry.data[CONF_LOCAL_KEY],
            protocol_version=entry.data.get(
                CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION
            ),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data points from the fireplace."""
        try:
            return await self.hass.async_add_executor_job(self.device.status)
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001 - surface any local error
            raise UpdateFailed(f"Error communicating with fireplace: {err}") from err

    async def async_set_dp(self, dp: str, value: Any) -> None:
        """Set a data point then refresh so entities reflect the new state."""
        await self.hass.async_add_executor_job(self.device.set_dp, dp, value)
        await self.async_request_refresh()

    async def async_set_multiple(self, values: dict[str, Any]) -> None:
        """Set several data points at once then refresh."""
        await self.hass.async_add_executor_job(self.device.set_multiple, values)
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Close the connection on unload."""
        await super().async_shutdown()
        await self.hass.async_add_executor_job(self.device.close)
