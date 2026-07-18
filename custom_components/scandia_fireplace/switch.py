"""Switch platform for the Scandia Fireplace: master power."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import FN_POWER
from .entity import ScandiaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the master power switch."""
    coordinator = entry.runtime_data
    if coordinator.configured(FN_POWER):
        async_add_entities([ScandiaPower(coordinator)])


class ScandiaPower(ScandiaEntity, SwitchEntity):
    """Turn the whole fireplace (flames and heater) on or off."""

    _attr_name = None
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator) -> None:
        """Cache the entity id."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_power"

    @property
    def is_on(self) -> bool:
        """Return True when the fireplace is on."""
        return bool(self.coordinator.read(FN_POWER))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the fireplace on."""
        await self.coordinator.async_write({FN_POWER: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fireplace off."""
        await self.coordinator.async_write({FN_POWER: False})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
