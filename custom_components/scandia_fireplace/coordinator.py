"""Coordinators for the Scandia Fireplace: shared base + cloud and local."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import tinytuya
from tuya_sharing import (
    CustomerDevice,
    Manager,
    SharingDeviceListener,
    SharingTokenListener,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CLOUD_DEFAULTS,
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_MODE,
    CONF_PROTOCOL_VERSION,
    CONF_TERMINAL_ID,
    CONF_TOKEN_INFO,
    CONF_USER_CODE,
    DEFAULT_PROTOCOL_VERSION,
    DOMAIN,
    FUNCTIONS,
    LOCAL_DEFAULTS,
    MODE_CLOUD,
    OPTION_KEY,
    TUYA_CLIENT_ID,
)
from .discovery import scan_lan

_LOGGER = logging.getLogger(__name__)

CLOUD_INTERVAL = timedelta(seconds=60)
LOCAL_INTERVAL = timedelta(seconds=30)


def build_address_map(entry: ConfigEntry) -> dict[str, str]:
    """Resolve semantic function -> address (code or DP) from the options."""
    defaults = (
        CLOUD_DEFAULTS if entry.data.get(CONF_MODE) == MODE_CLOUD else LOCAL_DEFAULTS
    )
    addr: dict[str, str] = {}
    for fn in FUNCTIONS:
        raw = entry.options.get(OPTION_KEY[fn], defaults[fn])
        text = str(raw).strip() if raw is not None else ""
        if text:
            addr[fn] = text
    return addr


class ScandiaBaseCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Common semantic read/write layer shared by both connection modes."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, interval: timedelta
    ) -> None:
        """Set up the shared address map."""
        self.entry = entry
        self.device_id = entry.data[CONF_DEVICE_ID]
        self.addr = build_address_map(entry)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=interval)

    # -- semantic access ----------------------------------------------------
    def configured(self, fn: str) -> bool:
        """Return True if this function is mapped to an address."""
        return fn in self.addr

    def read(self, fn: str) -> Any:
        """Return the current value of a function, or None."""
        if self.data is None or fn not in self.addr:
            return None
        return self.data.get(self.addr[fn])

    def present(self, fn: str) -> bool:
        """Return True if the device currently reports this function."""
        return (
            self.data is not None
            and fn in self.addr
            and self.addr[fn] in self.data
        )

    async def async_write(self, values: dict[str, Any]) -> None:
        """Write one or more semantic function values, then refresh."""
        addr_values = {
            self.addr[fn]: value for fn, value in values.items() if fn in self.addr
        }
        if not addr_values:
            return
        await self._send(addr_values)
        await self.async_request_refresh()

    async def _send(self, addr_values: dict[str, Any]) -> None:
        """Send address->value pairs to the device (mode-specific)."""
        raise NotImplementedError

    # -- device info --------------------------------------------------------
    @property
    def device_online(self) -> bool:
        """Whether the device is considered reachable."""
        return True

    @property
    def device_model(self) -> str | None:
        """Model string for the device registry, if known."""
        return self.entry.data.get("model") or None


# ---------------------------------------------------------------------------
# Cloud (Tuya sharing) mode
# ---------------------------------------------------------------------------
class TokenListener(SharingTokenListener):
    """Persist refreshed OAuth tokens back onto the config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry | None) -> None:
        """Store references needed to update the entry."""
        self.hass = hass
        self.entry = entry

    def update_token(self, token_info: dict[str, Any]) -> None:
        """Save a refreshed token (no-op during the transient setup flow)."""
        if self.entry is None:
            return
        self.hass.config_entries.async_update_entry(
            self.entry, data={**self.entry.data, CONF_TOKEN_INFO: token_info}
        )


def build_manager(entry: ConfigEntry, token_listener: SharingTokenListener) -> Manager:
    """Construct a tuya-sharing Manager from a config entry (or stub)."""
    return Manager(
        TUYA_CLIENT_ID,
        entry.data[CONF_USER_CODE],
        entry.data[CONF_TERMINAL_ID],
        entry.data[CONF_ENDPOINT],
        entry.data[CONF_TOKEN_INFO],
        token_listener,
    )


class ScandiaCloudCoordinator(ScandiaBaseCoordinator):
    """Control the fireplace through the Tuya cloud."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, manager: Manager) -> None:
        """Set up around an existing Manager."""
        self.manager = manager
        super().__init__(hass, entry, CLOUD_INTERVAL)

    @property
    def device(self) -> CustomerDevice | None:
        """Return the device object from the manager cache."""
        return self.manager.device_map.get(self.device_id)

    @property
    def device_online(self) -> bool:
        """Reflect the cloud-reported online state."""
        device = self.device
        return bool(device.online) if device else False

    @property
    def device_model(self) -> str | None:
        """Prefer the cloud product name for the model."""
        device = self.device
        return (device.product_name if device else None) or super().device_model

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh the device cache and return this device's status codes."""
        try:
            await self.hass.async_add_executor_job(self.manager.update_device_cache)
        except Exception as err:  # noqa: BLE001
            message = str(err).lower()
            if "token" in message or "authoriz" in message or "sign" in message:
                raise ConfigEntryAuthFailed(str(err)) from err
            raise UpdateFailed(f"Error talking to Tuya cloud: {err}") from err

        device = self.device
        if device is None:
            raise UpdateFailed(f"Fireplace {self.device_id} is no longer on the account")
        return dict(device.status)

    async def _send(self, addr_values: dict[str, Any]) -> None:
        commands = [{"code": code, "value": value} for code, value in addr_values.items()]
        await self.hass.async_add_executor_job(
            self.manager.send_commands, self.device_id, commands
        )


