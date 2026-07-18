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
    DEFAULT_PRESET_MODES,
    FN_CURRENT_TEMP,
    FN_HEAT,
    FN_POWER,
    FN_PRESET,
    FN_TARGET_TEMP,
)
from .entity import ScandiaEntity
from .helpers import get_temp_range


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fireplace climate entity."""
    async_add_entities([ScandiaClimate(entry.runtime_data, entry)])


class ScandiaClimate(ScandiaEntity, ClimateEntity):
    """Represent the fireplace as a heater with an optional flame-only mode."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1.0
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Configure features from the available functions."""
        super().__init__(coordinator)
        self._has_heat = coordinator.configured(FN_HEAT)
        self._has_preset = coordinator.configured(FN_PRESET) and coordinator.present(
            FN_PRESET
        )
        self._attr_unique_id = f"{coordinator.device_id}_climate"
        self._attr_min_temp, self._attr_max_temp = get_temp_range(entry)

        if self._has_heat:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY]
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

        features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if coordinator.configured(FN_TARGET_TEMP):
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self._has_preset:
            features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = list(DEFAULT_PRESET_MODES)
        self._attr_supported_features = features

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current operating mode."""
        if not bool(self.coordinator.read(FN_POWER)):
            return HVACMode.OFF
        if self._has_heat and not bool(self.coordinator.read(FN_HEAT)):
            return HVACMode.FAN_ONLY
        return HVACMode.HEAT

    @property
    def current_temperature(self) -> float | None:
        """Return the measured room temperature."""
        value = self.coordinator.read(FN_CURRENT_TEMP)
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        value = self.coordinator.read(FN_TARGET_TEMP)
        return float(value) if value is not None else None

    @property
    def preset_mode(self) -> str | None:
        """Return the current heat preset."""
        value = self.coordinator.read(FN_PRESET)
        return str(value) if value is not None else None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Turn power on/off and toggle the heating element."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write({FN_POWER: False})
            return
        values: dict[str, Any] = {FN_POWER: True}
        if self._has_heat:
            values[FN_HEAT] = hvac_mode == HVACMode.HEAT
        await self.coordinator.async_write(values)

    async def async_turn_on(self) -> None:
        """Turn the fireplace on (heat mode)."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the fireplace off."""
        await self.coordinator.async_write({FN_POWER: False})

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None or not self.coordinator.configured(FN_TARGET_TEMP):
            return
        await self.coordinator.async_write({FN_TARGET_TEMP: int(round(temperature))})

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the heat preset."""
        if self._has_preset:
            await self.coordinator.async_write({FN_PRESET: preset_mode})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
