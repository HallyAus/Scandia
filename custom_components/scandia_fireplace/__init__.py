"""The Scandia Fireplace integration (Tuya cloud or local, QR sign-in)."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_MODE, DOMAIN, MODE_CLOUD, PLATFORMS
from .coordinator import (
    DeviceListener,
    ScandiaBaseCoordinator,
    ScandiaCloudCoordinator,
    ScandiaLocalCoordinator,
    TokenListener,
    build_manager,
)

_LOGGER = logging.getLogger(__name__)

ScandiaConfigEntry = ConfigEntry[ScandiaBaseCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ScandiaConfigEntry) -> bool:
    """Set up Scandia Fireplace from a config entry."""
    if entry.data.get(CONF_MODE) == MODE_CLOUD:
        coordinator: ScandiaBaseCoordinator = await _async_setup_cloud(hass, entry)
    else:
        coordinator = ScandiaLocalCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_setup_cloud(
    hass: HomeAssistant, entry: ScandiaConfigEntry
) -> ScandiaCloudCoordinator:
    """Build and start the cloud coordinator."""
    manager = build_manager(entry, TokenListener(hass, entry))
    coordinator = ScandiaCloudCoordinator(hass, entry, manager)
    manager.add_device_listener(DeviceListener(coordinator))

    await coordinator.async_config_entry_first_refresh()
    try:
        await hass.async_add_executor_job(manager.refresh_mq)
    except Exception as err:  # noqa: BLE001 - push is optional, we still poll
        _LOGGER.warning("Tuya push connection unavailable, will poll: %s", err)
    return coordinator


async def async_unload_entry(hass: HomeAssistant, entry: ScandiaConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: ScandiaBaseCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        if isinstance(coordinator, ScandiaCloudCoordinator):
            mq = getattr(coordinator.manager, "mq", None)
            if mq is not None:
                await hass.async_add_executor_job(mq.stop)
        elif isinstance(coordinator, ScandiaLocalCoordinator):
            await coordinator.async_shutdown()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ScandiaConfigEntry) -> None:
    """Revoke the cloud session when the integration is removed."""
    if not entry.data.get("token_info"):
        return
    manager = build_manager(entry, TokenListener(hass, entry))
    try:
        await hass.async_add_executor_job(manager.unload)
    except Exception as err:  # noqa: BLE001 - best-effort logout
        _LOGGER.debug("Error revoking Tuya session: %s", err)


async def _async_update_listener(hass: HomeAssistant, entry: ScandiaConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