class DeviceListener(SharingDeviceListener):
    """Bridge cloud push updates into the coordinator."""

    def __init__(self, coordinator: ScandiaCloudCoordinator) -> None:
        """Store the coordinator to notify on updates."""
        self.coordinator = coordinator

    def update_device(
        self, device: CustomerDevice, dp_ids: list[str] | None = None
    ) -> None:
        """Handle a pushed status change for our device."""
        if device.id == self.coordinator.device_id:
            self.coordinator.hass.add_job(
                self.coordinator.async_set_updated_data, dict(device.status)
            )

    def add_device(self, device: CustomerDevice) -> None:
        """Ignore devices added elsewhere."""

    def remove_device(self, device_id: str) -> None:
        """Ignore devices removed elsewhere."""


# ---------------------------------------------------------------------------
# Local (tinytuya) mode
# ---------------------------------------------------------------------------
def _make_local_device(
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
    device = _make_local_device(device_id, host, local_key, protocol_version)
    device.set_socketTimeout(5)
    data = device.status()
    device.close()
    if not isinstance(data, dict) or "dps" not in data:
        raise ConnectionError(f"Unexpected response from fireplace: {data!r}")
    return data["dps"]


class ScandiaLocalCoordinator(ScandiaBaseCoordinator):
    """Control the fireplace directly over the LAN via tinytuya."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Open a persistent local connection."""
        super().__init__(hass, entry, LOCAL_INTERVAL)
        self._device = self._new_device()
        self._device.set_socketPersistent(True)
        self._recover_attempted = False

    def _new_device(self) -> tinytuya.Device:
        device = _make_local_device(
            self.entry.data[CONF_DEVICE_ID],
            self.entry.data[CONF_HOST],
            self.entry.data[CONF_LOCAL_KEY],
            self.entry.data.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION),
        )
        device.set_socketTimeout(5)
        return device

    def _status(self) -> dict[str, Any]:
        data = self._device.status()
        if not isinstance(data, dict) or "dps" not in data:
            raise UpdateFailed(f"Unexpected response from fireplace: {data!r}")
        return data["dps"]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.hass.async_add_executor_job(self._status)
        except Exception as first_err:  # noqa: BLE001
            # A dropped connection usually means the fireplace moved to a new
            # DHCP IP, or its local key changed after re-pairing. Re-discover
            # the IP on the LAN and refresh the key from the cloud once, then
            # retry before giving up.
            if not self._recover_attempted and await self._async_recover():
                self._recover_attempted = True
                try:
                    data = await self.hass.async_add_executor_job(self._status)
                except Exception as retry_err:  # noqa: BLE001
                    raise UpdateFailed(
                        f"Error communicating with fireplace: {retry_err}"
                    ) from retry_err
            else:
                raise UpdateFailed(
                    f"Error communicating with fireplace: {first_err}"
                ) from first_err
        self._recover_attempted = False
        return data

    async def _async_recover(self) -> bool:
        """Try to restore a lost local connection.

        Re-discovers the device's current IP on the LAN and refreshes its local
        key from the cloud. Rebuilds the socket if either changed. Returns True
        when something changed and a retry is worthwhile.
        """
        host_changed = await self._async_rediscover_host()
        key_changed = await self._async_refresh_local_key()
        if not (host_changed or key_changed):
            return False
        await self.hass.async_add_executor_job(self._device.close)
        self._device = self._new_device()
        self._device.set_socketPersistent(True)
        return True

    async def _async_rediscover_host(self) -> bool:
        """Scan the LAN for the device's current IP. Returns True if it moved."""
        found = await self.hass.async_add_executor_job(scan_lan)
        info = found.get(self.device_id)
        new_host = info.get("ip") if info else None
        if not new_host or new_host == self.entry.data.get(CONF_HOST):
            return False

        _LOGGER.info(
            "Rediscovered fireplace %s at new IP %s", self.device_id, new_host
        )
        self.hass.config_entries.async_update_entry(
            self.entry, data={**self.entry.data, CONF_HOST: new_host}
        )
        return True

    async def _async_refresh_local_key(self) -> bool:
        """Re-fetch the local key from the Tuya cloud. Returns True if changed."""
        if not self.entry.data.get(CONF_TOKEN_INFO):
            return False
        try:
            manager = build_manager(self.entry, TokenListener(self.hass, None))
            await self.hass.async_add_executor_job(manager.update_device_cache)
            device = manager.device_map.get(self.device_id)
        except Exception as err:  # noqa: BLE001 - best-effort
            _LOGGER.debug("Could not refresh local key from cloud: %s", err)
            return False

        new_key = getattr(device, "local_key", None)
        if not new_key or new_key == self.entry.data[CONF_LOCAL_KEY]:
            return False

        _LOGGER.info("Refreshed local key for %s from Tuya cloud", self.device_id)
        self.hass.config_entries.async_update_entry(
            self.entry, data={**self.entry.data, CONF_LOCAL_KEY: new_key}
        )
        return True

    async def _send(self, addr_values: dict[str, Any]) -> None:
        await self.hass.async_add_executor_job(
            self._device.set_multiple_values, addr_values
        )

    async def async_shutdown(self) -> None:
        """Close the local socket on unload."""
        await super().async_shutdown()
        await self.hass.async_add_executor_job(self._device.close)
