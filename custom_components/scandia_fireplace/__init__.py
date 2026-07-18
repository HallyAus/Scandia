"""The Scandia Fireplace integration (Tuya cloud, QR login)."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import (
    DeviceListener,
    ScandiaCoordinator,
    TokenListener,
    build_manager,
)

_LOGGER = logging.getLogger(__name__)

ScandiaConfigEntry = ConfigEntry[ScandiaCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ScandiaConfigEntry) -> bool:
    """Set up Scandia Fireplace from a config entry."""
    token_listener = TokenListener(hass, entry)
    manager = build_manager(entry, token_listener)

    coordinator = ScandiaCoordinator(hass, entry, manager)

    listener = DeviceListener(coordinator)
    manager.add_device_listener(listener)

    # Pull the initial device list (raises ConfigEntryNotReady on failure)...
    await coordinator.async_config_entry_first_refresh()

    # ...then start the push (MQTT) connection. Failure here is non-fatal: we
    # simply fall back to periodic polling.
    try:
        await hass.async_add_executor_job(manager.refresh_mq)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Tuya push connection unavailable, will poll: %s", err)

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ScandiaConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: ScandiaCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        mq = getattr(coordinator.manager, "mq", None)
        if mq is not None:
            await hass.async_add_executor_job(mq.stop)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ScandiaConfigEntry) -> None:
    """Revoke the cloud session when the integration is removed."""
    token_listener = TokenListener(hass, entry)
    manager = build_manager(entry, token_listener)
    try:
        await hass.async_add_executor_job(manager.unload)
    except Exception as err:  # noqa: BLE001 - best-effort logout
        _LOGGER.debug("Error revoking Tuya session: %s", err)


async def _async_update_listener(hass: HomeAssistant, entry: ScandiaConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
