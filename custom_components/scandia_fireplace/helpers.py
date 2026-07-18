"""Shared helpers for resolving the effective DP mapping."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_DP_CHILD_LOCK,
    CONF_DP_CURRENT_TEMP,
    CONF_DP_FLAME_BRIGHTNESS,
    CONF_DP_FLAME_EFFECT,
    CONF_DP_FLAME_SPEED,
    CONF_DP_HEAT,
    CONF_DP_POWER,
    CONF_DP_TARGET_TEMP,
    CONF_DP_TIMER,
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    DEFAULT_DP_CHILD_LOCK,
    DEFAULT_DP_CURRENT_TEMP,
    DEFAULT_DP_FLAME_BRIGHTNESS,
    DEFAULT_DP_FLAME_EFFECT,
    DEFAULT_DP_FLAME_SPEED,
    DEFAULT_DP_HEAT,
    DEFAULT_DP_POWER,
    DEFAULT_DP_TARGET_TEMP,
    DEFAULT_DP_TIMER,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
)

_DP_DEFAULTS: dict[str, str] = {
    CONF_DP_POWER: DEFAULT_DP_POWER,
    CONF_DP_HEAT: DEFAULT_DP_HEAT,
    CONF_DP_TARGET_TEMP: DEFAULT_DP_TARGET_TEMP,
    CONF_DP_CURRENT_TEMP: DEFAULT_DP_CURRENT_TEMP,
    CONF_DP_FLAME_BRIGHTNESS: DEFAULT_DP_FLAME_BRIGHTNESS,
    CONF_DP_FLAME_EFFECT: DEFAULT_DP_FLAME_EFFECT,
    CONF_DP_FLAME_SPEED: DEFAULT_DP_FLAME_SPEED,
    CONF_DP_TIMER: DEFAULT_DP_TIMER,
    CONF_DP_CHILD_LOCK: DEFAULT_DP_CHILD_LOCK,
}


def get_dp(entry: ConfigEntry, key: str) -> str | None:
    """Return the configured DP id for ``key``.

    An option that has been cleared (empty string) disables that feature and
    returns ``None``. Options take precedence over the built-in defaults.
    """
    raw = entry.options.get(key, _DP_DEFAULTS.get(key))
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
