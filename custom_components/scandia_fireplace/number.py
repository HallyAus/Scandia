"""Number platform for the Scandia Fireplace countdown timer."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import CONF_DP_TIMER
from .entity import ScandiaEntity
from .helpers import get_dp


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the countdown-timer number if the device exposes it."""
    if get_dp(entry, CONF_DP_TIMER):
        async_add_entities([ScandiaTimer(entry.runtime_data, entry)])


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
        """Cache the timer DP."""
        super().__init__(coordinator)
        self._dp_timer = get_dp(entry, CONF_DP_TIMER)
        self._attr_unique_id = f"{entry.data['device_id']}_timer"

    @property
    def native_value(self) -> float | None:
        """Return the currently set timer value."""
        value = self._dp_value(self._dp_timer)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the countdown timer."""
        await self.coordinator.async_set_dp(self._dp_timer, int(value))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
