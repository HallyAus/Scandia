"""Constants for the Scandia Fireplace integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "scandia_fireplace"

# --- Tuya cloud sharing (QR / user-code login) -----------------------------
# These mirror the login used by Home Assistant's official Tuya integration:
# the user enters a "user code" from the Smart Life app and scans a QR code,
# so no developer/IoT project is required.
CONF_USER_CODE: Final = "user_code"
CONF_TOKEN_INFO: Final = "token_info"
CONF_TERMINAL_ID: Final = "terminal_id"
CONF_ENDPOINT: Final = "endpoint"

TUYA_CLIENT_ID: Final = "HA_3y9q4ak7g4ephrvke"
TUYA_SCHEMA: Final = "haauthorize"

TUYA_RESPONSE_CODE: Final = "code"
TUYA_RESPONSE_MSG: Final = "msg"
TUYA_RESPONSE_SUCCESS: Final = "success"
TUYA_RESPONSE_RESULT: Final = "result"
TUYA_RESPONSE_QR_CODE: Final = "qrcode"

# The device this entry controls (chosen from the account during setup).
CONF_DEVICE_ID: Final = "device_id"
CONF_MODEL: Final = "model"

# --- Function-code mapping --------------------------------------------------
# Cloud devices expose their functions as named "codes" (e.g. "switch",
# "temp_set") rather than the numbered data points used for local control.
# Codes vary between models, so every mapping is overridable from the options,
# and the diagnostics download lists the codes your device actually reports.
CONF_CODE_POWER: Final = "code_power"
CONF_CODE_HEAT: Final = "code_heat"
CONF_CODE_TARGET_TEMP: Final = "code_target_temp"
CONF_CODE_CURRENT_TEMP: Final = "code_current_temp"
CONF_CODE_FLAME_BRIGHTNESS: Final = "code_flame_brightness"
CONF_CODE_FLAME_EFFECT: Final = "code_flame_effect"
CONF_CODE_FLAME_SPEED: Final = "code_flame_speed"
CONF_CODE_TIMER: Final = "code_timer"
CONF_CODE_CHILD_LOCK: Final = "code_child_lock"
CONF_CODE_PRESET: Final = "code_preset"
CONF_CODE_POWER_W: Final = "code_power_w"
CONF_CODE_ENERGY: Final = "code_energy"

CONF_MIN_TEMP: Final = "min_temp"
CONF_MAX_TEMP: Final = "max_temp"

# Sensible defaults for a standard Tuya electric-fireplace heater. The
# flame-specific codes are left blank (disabled) because they vary widely; set
# them from the options once identified via the "Raw data points" diagnostic.
DEFAULT_CODE_POWER: Final = "switch"
DEFAULT_CODE_HEAT: Final = ""
DEFAULT_CODE_TARGET_TEMP: Final = "temp_set"
DEFAULT_CODE_CURRENT_TEMP: Final = "temp_current"
DEFAULT_CODE_FLAME_BRIGHTNESS: Final = "bright_value"
DEFAULT_CODE_FLAME_EFFECT: Final = ""
DEFAULT_CODE_FLAME_SPEED: Final = ""
DEFAULT_CODE_TIMER: Final = "countdown_set"
DEFAULT_CODE_CHILD_LOCK: Final = "child_lock"
DEFAULT_CODE_PRESET: Final = "mode"
DEFAULT_CODE_POWER_W: Final = ""
DEFAULT_CODE_ENERGY: Final = ""

DEFAULT_MIN_TEMP: Final = 15
DEFAULT_MAX_TEMP: Final = 30

# Flame effect / colour options (enum values the effect code accepts). Editable
# in the options to match your firmware.
DEFAULT_FLAME_EFFECTS: Final = [
    "orange",
    "blue",
    "yellow",
    "red",
    "green",
    "purple",
    "colourful",
]

# Flame animation speed options.
DEFAULT_FLAME_SPEEDS: Final = ["slow", "medium", "fast"]

# Heat preset options (enum values the preset code accepts).
DEFAULT_PRESET_MODES: Final = ["eco", "comfort", "boost"]

# Energy is commonly reported in hundredths of a kWh.
ENERGY_CODE_SCALE: Final = 0.01

# Cloud brightness codes usually range 0-1000; Home Assistant uses 0-255.
TUYA_BRIGHTNESS_MAX: Final = 1000

PLATFORMS: Final = [
    "climate",
    "light",
    "select",
    "number",
    "switch",
    "sensor",
]
