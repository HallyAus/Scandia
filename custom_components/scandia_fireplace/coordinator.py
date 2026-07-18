"""Tuya cloud (sharing) communication and update coordinator."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

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
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_TERMINAL_ID,
    CONF_TOKEN_INFO,
    CONF_USER_CODE,
    DOMAIN,
    TUYA_CLIENT_ID,
)

_LOGGER = logging.getLogger(__name__)

# The cloud pushes changes over MQTT, so we only poll occasionally as a safety
# net in case a push is missed.
UPDATE_INTERVAL = timedelta(seconds=60)


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
            self.entry,
            data={**self.entry.data, CONF_TOKEN_INFO: token_info},
        )


def build_manager(entry: ConfigEntry, token_listener: SharingTokenListener) -> Manager:
    """Construct a tuya-sharing Manager from a config entry."""
    return Manager(
        TUYA_CLIENT_ID,
        entry.data[CONF_USER_CODE],
        entry.data[CONF_TERMINAL_ID],
        entry.data[CONF_ENDPOINT],
        entry.data[CONF_TOKEN_INFO],
        token_listener,
    )


class ScandiaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keep one fireplace's status in sync via the Tuya cloud."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, manager: Manager) -> None:
        """Set up the coordinator around an existing Manager."""
        self.entry = entry
        self.manager = manager
        self.device_id = entry.data[CONF_DEVICE_ID]
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL
        )

    @property
    def device(self) -> CustomerDevice | None:
        """Return the current device object from the manager cache."""
        return self.manager.device_map.get(self.device_id)

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh the device cache and return this device's status codes."""
        try:
            await self.hass.async_add_executor_job(self.manager.update_device_cache)
        except Exception as err:  # noqa: BLE001 - surface any cloud error
            message = str(err).lower()
            if "token" in message or "authoriz" in message or "sign" in message:
                raise ConfigEntryAuthFailed(str(err)) from err
            raise UpdateFailed(f"Error talking to Tuya cloud: {err}") from err

        device = self.device
        if device is None:
            raise UpdateFailed(
                f"Fireplace {self.device_id} is no longer on the account"
            )
        return dict(device.status)

    async def async_send(self, commands: list[dict[str, Any]]) -> None:
        """Send one or more {code, value} commands then refresh."""
        _LOGGER.debug("Sending commands %r", commands)
        await self.hass.async_add_executor_job(
            self.manager.send_commands, self.device_id, commands
        )
        await self.async_request_refresh()


class DeviceListener(SharingDeviceListener):
    """Bridge cloud push updates into the coordinator."""

    def __init__(self, coordinator: ScandiaCoordinator) -> None:
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
