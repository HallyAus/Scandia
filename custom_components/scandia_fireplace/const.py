"""Constants for the Scandia Fireplace integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "scandia_fireplace"

# --- Connection mode --------------------------------------------------------
# Both modes are bootstrapped from the same QR (user-code) sign-in; the choice
# only affects how commands are delivered at runtime.
CONF_MODE: Final = "mode"
MODE_CLOUD: Final = "cloud"  # commands via the Tuya cloud (works anywhere)
MODE_LOCAL: Final = "local"  # commands direct over the LAN (fast, no cloud)

# --- Tuya cloud sharing (QR / user-code login) -----------------------------
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

# --- Device / local-connection details -------------------------------------
CONF_DEVICE_ID: Final = "device_id"
CONF_MODEL: Final = "model"
CONF_LOCAL_KEY: Final = "local_key"
CONF_HOST: Final = "host"
CONF_PROTOCOL_VERSION: Final = "protocol_version"

PROTOCOL_VERSIONS: Final = ["3.1", "3.2", "3.3", "3.4", "3.5"]
DEFAULT_PROTOCOL_VERSION: Final = "3.3"

CONF_MIN_TEMP: Final = "min_temp"
CONF_MAX_TEMP: Final = "max_temp"
DEFAULT_MIN_TEMP: Final = 15
DEFAULT_MAX_TEMP: Final = 30

# --- Semantic functions -----------------------------------------------------
# Entities are written against these engine-neutral keys; the coordinator maps
# each one to a Tuya "code" (cloud) or a numeric data point (local).
FN_POWER: Final = "power"
FN_HEAT: Final = "heat"
FN_TARGET_TEMP: Final = "target_temp"
FN_CURRENT_TEMP: Final = "current_temp"
FN_FLAME_BRIGHTNESS: Final = "flame_brightness"
FN_FLAME_EFFECT: Final = "flame_effect"
FN_FLAME_SPEED: Final = "flame_speed"
FN_TIMER: Final = "timer"
FN_CHILD_LOCK: Final = "child_lock"
FN_PRESET: Final = "preset"
FN_POWER_W: Final = "power_w"
FN_ENERGY: Final = "energy"

# Ordered list of functions, and the shared option key used to store each
# one's address. The address is a Tuya function code (cloud) or a numeric data
# point (local); which is meant depends on the entry's mode.
FUNCTIONS: Final = [
    FN_POWER,
    FN_HEAT,
    FN_TARGET_TEMP,
    FN_CURRENT_TEMP,
    FN_FLAME_BRIGHTNESS,
    FN_FLAME_EFFECT,
    FN_FLAME_SPEED,
    FN_TIMER,
    FN_CHILD_LOCK,
    FN_PRESET,
    FN_POWER_W,
    FN_ENERGY,
]

OPTION_KEY: Final = {fn: f"addr_{fn}" for fn in FUNCTIONS}

# Default addresses per mode. A blank default disables that function until the
# user maps it. Cloud values are Tuya function codes; local values are DPs.
CLOUD_DEFAULTS: Final[dict[str, str]] = {
    FN_POWER: "switch",
    FN_HEAT: "",
    FN_TARGET_TEMP: "temp_set",
    FN_CURRENT_TEMP: "temp_current",
    FN_FLAME_BRIGHTNESS: "bright_value",
    FN_FLAME_EFFECT: "",
    FN_FLAME_SPEED: "",
    FN_TIMER: "countdown_set",
    FN_CHILD_LOCK: "child_lock",
    FN_PRESET: "mode",
    FN_POWER_W: "",
    FN_ENERGY: "",
}

LOCAL_DEFAULTS: Final[dict[str, str]] = {
    FN_POWER: "1",
    FN_HEAT: "107",
    FN_TARGET_TEMP: "2",
    FN_CURRENT_TEMP: "3",
    FN_FLAME_BRIGHTNESS: "102",
    FN_FLAME_EFFECT: "101",
    FN_FLAME_SPEED: "103",
    FN_TIMER: "106",
    FN_CHILD_LOCK: "108",
    FN_PRESET: "",
    FN_POWER_W: "",
    FN_ENERGY: "",
}

# Functions the options flow exposes as optional (all except power).
OPTIONAL_FUNCTIONS: Final = [fn for fn in FUNCTIONS if fn != FN_POWER]

# --- Enumerations / scaling -------------------------------------------------
DEFAULT_FLAME_EFFECTS: Final = [
    "orange",
    "blue",
    "yellow",
    "red",
    "green",
    "purple",
    "colourful",
]
DEFAULT_FLAME_SPEEDS: Final = ["slow", "medium", "fast"]
DEFAULT_PRESET_MODES: Final = ["eco", "comfort", "boost"]

ENERGY_SCALE: Final = 0.01  # energy is usually reported in 0.01 kWh

# Brightness raw range differs: cloud codes use 0-1000, local DPs use 0-255.
CLOUD_BRIGHTNESS_MAX: Final = 1000
LOCAL_BRIGHTNESS_MAX: Final = 255

PLATFORMS: Final = [
    "climate",
    "light",
    "select",
    "number",
    "switch",
    "sensor",
]
