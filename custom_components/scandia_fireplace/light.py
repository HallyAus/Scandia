"""Light platform for the Scandia Fireplace flame effect."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScandiaConfigEntry
from .const import (
    CONF_DP_FLAME_BRIGHTNESS,
    CONF_DP_FLAME_EFFECT,
    CONF_DP_POWER,
    DEFAULT_FLAME_EFFECTS,
)
from .entity import ScandiaEntity
from .helpers import get_dp


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the flame light entity if the device exposes flame control."""
    coordinator = entry.runtime_data
    if get_dp(entry, CONF_DP_FLAME_BRIGHTNESS) or get_dp(entry, CONF_DP_FLAME_EFFECT):
        async_add_entities([ScandiaFlameLight(coordinator, entry)])


class ScandiaFlameLight(ScandiaEntity, LightEntity):
    """Expose the decorative flame as a dimmable, effect-capable light."""

    _attr_translation_key = "flame"

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Determine supported features from the DP mapping."""
        super().__init__(coordinator)
        self._dp_power = get_dp(entry, CONF_DP_POWER)
        self._dp_brightness = get_dp(entry, CONF_DP_FLAME_BRIGHTNESS)
        self._dp_effect = get_dp(entry, CONF_DP_FLAME_EFFECT)
        self._attr_unique_id = f"{entry.data['device_id']}_flame"

        if self._dp_brightness is not None:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

        if self._dp_effect is not None:
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._attr_effect_list = list(DEFAULT_FLAME_EFFECTS)

    @property
    def is_on(self) -> bool:
        """The flame follows the master power state."""
        return bool(self._dp_value(self._dp_power))

    @property
    def brightness(self) -> int | None:
        """Return brightness scaled to Home Assistant's 0-255 range."""
        if self._dp_brightness is None:
            return None
        value = self._dp_value(self._dp_brightness)
        if value is None:
            return None
        try:
            # Firmware may report either a raw 0-255 int or an enum string.
            return max(0, min(255, int(value)))
        except (TypeError, ValueError):
            return None

    @property
    def effect(self) -> str | None:
        """Return the active flame effect."""
        if self._dp_effect is None:
            return None
        value = self._dp_value(self._dp_effect)
        return str(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the flame on and apply brightness/effect changes."""
        updates: dict[str, Any] = {self._dp_power: True}

        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None and self._dp_brightness:
            updates[self._dp_brightness] = int(max(1, min(255, brightness)))

        if (effect := kwargs.get(ATTR_EFFECT)) is not None and self._dp_effect:
            updates[self._dp_effect] = effect

        await self.coordinator.async_set_multiple(updates)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the flame (and thus the fireplace) off."""
        await self.coordinator.async_set_dp(self._dp_power, False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
