"""Local Tuya communication and update coordinator for Scandia Fireplace."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import tinytuya

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cloud import CloudError, TuyaCloud
from .const import (
    CONF_CLOUD_API_KEY,
    CONF_CLOUD_API_SECRET,
    CONF_CLOUD_REGION,
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


def _make_device(
    device_id: str, host: str, local_key: str, protocol_version: str
) -> tinytuya.Device:
    """Create and configure a tinytuya device object."""
    device = tinytuya.Device(device_id, host, local_key)
    try:
        device.set_version(float(protocol_version))
    except (TypeError, ValueError):
        device.set_version(float(DEFAULT_PROTOCOL_VERSION))
    return device


def test_local_connection(
    device_id: str, host: str, local_key: str, protocol_version: str
) -> dict[str, Any]:
    """Attempt a local status read and return the raw dps. Runs in executor."""
    device = _make_device(device_id, host, local_key, protocol_version)
    device.set_socketTimeout(5)
    data = device.status()
    device.close()
    if not isinstance(data, dict) or "dps" not in data:
        raise ConnectionError(f"Unexpected response from fireplace: {data!r}")
    return data["dps"]


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
        self._device = _make_device(device_id, host, local_key, protocol_version)
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
        merged = {**entry.data, **entry.options}
        scan_interval = merged.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        self.device = ScandiaDevice(
            device_id=entry.data[CONF_DEVICE_ID],
            host=entry.data[CONF_HOST],
            local_key=entry.data[CONF_LOCAL_KEY],
            protocol_version=entry.data.get(
                CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION
            ),
        )
        self._refresh_attempted = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data points, refreshing the key if needed."""
        try:
            data = await self.hass.async_add_executor_job(self.device.status)
        except Exception as first_err:  # noqa: BLE001
            # A stale local key (e.g. after re-pairing in the app) looks like a
            # connection failure. Try to pull a fresh key from the cloud once,
            # then retry before giving up.
            if not self._refresh_attempted and await self._async_refresh_local_key():
                self._refresh_attempted = True
                try:
                    data = await self.hass.async_add_executor_job(self.device.status)
                except Exception as retry_err:  # noqa: BLE001
                    raise UpdateFailed(
                        f"Error communicating with fireplace: {retry_err}"
                    ) from retry_err
            else:
                raise UpdateFailed(
                    f"Error communicating with fireplace: {first_err}"
                ) from first_err

        self._refresh_attempted = False
        return data

    async def _async_refresh_local_key(self) -> bool:
        """Re-fetch the local key from the Tuya cloud. Returns True if changed."""
        region = self.entry.data.get(CONF_CLOUD_REGION)
        api_key = self.entry.data.get(CONF_CLOUD_API_KEY)
        api_secret = self.entry.data.get(CONF_CLOUD_API_SECRET)
        device_id = self.entry.data[CONF_DEVICE_ID]
        if not (region and api_key and api_secret):
            return False

        try:
            cloud = await self.hass.async_add_executor_job(
                TuyaCloud, region, api_key, api_secret, device_id
            )
            device = await self.hass.async_add_executor_job(
                cloud.get_device, device_id
            )
        except (CloudError, Exception) as err:  # noqa: BLE001
            _LOGGER.debug("Could not refresh local key from cloud: %s", err)
            return False

        new_key = (device or {}).get("key")
        if not new_key or new_key == self.entry.data[CONF_LOCAL_KEY]:
            return False

        _LOGGER.info("Refreshed local key for %s from Tuya cloud", device_id)
        self.hass.config_entries.async_update_entry(
            self.entry, data={**self.entry.data, CONF_LOCAL_KEY: new_key}
        )
        await self.hass.async_add_executor_job(self.device.close)
        self.device = ScandiaDevice(
            device_id=device_id,
            host=self.entry.data[CONF_HOST],
            local_key=new_key,
            protocol_version=self.entry.data.get(
                CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION
            ),
        )
        return True

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
