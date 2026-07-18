"""Constants for the Scandia Fireplace integration.

The control model matches the Scandia Aurora electric fire's remote/app:
power, a heater (Off/Lo/Hi), a countdown timer, and three preset "colour"
controls — flame effect (13), flame log / fuel bed (13) and a top light (4).
This unit has no dimmer and no thermostat, so every non-power control is an
enum picked from a fixed set of presets.
"""

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

# --- Semantic functions -----------------------------------------------------
# Entities are written against these engine-neutral keys; the coordinator maps
# each one to a Tuya "code" (cloud) or a numeric data point (local).
FN_POWER: Final = "power"
FN_HEAT: Final = "heat"
FN_TOP_LIGHT: Final = "top_light"
FN_TIMER: Final = "timer"
FN_FLAME_EFFECT: Final = "flame_effect"
FN_FLAME_LOG: Final = "flame_log"

# Ordered list of functions, and the shared option key used to store each
# one's address. The address is a Tuya function code (cloud) or a numeric data
# point (local); which is meant depends on the entry's mode.
FUNCTIONS: Final = [
    FN_POWER,
    FN_HEAT,
    FN_TOP_LIGHT,
    FN_TIMER,
    FN_FLAME_EFFECT,
    FN_FLAME_LOG,
]

OPTION_KEY: Final = {fn: f"addr_{fn}" for fn in FUNCTIONS}

# Default addresses per mode. A blank default disables that function until the
# user maps it. Cloud values are Tuya function codes; local values are DPs.
#
# Local DPs are the verified Scandia Aurora layout:
#   1  power (bool)   4  heater (Off/Lo/Hi)     5  top light (F0-F3)
#   19 timer (enum)   101 flame effect (L01-L13) 102 flame log (C01-C13)
# The Tuya cloud only publishes "switch" and "countdown_set" for this device,
# so the colour/heater controls are available in local mode only.
CLOUD_DEFAULTS: Final[dict[str, str]] = {
    FN_POWER: "switch",
    FN_HEAT: "",
    FN_TOP_LIGHT: "",
    FN_TIMER: "countdown_set",
    FN_FLAME_EFFECT: "",
    FN_FLAME_LOG: "",
}

LOCAL_DEFAULTS: Final[dict[str, str]] = {
    FN_POWER: "1",
    FN_HEAT: "4",
    FN_TOP_LIGHT: "5",
    FN_TIMER: "19",
    FN_FLAME_EFFECT: "101",
    FN_FLAME_LOG: "102",
}

# Functions the options flow exposes as optional (all except power).
OPTIONAL_FUNCTIONS: Final = [fn for fn in FUNCTIONS if fn != FN_POWER]

# --- Preset value maps (raw device value -> friendly label) -----------------
# Flame effect and flame-log each expose 13 colours (L01-L13 / C01-C13). The
# unit ships no names for them, so they read as "Colour 1".."Colour 13".
FLAME_EFFECT_OPTIONS: Final[dict[str, str]] = {
    f"L{n:02d}": f"Colour {n}" for n in range(1, 14)
}
FLAME_LOG_OPTIONS: Final[dict[str, str]] = {
    f"C{n:02d}": f"Colour {n}" for n in range(1, 14)
}
TOP_LIGHT_OPTIONS: Final[dict[str, str]] = {
    "F0": "Off",
    "F1": "Yellow",
    "F2": "Blue",
    "F3": "Purple",
}
HEATER_OPTIONS: Final[dict[str, str]] = {
    "OFF": "Off",
    "LO": "Low (750W)",
    "HI": "High (1500W)",
}
TIMER_OPTIONS: Final[dict[str, str]] = {
    "cancel": "Off",
    "1h": "1 hour",
    "2h": "2 hours",
    "3h": "3 hours",
    "4h": "4 hours",
    "5h": "5 hours",
    "6h": "6 hours",
}

PLATFORMS: Final = [
    "switch",
    "select",
    "button",
    "sensor",
]
