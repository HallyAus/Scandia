"""Config and options flow for the Scandia Fireplace integration.

Setup is cloud-assisted but the running integration is local: the user supplies
their Tuya IoT project credentials once, the flow pulls every device's local key
and protocol version from the Tuya cloud, and the fireplace is then controlled
directly over the LAN.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .cloud import CloudError, TuyaCloud
from .const import (
    CLOUD_REGIONS,
    CONF_CLOUD_API_KEY,
    CONF_CLOUD_API_SECRET,
    CONF_CLOUD_REGION,
    CONF_DEVICE_ID,
    CONF_DP_CHILD_LOCK,
    CONF_DP_CURRENT_TEMP,
    CONF_DP_FLAME_BRIGHTNESS,
    CONF_DP_FLAME_EFFECT,
    CONF_DP_FLAME_SPEED,
    CONF_DP_HEAT,
    CONF_DP_POWER,
    CONF_DP_TARGET_TEMP,
    CONF_DP_TIMER,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    CONF_MODEL,
    CONF_PROTOCOL_VERSION,
    CONF_SCAN_INTERVAL,
    DEFAULT_CLOUD_REGION,
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
    DEFAULT_PROTOCOL_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROTOCOL_VERSIONS,
)
from .coordinator import test_local_connection
from .discovery import scan_lan

_LOGGER = logging.getLogger(__name__)


def _normalise_version(raw: Any) -> str:
    """Coerce a cloud-reported protocol version to a supported string."""
    version = str(raw).strip() if raw is not None else ""
    return version if version in PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION


class ScandiaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Cloud-assisted setup for a Scandia fireplace."""

    VERSION = 1

    def __init__(self) -> None:
        """Hold state between the credential and device-selection steps."""
        self._cloud_creds: dict[str, str] = {}
        self._devices: list[dict[str, Any]] = []
        self._discovered: dict[str, str] = {}
        self._scanned = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect Tuya IoT credentials and list the account's devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            region = user_input[CONF_CLOUD_REGION]
            api_key = user_input[CONF_CLOUD_API_KEY].strip()
            api_secret = user_input[CONF_CLOUD_API_SECRET].strip()
            sample_id = user_input[CONF_DEVICE_ID].strip()

            try:
                cloud = await self.hass.async_add_executor_job(
                    TuyaCloud, region, api_key, api_secret, sample_id
                )
                devices = await self.hass.async_add_executor_job(cloud.list_devices)
            except CloudError as err:
                _LOGGER.warning("Tuya cloud error: %s", err)
                errors["base"] = "cloud_error"
            except Exception as err:  # noqa: BLE001 - map any failure to a form error
                _LOGGER.warning("Unexpected cloud error: %s", err)
                errors["base"] = "cloud_error"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    self._cloud_creds = {
                        CONF_CLOUD_REGION: region,
                        CONF_CLOUD_API_KEY: api_key,
                        CONF_CLOUD_API_SECRET: api_secret,
                    }
                    self._devices = devices
                    return await self.async_step_select_device()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CLOUD_REGION, default=DEFAULT_CLOUD_REGION
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=CLOUD_REGIONS, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Required(CONF_CLOUD_API_KEY): TextSelector(),
                vol.Required(CONF_CLOUD_API_SECRET): TextSelector(),
                vol.Required(CONF_DEVICE_ID): TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick the fireplace, confirm its IP, and verify local control."""
        errors: dict[str, str] = {}

        devices_by_id = {d["id"]: d for d in self._devices if d.get("id")}

        # Best-effort LAN scan (once) so we can auto-fill the fireplace's IP.
        if not self._scanned:
            self._discovered = await self.hass.async_add_executor_job(scan_lan)
            self._scanned = True

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = devices_by_id.get(device_id, {})
            local_key = device.get("key", "")
            # Fall back to the auto-discovered IP if the field was left blank.
            host = user_input.get(CONF_HOST, "").strip() or self._discovered.get(
                device_id, ""
            )
            version = user_input[CONF_PROTOCOL_VERSION]

            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            if not local_key:
                errors["base"] = "no_local_key"
            elif not host:
                errors["base"] = "no_ip"
            else:
                try:
                    await self.hass.async_add_executor_job(
                        test_local_connection, device_id, host, local_key, version
                    )
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Could not connect locally: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=device.get("name") or "Scandia Fireplace",
                        data={
                            CONF_MODEL: device.get("name", ""),
                            CONF_DEVICE_ID: device_id,
                            CONF_HOST: host,
                            CONF_LOCAL_KEY: local_key,
                            CONF_PROTOCOL_VERSION: version,
                            **self._cloud_creds,
                        },
                    )

        options = [
            SelectOptionDict(
                value=d["id"], label=f"{d.get('name', 'Device')} ({d['id']})"
            )
            for d in self._devices
            if d.get("id")
        ]

        # Pre-fill the protocol version and IP from the first/selected device.
        selected = user_input.get(CONF_DEVICE_ID) if user_input else None
        default_device = (
            devices_by_id.get(selected) if selected else self._devices[0]
        ) or self._devices[0]
        default_version = _normalise_version(default_device.get("version"))
        default_host = (
            user_input.get(CONF_HOST) if user_input else None
        ) or self._discovered.get(default_device.get("id", ""), "")

        host_field = (
            vol.Required(CONF_HOST, default=default_host)
            if default_host
            else vol.Optional(CONF_HOST, default="")
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_ID, default=default_device.get("id")
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=options, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                host_field: TextSelector(),
                vol.Required(
                    CONF_PROTOCOL_VERSION, default=default_version
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=PROTOCOL_VERSIONS, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="select_device",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "discovered": str(len(self._discovered)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> ScandiaOptionsFlow:
        """Return the options flow handler."""
        return ScandiaOptionsFlow()


class ScandiaOptionsFlow(OptionsFlow):
    """Let the user remap data points and tune temperature limits."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the DP mapping and temperature options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        def _dp_default(key: str, fallback: str) -> str:
            return str(options.get(key, fallback))

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DP_POWER, default=_dp_default(CONF_DP_POWER, DEFAULT_DP_POWER)
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_HEAT, default=_dp_default(CONF_DP_HEAT, DEFAULT_DP_HEAT)
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_TARGET_TEMP,
                    default=_dp_default(CONF_DP_TARGET_TEMP, DEFAULT_DP_TARGET_TEMP),
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_CURRENT_TEMP,
                    default=_dp_default(CONF_DP_CURRENT_TEMP, DEFAULT_DP_CURRENT_TEMP),
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_FLAME_BRIGHTNESS,
                    default=_dp_default(
                        CONF_DP_FLAME_BRIGHTNESS, DEFAULT_DP_FLAME_BRIGHTNESS
                    ),
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_FLAME_EFFECT,
                    default=_dp_default(CONF_DP_FLAME_EFFECT, DEFAULT_DP_FLAME_EFFECT),
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_FLAME_SPEED,
                    default=_dp_default(CONF_DP_FLAME_SPEED, DEFAULT_DP_FLAME_SPEED),
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_TIMER,
                    default=_dp_default(CONF_DP_TIMER, DEFAULT_DP_TIMER),
                ): TextSelector(),
                vol.Optional(
                    CONF_DP_CHILD_LOCK,
                    default=_dp_default(CONF_DP_CHILD_LOCK, DEFAULT_DP_CHILD_LOCK),
                ): TextSelector(),
                vol.Required(
                    CONF_MIN_TEMP,
                    default=options.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5, max=40, step=1, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_MAX_TEMP,
                    default=options.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5, max=40, step=1, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10, max=600, step=5, mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
