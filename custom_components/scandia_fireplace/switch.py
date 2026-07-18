"""Switch platform for the Scandia Fireplace child lock."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import FN_CHILD_LOCK
from .entity import ScandiaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the child-lock switch if the device exposes it."""
    coordinator = entry.runtime_data
    if coordinator.configured(FN_CHILD_LOCK):
        async_add_entities([ScandiaChildLock(coordinator, entry)])


class ScandiaChildLock(ScandiaEntity, SwitchEntity):
    """Toggle the fireplace's child lock."""

    _attr_translation_key = "child_lock"
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Cache the entity id."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_child_lock"

    @property
    def is_on(self) -> bool:
        """Return True when the child lock is engaged."""
        return bool(self.coordinator.read(FN_CHILD_LOCK))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Engage the child lock."""
        await self.coordinator.async_write({FN_CHILD_LOCK: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Release the child lock."""
        await self.coordinator.async_write({FN_CHILD_LOCK: False})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
