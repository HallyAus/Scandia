"""Select platform for the Scandia Fireplace flame animation speed."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import DEFAULT_FLAME_SPEEDS, FN_FLAME_SPEED
from .entity import ScandiaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the flame-speed select if the device exposes it."""
    coordinator = entry.runtime_data
    if coordinator.configured(FN_FLAME_SPEED):
        async_add_entities([ScandiaFlameSpeed(coordinator, entry)])


class ScandiaFlameSpeed(ScandiaEntity, SelectEntity):
    """Control the flame animation speed."""

    _attr_translation_key = "flame_speed"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Cache the available options."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_flame_speed"
        self._attr_options = list(DEFAULT_FLAME_SPEEDS)

    @property
    def current_option(self) -> str | None:
        """Return the current flame speed."""
        value = self.coordinator.read(FN_FLAME_SPEED)
        return str(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        """Change the flame speed."""
        await self.coordinator.async_write({FN_FLAME_SPEED: option})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
