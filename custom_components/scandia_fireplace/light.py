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
    DEFAULT_FLAME_EFFECTS,
    FN_FLAME_BRIGHTNESS,
    FN_FLAME_EFFECT,
    FN_POWER,
)
from .entity import ScandiaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the flame light entity if the device exposes flame control."""
    coordinator = entry.runtime_data
    if coordinator.configured(FN_FLAME_BRIGHTNESS) or coordinator.configured(
        FN_FLAME_EFFECT
    ):
        async_add_entities([ScandiaFlameLight(coordinator, entry)])


class ScandiaFlameLight(ScandiaEntity, LightEntity):
    """Expose the decorative flame as a dimmable, effect-capable light."""

    _attr_translation_key = "flame"

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Determine supported features from the function mapping."""
        super().__init__(coordinator)
        self._brightness_max = coordinator.brightness_max
        self._has_brightness = coordinator.configured(FN_FLAME_BRIGHTNESS)
        self._has_effect = coordinator.configured(FN_FLAME_EFFECT)
        self._attr_unique_id = f"{coordinator.device_id}_flame"

        if self._has_brightness:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

        if self._has_effect:
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._attr_effect_list = list(DEFAULT_FLAME_EFFECTS)

    @property
    def is_on(self) -> bool:
        """The flame follows the master power state."""
        return bool(self.coordinator.read(FN_POWER))

    @property
    def brightness(self) -> int | None:
        """Return brightness scaled from the device range to 0-255."""
        if not self._has_brightness:
            return None
        value = self.coordinator.read(FN_FLAME_BRIGHTNESS)
        if value is None:
            return None
        try:
            return round(int(value) * 255 / self._brightness_max)
        except (TypeError, ValueError):
            return None

    @property
    def effect(self) -> str | None:
        """Return the active flame effect."""
        if not self._has_effect:
            return None
        value = self.coordinator.read(FN_FLAME_EFFECT)
        return str(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the flame on and apply brightness/effect changes."""
        values: dict[str, Any] = {FN_POWER: True}

        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None and self._has_brightness:
            values[FN_FLAME_BRIGHTNESS] = max(
                1, round(brightness * self._brightness_max / 255)
            )
        if (effect := kwargs.get(ATTR_EFFECT)) is not None and self._has_effect:
            values[FN_FLAME_EFFECT] = effect

        await self.coordinator.async_write(values)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the flame (and thus the fireplace) off."""
        await self.coordinator.async_write({FN_POWER: False})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
