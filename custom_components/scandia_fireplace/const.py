"""Constants for the Scandia Fireplace integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "scandia_fireplace"

# Config entry keys
CONF_DEVICE_ID: Final = "device_id"
CONF_LOCAL_KEY: Final = "local_key"
CONF_HOST: Final = "host"
CONF_PROTOCOL_VERSION: Final = "protocol_version"
CONF_MODEL: Final = "model"
CONF_MAC: Final = "mac"

# Tuya cloud credentials (used to auto-fetch the local key, and to refresh it
# automatically if it changes after re-pairing).
CONF_CLOUD_REGION: Final = "cloud_region"
CONF_CLOUD_API_KEY: Final = "cloud_api_key"
CONF_CLOUD_API_SECRET: Final = "cloud_api_secret"

# Tuya cloud data-centre regions supported by tinytuya.
CLOUD_REGIONS: Final = ["us", "us-e", "eu", "eu-w", "cn", "in", "sg"]
DEFAULT_CLOUD_REGION: Final = "us"

# Options / data-point mapping keys
CONF_DP_POWER: Final = "dp_power"
CONF_DP_HEAT: Final = "dp_heat"
CONF_DP_TARGET_TEMP: Final = "dp_target_temp"
CONF_DP_CURRENT_TEMP: Final = "dp_current_temp"
CONF_DP_FLAME_BRIGHTNESS: Final = "dp_flame_brightness"
CONF_DP_FLAME_EFFECT: Final = "dp_flame_effect"
CONF_DP_FLAME_SPEED: Final = "dp_flame_speed"
CONF_DP_TIMER: Final = "dp_timer"
CONF_DP_CHILD_LOCK: Final = "dp_child_lock"
CONF_DP_PRESET: Final = "dp_preset"
CONF_DP_POWER_W: Final = "dp_power_w"
CONF_DP_ENERGY: Final = "dp_energy"
CONF_MIN_TEMP: Final = "min_temp"
CONF_MAX_TEMP: Final = "max_temp"
CONF_TEMP_UNIT: Final = "temp_unit"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Supported Tuya local protocol versions.
PROTOCOL_VERSIONS: Final = ["3.1", "3.2", "3.3", "3.4", "3.5"]
DEFAULT_PROTOCOL_VERSION: Final = "3.3"

# Default polling interval, seconds.
DEFAULT_SCAN_INTERVAL: Final = 30

# Default data-point (DP) mapping.
#
# The Scandia Aurora electric fires are re-badged Tuya heaters that share their
# firmware with several other Australian brands (Kogan, Touchstone, Modern
# Flames). These are the DP identifiers those units expose. Because firmware
# revisions occasionally shuffle the higher DP numbers, every mapping below can
# be overridden from the integration's options if your unit differs. Use the
# "Raw data points" diagnostic to discover your device's actual DPs.
DEFAULT_DP_POWER: Final = "1"  # bool: master power / flame on-off
DEFAULT_DP_HEAT: Final = "107"  # bool: heating element enable
DEFAULT_DP_TARGET_TEMP: Final = "2"  # int: target temperature
DEFAULT_DP_CURRENT_TEMP: Final = "3"  # int: measured room temperature
DEFAULT_DP_FLAME_BRIGHTNESS: Final = "102"  # enum/int: flame brightness
DEFAULT_DP_FLAME_EFFECT: Final = "101"  # enum: flame colour / effect
DEFAULT_DP_FLAME_SPEED: Final = "103"  # enum: flame animation speed
DEFAULT_DP_TIMER: Final = "106"  # int: countdown timer (hours)
DEFAULT_DP_CHILD_LOCK: Final = "108"  # bool: child lock

# These vary widely between models and are disabled by default. Enable them by
# setting the DP number in the integration options once you've identified them
# from the "Raw data points" diagnostic.
DEFAULT_DP_PRESET: Final = ""  # enum: heat preset (eco/comfort/boost)
DEFAULT_DP_POWER_W: Final = ""  # int: instantaneous power, watts
DEFAULT_DP_ENERGY: Final = ""  # int: cumulative energy, often in 0.01 kWh

DEFAULT_MIN_TEMP: Final = 15
DEFAULT_MAX_TEMP: Final = 30

TEMP_UNIT_C: Final = "C"
TEMP_UNIT_F: Final = "F"

# Flame effect / colour options. These are the string values the firmware
# accepts on the flame-effect DP. The options flow lets you edit this list to
# match your firmware if it reports different names.
DEFAULT_FLAME_EFFECTS: Final = [
    "orange",
    "blue",
    "yellow",
    "red",
    "green",
    "purple",
    "orange_blue",
    "colorful",
]

# Flame brightness levels reported by these units (enum strings). Some firmware
# uses raw integers 0-255 instead; the light entity handles both.
DEFAULT_FLAME_BRIGHTNESS_LEVELS: Final = ["25", "51", "102", "153", "204", "255"]

# Flame animation speed options.
DEFAULT_FLAME_SPEEDS: Final = ["slow", "medium", "fast"]

# Heat preset options (enum strings the preset DP accepts). Editable if your
# firmware uses different names.
DEFAULT_PRESET_MODES: Final = ["eco", "comfort", "boost"]

# Energy DP is commonly reported in hundredths of a kWh.
ENERGY_DP_SCALE: Final = 0.01

PLATFORMS: Final = [
    "climate",
    "light",
    "select",
    "number",
    "switch",
    "sensor",
]
