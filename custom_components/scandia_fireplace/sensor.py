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
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import ENERGY_SCALE, FN_CURRENT_TEMP, FN_ENERGY, FN_POWER_W
from .entity import ScandiaEntity


@dataclass(frozen=True, kw_only=True)
class ScandiaSensorDescription(SensorEntityDescription):
    """Describes a Scandia sensor and how to derive its value."""

    function: str
    scale: float = 1.0


SENSORS: tuple[ScandiaSensorDescription, ...] = (
    ScandiaSensorDescription(
        key="current_temperature",
        function=FN_CURRENT_TEMP,
        translation_key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    ScandiaSensorDescription(
        key="power",
        function=FN_POWER_W,
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    ScandiaSensorDescription(
        key="energy",
        function=FN_ENERGY,
        scale=ENERGY_SCALE,
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
    """Set up known sensors plus a diagnostic sensor for every raw endpoint."""
    coordinator = entry.runtime_data
    async_add_entities(
        ScandiaSensor(coordinator, description)
        for description in SENSORS
        if coordinator.configured(description.function)
    )

    # Auto-discovery: surface every endpoint (Tuya code or local DP) the device
    # reports that isn't already backed by a semantic entity as a
    # disabled-by-default diagnostic sensor. Endpoints are picked up as they
    # first appear (e.g. once the fireplace is switched on).
    mapped = {str(address) for address in coordinator.addr.values()}
    discovered: set[str] = set()

    @callback
    def _discover_raw_endpoints() -> None:
        new_entities = []
        for address in coordinator.data or {}:
            key = str(address)
            if key in mapped or key in discovered:
                continue
            discovered.add(key)
            new_entities.append(ScandiaRawSensor(coordinator, address))
        if new_entities:
            async_add_entities(new_entities)

    _discover_raw_endpoints()
    entry.async_on_unload(coordinator.async_add_listener(_discover_raw_endpoints))


class ScandiaSensor(ScandiaEntity, SensorEntity):
    """A numeric reading derived from a single function."""

    entity_description: ScandiaSensorDescription

    def __init__(self, coordinator, description: ScandiaSensorDescription) -> None:
        """Store the description."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the scaled sensor value."""
        value = self.coordinator.read(self.entity_description.function)
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


class ScandiaRawSensor(ScandiaEntity, SensorEntity):
    """Diagnostic sensor exposing one raw endpoint (Tuya code or local DP).

    Disabled by default. Enable the ones you want in the entity settings, then
    watch their live values while toggling the fireplace to work out what each
    unmapped endpoint does — then map it in the integration options.
    """

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator, address: object) -> None:
        """Bind the sensor to a single raw address."""
        super().__init__(coordinator)
        self._address = address
        self._attr_unique_id = f"{coordinator.device_id}_dp_{address}"
        self._attr_name = f"Endpoint {address}"

    @property
    def native_value(self) -> str | int | float | None:
        """Return the raw value the device reports for this endpoint."""
        value = (self.coordinator.data or {}).get(self._address)
        if value is None:
            return None
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (int, float)):
            return value
        # HA rejects sensor states over 255 chars (e.g. Base64 "raw" DPs).
        return str(value)[:255]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
