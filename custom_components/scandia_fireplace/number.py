"""Number platform for the Scandia Fireplace countdown timer."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import FN_TIMER
from .entity import ScandiaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the countdown-timer number if the device exposes it."""
    coordinator = entry.runtime_data
    if coordinator.configured(FN_TIMER):
        async_add_entities([ScandiaTimer(coordinator, entry)])


class ScandiaTimer(ScandiaEntity, NumberEntity):
    """Set the auto-off countdown timer, in hours."""

    _attr_translation_key = "timer"
    _attr_icon = "mdi:timer-outline"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Cache the entity id."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_timer"

    @property
    def native_value(self) -> float | None:
        """Return the currently set timer value."""
        value = self.coordinator.read(FN_TIMER)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the countdown timer."""
        await self.coordinator.async_write({FN_TIMER: int(value)})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
