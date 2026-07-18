"""Shared helpers for resolving the effective function-code mapping."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_CODE_CHILD_LOCK,
    CONF_CODE_CURRENT_TEMP,
    CONF_CODE_ENERGY,
    CONF_CODE_FLAME_BRIGHTNESS,
    CONF_CODE_FLAME_EFFECT,
    CONF_CODE_FLAME_SPEED,
    CONF_CODE_HEAT,
    CONF_CODE_POWER,
    CONF_CODE_POWER_W,
    CONF_CODE_PRESET,
    CONF_CODE_TARGET_TEMP,
    CONF_CODE_TIMER,
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    DEFAULT_CODE_CHILD_LOCK,
    DEFAULT_CODE_CURRENT_TEMP,
    DEFAULT_CODE_ENERGY,
    DEFAULT_CODE_FLAME_BRIGHTNESS,
    DEFAULT_CODE_FLAME_EFFECT,
    DEFAULT_CODE_FLAME_SPEED,
    DEFAULT_CODE_HEAT,
    DEFAULT_CODE_POWER,
    DEFAULT_CODE_POWER_W,
    DEFAULT_CODE_PRESET,
    DEFAULT_CODE_TARGET_TEMP,
    DEFAULT_CODE_TIMER,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
)

_CODE_DEFAULTS: dict[str, str] = {
    CONF_CODE_POWER: DEFAULT_CODE_POWER,
    CONF_CODE_HEAT: DEFAULT_CODE_HEAT,
    CONF_CODE_TARGET_TEMP: DEFAULT_CODE_TARGET_TEMP,
    CONF_CODE_CURRENT_TEMP: DEFAULT_CODE_CURRENT_TEMP,
    CONF_CODE_FLAME_BRIGHTNESS: DEFAULT_CODE_FLAME_BRIGHTNESS,
    CONF_CODE_FLAME_EFFECT: DEFAULT_CODE_FLAME_EFFECT,
    CONF_CODE_FLAME_SPEED: DEFAULT_CODE_FLAME_SPEED,
    CONF_CODE_TIMER: DEFAULT_CODE_TIMER,
    CONF_CODE_CHILD_LOCK: DEFAULT_CODE_CHILD_LOCK,
    CONF_CODE_PRESET: DEFAULT_CODE_PRESET,
    CONF_CODE_POWER_W: DEFAULT_CODE_POWER_W,
    CONF_CODE_ENERGY: DEFAULT_CODE_ENERGY,
}


def get_code(entry: ConfigEntry, key: str) -> str | None:
    """Return the configured Tuya function code for ``key``.

    A cleared option (empty string) disables that feature and returns ``None``.
    Options take precedence over the built-in defaults.
    """
    raw = entry.options.get(key, _CODE_DEFAULTS.get(key))
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def get_temp_range(entry: ConfigEntry) -> tuple[float, float]:
    """Return the (min, max) target-temperature range."""
    return (
        float(entry.options.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)),
        float(entry.options.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)),
    )
