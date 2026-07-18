"""Constants for the Scandia Fireplace integration.

The control model matches the Scandia Aurora electric fire's remote/app:
power, a heater (Off/Lo/Hi), a countdown timer, and preset "colour" controls —
flame effect, flame log / fuel bed and (Aurora only) a top light.

The same Tuya OEM board is rebadged widely, but different variants use
different data points *and* different preset value sets. Those variations are
captured as selectable device profiles (see ``DEVICE_PROFILES``).
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
CONF_PROFILE: Final = "profile"

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

# Functions the options flow exposes as optional (all except power).
OPTIONAL_FUNCTIONS: Final = [fn for fn in FUNCTIONS if fn != FN_POWER]

# --- Preset value maps (raw device value -> friendly label) -----------------
# Scandia Aurora: flame effect and flame log each expose 13 numbered colours.
AURORA_FLAME_OPTIONS: Final[dict[str, str]] = {
    f"L{n:02d}": f"Colour {n}" for n in range(1, 14)
}
AURORA_LOG_OPTIONS: Final[dict[str, str]] = {
    f"C{n:02d}": f"Colour {n}" for n in range(1, 14)
}
AURORA_TOP_LIGHT_OPTIONS: Final[dict[str, str]] = {
    "F0": "Off",
    "F1": "Yellow",
    "F2": "Blue",
    "F3": "Purple",
}
AURORA_HEATER_OPTIONS: Final[dict[str, str]] = {
    "OFF": "Off",
    "LO": "Low (750W)",
    "HI": "High (1500W)",
}

# Auchsiag-style clones: named flame colours + named ember colours, lowercase
# heat values. Values verified from make-all/tuya-local (auchsiag_fireplace).
AUCHSIAG_FLAME_OPTIONS: Final[dict[str, str]] = {
    "auto": "Auto",
    "light_red": "Red",
    "light_yellow": "Yellow",
    "light_blue": "Blue",
    "light_orange": "Orange",
    "light_red_yellow": "Red + Yellow",
    "light_red_blue": "Red + Blue",
    "light_red_white": "Red + White",
    "light_yellow_blue": "Yellow + Blue",
    "light_yellow_white": "Yellow + White",
    "light_blue_white": "Blue + White",
    "light_red_yellow_blue": "Red + Yellow + Blue",
    "light_multicolor": "Multicolor",
}
AUCHSIAG_EMBER_OPTIONS: Final[dict[str, str]] = {
    "light_1": "Red",
    "light_2": "Steel Blue",
    "light_3": "Green",
    "light_4": "Pink",
    "light_5": "Yellow",
    "light_6": "Cyan",
    "light_7": "Purple",
    "light_8": "White",
    "light_9": "Goldenrod",
    "light_10": "Sky Blue",
    "light_11": "Sea Green",
    "light_12": "Cornflower Blue",
    "light_13": "Auto",
}
AUCHSIAG_HEATER_OPTIONS: Final[dict[str, str]] = {
    "off": "Off",
    "low": "Low",
    "high": "High",
}

# Countdown timer values are the same string enum across the known variants.
TIMER_OPTIONS: Final[dict[str, str]] = {
    "cancel": "Off",
    "1h": "1 hour",
    "2h": "2 hours",
    "3h": "3 hours",
    "4h": "4 hours",
    "5h": "5 hours",
    "6h": "6 hours",
}

# --- Device profiles --------------------------------------------------------
# Each profile pins the local data points AND the preset value maps for one
# rebadge family. Cloud mode ignores profiles (it only exposes switch + timer).
PROFILE_AURORA: Final = "aurora"
PROFILE_AUCHSIAG: Final = "auchsiag"
DEFAULT_PROFILE: Final = PROFILE_AURORA

DEVICE_PROFILES: Final[dict[str, dict]] = {
    PROFILE_AURORA: {
        "label": "Scandia Aurora (13 flame / 13 log / 3 top-light)",
        "addresses": {
            FN_POWER: "1",
            FN_HEAT: "4",
            FN_TOP_LIGHT: "5",
            FN_TIMER: "19",
            FN_FLAME_EFFECT: "101",
            FN_FLAME_LOG: "102",
        },
        "labels": {
            FN_HEAT: AURORA_HEATER_OPTIONS,
            FN_TOP_LIGHT: AURORA_TOP_LIGHT_OPTIONS,
            FN_TIMER: TIMER_OPTIONS,
            FN_FLAME_EFFECT: AURORA_FLAME_OPTIONS,
            FN_FLAME_LOG: AURORA_LOG_OPTIONS,
        },
    },
    PROFILE_AUCHSIAG: {
        "label": "Auchsiag / named-colour clones (no top light)",
        "addresses": {
            FN_POWER: "1",
            FN_HEAT: "5",
            FN_TOP_LIGHT: "",
            FN_TIMER: "13",
            FN_FLAME_EFFECT: "17",
            FN_FLAME_LOG: "101",
        },
        "labels": {
            FN_HEAT: AUCHSIAG_HEATER_OPTIONS,
            FN_TIMER: TIMER_OPTIONS,
            FN_FLAME_EFFECT: AUCHSIAG_FLAME_OPTIONS,
            FN_FLAME_LOG: AUCHSIAG_EMBER_OPTIONS,
        },
    },
}

# --- Cloud defaults ---------------------------------------------------------
# The Tuya cloud only publishes "switch" and "countdown_set" for this OEM, so
# the colour/heater controls are available in local mode only.
CLOUD_DEFAULTS: Final[dict[str, str]] = {
    FN_POWER: "switch",
    FN_HEAT: "",
    FN_TOP_LIGHT: "",
    FN_TIMER: "countdown_set",
    FN_FLAME_EFFECT: "",
    FN_FLAME_LOG: "",
}
CLOUD_LABELS: Final[dict[str, dict[str, str]]] = {FN_TIMER: TIMER_OPTIONS}


def profile_addresses(profile: str) -> dict[str, str]:
    """Return the local address map for a profile (falls back to default)."""
    return DEVICE_PROFILES.get(profile, DEVICE_PROFILES[DEFAULT_PROFILE])["addresses"]


def profile_labels(profile: str) -> dict[str, dict[str, str]]:
    """Return the preset value maps for a profile (falls back to default)."""
    return DEVICE_PROFILES.get(profile, DEVICE_PROFILES[DEFAULT_PROFILE])["labels"]


PLATFORMS: Final = [
    "switch",
    "select",
    "button",
    "sensor",
]
