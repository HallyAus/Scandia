"""Sensor platform for the Scandia Fireplace (temperature, power, energy)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import (
    CONF_DP_CURRENT_TEMP,
    CONF_DP_ENERGY,
    CONF_DP_POWER_W,
    ENERGY_DP_SCALE,
)
from .entity import ScandiaEntity
from .helpers import get_dp


@dataclass(frozen=True, kw_only=True)
class ScandiaSensorDescription(SensorEntityDescription):
    """Describes a Scandia sensor and how to derive its value."""

    dp_option: str
    scale: float = 1.0


SENSORS: tuple[ScandiaSensorDescription, ...] = (
    ScandiaSensorDescription(
        key="current_temperature",
        dp_option=CONF_DP_CURRENT_TEMP,
        translation_key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    ScandiaSensorDescription(
        key="power",
        dp_option=CONF_DP_POWER_W,
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    ScandiaSensorDescription(
        key="energy",
        dp_option=CONF_DP_ENERGY,
        scale=ENERGY_DP_SCALE,
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
    """Set up the sensors whose data point is configured."""
    coordinator = entry.runtime_data
    entities = [
        ScandiaSensor(coordinator, entry, description)
        for description in SENSORS
        if get_dp(entry, description.dp_option)
    ]
    async_add_entities(entities)


class ScandiaSensor(ScandiaEntity, SensorEntity):
    """A numeric reading derived from a single data point."""

    entity_description: ScandiaSensorDescription

    def __init__(
        self, coordinator, entry: ScandiaConfigEntry, description: ScandiaSensorDescription
    ) -> None:
        """Store the description and resolve its data point."""
        super().__init__(coordinator)
        self.entity_description = description
        self._dp = get_dp(entry, description.dp_option)
        self._attr_unique_id = f"{entry.data['device_id']}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the scaled sensor value."""
        value = self._dp_value(self._dp)
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
