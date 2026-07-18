"""Sensor platform for the Scandia Fireplace (temperature, power, energy)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import (
    CONF_CODE_CURRENT_TEMP,
    CONF_CODE_ENERGY,
    CONF_CODE_POWER_W,
    ENERGY_CODE_SCALE,
)
from .entity import ScandiaEntity
from .helpers import get_code


@dataclass(frozen=True, kw_only=True)
class ScandiaSensorDescription(SensorEntityDescription):
    """Describes a Scandia sensor and how to derive its value."""

    code_option: str
    scale: float = 1.0


SENSORS: tuple[ScandiaSensorDescription, ...] = (
    ScandiaSensorDescription(
        key="current_temperature",
        code_option=CONF_CODE_CURRENT_TEMP,
        translation_key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    ScandiaSensorDescription(
        key="power",
        code_option=CONF_CODE_POWER_W,
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    ScandiaSensorDescription(
        key="energy",
        code_option=CONF_CODE_ENERGY,
        scale=ENERGY_CODE_SCALE,
        translation_key="energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors whose function code is configured."""
    coordinator = entry.runtime_data
    async_add_entities(
        ScandiaSensor(coordinator, entry, description)
        for description in SENSORS
        if get_code(entry, description.code_option)
    )


class ScandiaSensor(ScandiaEntity, SensorEntity):
    """A numeric reading derived from a single function code."""

    entity_description: ScandiaSensorDescription

    def __init__(
        self, coordinator, entry: ScandiaConfigEntry, description: ScandiaSensorDescription
    ) -> None:
        """Store the description and resolve its function code."""
        super().__init__(coordinator)
        self.entity_description = description
        self._code = get_code(entry, description.code_option)
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the scaled sensor value."""
        value = self._code_value(self._code)
        if value is None:
            return None
        try:
            return round(float(value) * self.entity_description.scale, 2)
        except (TypeError, ValueError):
            return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
