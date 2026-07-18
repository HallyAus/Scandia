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
    CONF_CODE_FLAME_BRIGHTNESS,
    CONF_CODE_FLAME_EFFECT,
    CONF_CODE_POWER,
    DEFAULT_FLAME_EFFECTS,
    TUYA_BRIGHTNESS_MAX,
)
from .entity import ScandiaEntity
from .helpers import get_code


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScandiaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the flame light entity if the device exposes flame control."""
    if get_code(entry, CONF_CODE_FLAME_BRIGHTNESS) or get_code(
        entry, CONF_CODE_FLAME_EFFECT
    ):
        async_add_entities([ScandiaFlameLight(entry.runtime_data, entry)])


class ScandiaFlameLight(ScandiaEntity, LightEntity):
    """Expose the decorative flame as a dimmable, effect-capable light."""

    _attr_translation_key = "flame"

    def __init__(self, coordinator, entry: ScandiaConfigEntry) -> None:
        """Determine supported features from the code mapping."""
        super().__init__(coordinator)
        self._code_power = get_code(entry, CONF_CODE_POWER)
        self._code_brightness = get_code(entry, CONF_CODE_FLAME_BRIGHTNESS)
        self._code_effect = get_code(entry, CONF_CODE_FLAME_EFFECT)
        self._attr_unique_id = f"{coordinator.device_id}_flame"

        if self._code_brightness is not None:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

        if self._code_effect is not None:
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._attr_effect_list = list(DEFAULT_FLAME_EFFECTS)

    @property
    def is_on(self) -> bool:
        """The flame follows the master power state."""
        return bool(self._code_value(self._code_power))

    @property
    def brightness(self) -> int | None:
        """Return brightness scaled from the device range to 0-255."""
        if self._code_brightness is None:
            return None
        value = self._code_value(self._code_brightness)
        if value is None:
            return None
        try:
            return round(int(value) * 255 / TUYA_BRIGHTNESS_MAX)
        except (TypeError, ValueError):
            return None

    @property
    def effect(self) -> str | None:
        """Return the active flame effect."""
        if self._code_effect is None:
            return None
        value = self._code_value(self._code_effect)
        return str(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the flame on and apply brightness/effect changes."""
        commands: list[dict[str, Any]] = [{"code": self._code_power, "value": True}]

        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None and self._code_brightness:
            scaled = max(1, round(brightness * TUYA_BRIGHTNESS_MAX / 255))
            commands.append({"code": self._code_brightness, "value": scaled})

        if (effect := kwargs.get(ATTR_EFFECT)) is not None and self._code_effect:
            commands.append({"code": self._code_effect, "value": effect})

        await self.coordinator.async_send(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the flame (and thus the fireplace) off."""
        await self.coordinator.async_send([{"code": self._code_power, "value": False}])

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state on new data."""
        self.async_write_ha_state()
