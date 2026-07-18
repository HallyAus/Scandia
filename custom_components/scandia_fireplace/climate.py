"""Climate platform for the Scandia Fireplace (power, heat, temperature)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import (
    CONF_DP_CURRENT_TEMP,
    CONF_DP_HEAT,
    CONF_DP_POWER,
    CONF_DP_TARGET_TEMP,
)
from .entity import ScandiaEntity
from .helpers import get_dp, get_temp_range


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fireplace climate entity."""
    async_add_entities([ScandiaClimate(entry.runtime_data, entry)])


class ScandiaClimate(ScandiaEntity, ClimateEntity):
    """Represent the fireplace as a heater with an optional fan-only (flame) mode."""

    _attr_name = None  # primary entity uses the device name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1.0
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Cache the DP mapping for this entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._dp_power = get_dp(entry, CONF_DP_POWER)
        self._dp_heat = get_dp(entry, CONF_DP_HEAT)
        self._dp_target = get_dp(entry, CONF_DP_TARGET_TEMP)
        self._dp_current = get_dp(entry, CONF_DP_CURRENT_TEMP)
        self._attr_unique_id = f"{entry.data['device_id']}_climate"
        self._attr_min_temp, self._attr_max_temp = get_temp_range(entry)

        # A dedicated heat DP means we can offer a flame-only (fan_only) mode.
        if self._dp_heat is not None:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY]
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

        features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if self._dp_target is not None:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_supported_features = features

    @property
    def _is_on(self) -> bool:
        return bool(self._dp_value(self._dp_power))

    @property
    def _heat_enabled(self) -> bool:
        """Whether the heating element is active. Defaults to on when no heat DP."""
        if self._dp_heat is None:
            return True
        return bool(self._dp_value(self._dp_heat))

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current operating mode."""
        if not self._is_on:
            return HVACMode.OFF
        if self._dp_heat is not None and not self._heat_enabled:
            return HVACMode.FAN_ONLY
        return HVACMode.HEAT

    @property
    def current_temperature(self) -> float | None:
        """Return the measured room temperature."""
        value = self._dp_value(self._dp_current)
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        value = self._dp_value(self._dp_target)
        return float(value) if value is not None else None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Turn power on/off and toggle the heating element."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_dp(self._dp_power, False)
            return

        updates: dict[str, Any] = {self._dp_power: True}
        if self._dp_heat is not None:
            updates[self._dp_heat] = hvac_mode == HVACMode.HEAT
        await self.coordinator.async_set_multiple(updates)

    async def async_turn_on(self) -> None:
        """Turn the fireplace on (heat mode)."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the fireplace off."""
        await self.coordinator.async_set_dp(self._dp_power, False)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None or self._dp_target is None:
            return
        await self.coordinator.async_set_dp(self._dp_target, int(round(temperature)))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
