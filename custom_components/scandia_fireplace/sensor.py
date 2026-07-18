"""Sensor platform for the Scandia Fireplace.

Two kinds of sensors:

* State sensors that show the current flame / flame-log / top-light colour, so
  the per-preset buttons have live feedback.
* Auto-discovered diagnostic sensors: one (disabled by default) for every raw
  endpoint the device reports that isn't already backed by another entity.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import (
    FLAME_EFFECT_OPTIONS,
    FLAME_LOG_OPTIONS,
    FN_FLAME_EFFECT,
    FN_FLAME_LOG,
    FN_TOP_LIGHT,
    TOP_LIGHT_OPTIONS,
)
from .entity import ScandiaEntity


@dataclass(frozen=True, kw_only=True)
class ScandiaStateSensorDescription(SensorEntityDescription):
    """Describes a sensor that shows the current label of an enum function."""

    function: str
    value_labels: dict[str, str]


STATE_SENSORS: tuple[ScandiaStateSensorDescription, ...] = (
    ScandiaStateSensorDescription(
        key="flame_colour",
        function=FN_FLAME_EFFECT,
        value_labels=FLAME_EFFECT_OPTIONS,
        name="Flame colour",
        icon="mdi:fire",
    ),
    ScandiaStateSensorDescription(
        key="flame_log_colour",
        function=FN_FLAME_LOG,
        value_labels=FLAME_LOG_OPTIONS,
        name="Flame log colour",
        icon="mdi:fireplace",
    ),
    ScandiaStateSensorDescription(
        key="top_light_colour",
        function=FN_TOP_LIGHT,
        value_labels=TOP_LIGHT_OPTIONS,
        name="Top light colour",
        icon="mdi:lightbulb-on",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up state sensors plus a diagnostic sensor for every raw endpoint."""
    coordinator = entry.runtime_data
    async_add_entities(
        ScandiaStateSensor(coordinator, description)
        for description in STATE_SENSORS
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


class ScandiaStateSensor(ScandiaEntity, SensorEntity):
    """Shows the current friendly label for an enum function."""

    entity_description: ScandiaStateSensorDescription

    def __init__(
        self, coordinator, description: ScandiaStateSensorDescription
    ) -> None:
        """Store the description."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"

    @property
    def native_value(self) -> str | None:
        """Return the label for the current raw value."""
        value = self.coordinator.read(self.entity_description.function)
        if value is None:
            return None
        return self.entity_description.value_labels.get(str(value), str(value))

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
