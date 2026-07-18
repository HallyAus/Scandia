"""Select platform for the Scandia Fireplace: heater and countdown timer.

Both are enum settings on the device (Off/Lo/Hi and Cancel/1h-6h) where seeing
the current value matters, so they read best as dropdowns rather than buttons.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import FN_HEAT, FN_TIMER, HEATER_OPTIONS, TIMER_OPTIONS
from .entity import ScandiaEntity


@dataclass(frozen=True, kw_only=True)
class ScandiaSelectDescription(SelectEntityDescription):
    """Describes a Scandia enum select and its raw-value <-> label map."""

    function: str
    value_labels: dict[str, str]


SELECTS: tuple[ScandiaSelectDescription, ...] = (
    ScandiaSelectDescription(
        key="heater",
        function=FN_HEAT,
        value_labels=HEATER_OPTIONS,
        name="Heater",
        icon="mdi:radiator",
    ),
    ScandiaSelectDescription(
        key="timer",
        function=FN_TIMER,
        value_labels=TIMER_OPTIONS,
        name="Timer",
        icon="mdi:timer-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the selects whose function is configured."""
    coordinator = entry.runtime_data
    async_add_entities(
        ScandiaSelect(coordinator, description)
        for description in SELECTS
        if coordinator.configured(description.function)
    )


class ScandiaSelect(ScandiaEntity, SelectEntity):
    """A dropdown backed by a single enum function."""

    entity_description: ScandiaSelectDescription

    def __init__(self, coordinator, description: ScandiaSelectDescription) -> None:
        """Build the option list and the reverse label -> value map."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"
        self._attr_options = list(description.value_labels.values())
        self._label_to_value = {
            label: value for value, label in description.value_labels.items()
        }

    @property
    def current_option(self) -> str | None:
        """Return the friendly label for the device's current value."""
        value = self.coordinator.read(self.entity_description.function)
        if value is None:
            return None
        return self.entity_description.value_labels.get(str(value))

    async def async_select_option(self, option: str) -> None:
        """Write the raw value for the chosen label."""
        value = self._label_to_value.get(option)
        if value is not None:
            await self.coordinator.async_write({self.entity_description.function: value})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
