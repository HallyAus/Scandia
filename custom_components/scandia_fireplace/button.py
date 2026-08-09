"""Button platform for the Scandia Fireplace: one button per flame preset.

Each colour the fireplace supports becomes its own button — tap it to jump
straight to that flame colour, flame-log colour, or top-light colour. The exact
presets come from the device profile; the current selection is shown by the
matching sensor.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import FN_FLAME_EFFECT, FN_FLAME_LOG, FN_TOP_LIGHT
from .entity import ScandiaEntity


@dataclass(frozen=True, kw_only=True)
class ScandiaButtonGroup:
    """A set of preset buttons for one enum function."""

    function: str
    label: str
    icon: str


BUTTON_GROUPS: tuple[ScandiaButtonGroup, ...] = (
    ScandiaButtonGroup(function=FN_FLAME_EFFECT, label="Flame", icon="mdi:fire"),
    ScandiaButtonGroup(function=FN_FLAME_LOG, label="Flame log", icon="mdi:fireplace"),
    ScandiaButtonGroup(function=FN_TOP_LIGHT, label="Top light", icon="mdi:lightbulb-on"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a button for every preset of each configured function."""
    coordinator = entry.runtime_data
    buttons = [
        ScandiaPresetButton(coordinator, group, value, label)
        for group in BUTTON_GROUPS
        if coordinator.configured(group.function)
        for value, label in coordinator.option_labels(group.function).items()
    ]
    async_add_entities(buttons)


class ScandiaPresetButton(ScandiaEntity, ButtonEntity):
    """Set one function to one fixed preset value."""

    def __init__(
        self, coordinator, group: ScandiaButtonGroup, value: str, label: str
    ) -> None:
        """Bind the button to a single (function, value) preset."""
        super().__init__(coordinator)
        self._function = group.function
        self._value = value
        self._attr_icon = group.icon
        self._attr_name = f"{group.label} {label}"
        self._attr_unique_id = f"{coordinator.device_id}_{group.function}_{value}"

    async def async_press(self) -> None:
        """Apply this preset."""
        await self.coordinator.async_write({self._function: self._value})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Buttons are stateless; nothing to refresh."""
