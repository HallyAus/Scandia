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
    CONF_CODE_CURRENT_TEMP,
    CONF_CODE_HEAT,
    CONF_CODE_POWER,
    CONF_CODE_PRESET,
    CONF_CODE_TARGET_TEMP,
    DEFAULT_PRESET_MODES,
)
from .entity import ScandiaEntity
from .helpers import get_code, get_temp_range


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
        """Cache the code mapping for this entity."""
        super().__init__(coordinator)
        self._code_power = get_code(entry, CONF_CODE_POWER)
        self._code_heat = get_code(entry, CONF_CODE_HEAT)
        self._code_target = get_code(entry, CONF_CODE_TARGET_TEMP)
        self._code_current = get_code(entry, CONF_CODE_CURRENT_TEMP)
        self._code_preset = get_code(entry, CONF_CODE_PRESET)
        self._attr_unique_id = f"{coordinator.device_id}_climate"
        self._attr_min_temp, self._attr_max_temp = get_temp_range(entry)

        if self._code_heat is not None:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY]
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

        features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if self._code_target is not None:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE

        if self._code_preset is not None and self._code_present(self._code_preset):
            features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = list(DEFAULT_PRESET_MODES)
        else:
            self._code_preset = None

        self._attr_supported_features = features

    @property
    def _is_on(self) -> bool:
        return bool(self._code_value(self._code_power))

    @property
    def _heat_enabled(self) -> bool:
        if self._code_heat is None:
            return True
        return bool(self._code_value(self._code_heat))

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current operating mode."""
        if not self._is_on:
            return HVACMode.OFF
        if self._code_heat is not None and not self._heat_enabled:
            return HVACMode.FAN_ONLY
        return HVACMode.HEAT

    @property
    def current_temperature(self) -> float | None:
        """Return the measured room temperature."""
        value = self._code_value(self._code_current)
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        value = self._code_value(self._code_target)
        return float(value) if value is not None else None

    @property
    def preset_mode(self) -> str | None:
        """Return the current heat preset."""
        value = self._code_value(self._code_preset)
        return str(value) if value is not None else None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Turn power on/off and toggle the heating element."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_send(
                [{"code": self._code_power, "value": False}]
            )
            return

        commands: list[dict[str, Any]] = [{"code": self._code_power, "value": True}]
        if self._code_heat is not None:
            commands.append(
                {"code": self._code_heat, "value": hvac_mode == HVACMode.HEAT}
            )
        await self.coordinator.async_send(commands)

    async def async_turn_on(self) -> None:
        """Turn the fireplace on (heat mode)."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the fireplace off."""
        await self.coordinator.async_send([{"code": self._code_power, "value": False}])

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None or self._code_target is None:
            return
        await self.coordinator.async_send(
            [{"code": self._code_target, "value": int(round(temperature))}]
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the heat preset."""
        if self._code_preset is not None:
            await self.coordinator.async_send(
                [{"code": self._code_preset, "value": preset_mode}]
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
