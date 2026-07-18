"""Shared helpers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import CONF_MAX_TEMP, CONF_MIN_TEMP, DEFAULT_MAX_TEMP, DEFAULT_MIN_TEMP


def get_temp_range(entry: ConfigEntry) -> tuple[float, float]:
    """Return the (min, max) target-temperature range."""
    return (
        float(entry.options.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)),
        float(entry.options.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)),
    )
