"""Config and options flow for the Scandia Fireplace integration.

Login mirrors Home Assistant's official Tuya integration: the user enters a
"user code" from the Smart Life app and scans a QR code — no developer/IoT
project required. Control then happens through the Tuya cloud.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from tuya_sharing import LoginControl

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
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
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    CONF_MODEL,
    CONF_TERMINAL_ID,
    CONF_TOKEN_INFO,
    CONF_USER_CODE,
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
    DOMAIN,
    TUYA_CLIENT_ID,
    TUYA_RESPONSE_QR_CODE,
    TUYA_RESPONSE_RESULT,
    TUYA_RESPONSE_SUCCESS,
    TUYA_SCHEMA,
)
from .coordinator import TokenListener, build_manager

_LOGGER = logging.getLogger(__name__)


class ScandiaConfigFlow(ConfigFlow, domain=DOMAIN):
    """QR-code (user-code) login for a Scandia fireplace."""

    VERSION = 1

    def __init__(self) -> None:
        """Hold state across the login steps."""
        self._login_control = LoginControl()
        self._user_code: str = ""
        self._qr_code: str = ""
        self._token_data: dict[str, Any] = {}
        self._devices: list[Any] = []
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the Smart Life user code and request a login QR code."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._user_code = user_input[CONF_USER_CODE].strip()
            response = await self.hass.async_add_executor_job(
                self._login_control.qr_code,
                TUYA_CLIENT_ID,
                TUYA_SCHEMA,
                self._user_code,
            )
            if response.get(TUYA_RESPONSE_SUCCESS):
                self._qr_code = response[TUYA_RESPONSE_RESULT][TUYA_RESPONSE_QR_CODE]
                return await self.async_step_scan()
            errors["base"] = "login_error"

        default_user_code = self._user_code
        if self._reauth_entry is not None:
            default_user_code = self._reauth_entry.data.get(CONF_USER_CODE, "")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USER_CODE, default=default_user_code
                    ): TextSelector()
                }
            ),
            errors=errors,
        )

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the QR code and wait for the user to scan and confirm."""
        if user_input is None:
            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema(
                    {
                        vol.Optional("QR"): selector.QrCodeSelector(
                            config=selector.QrCodeSelectorConfig(
                                data=f"tuyaSmart--qrLogin?token={self._qr_code}",
                                scale=5,
                                error_correction_level=(
                                    selector.QrErrorCorrectionLevel.QUARTILE
                                ),
                            )
                        )
                    }
                ),
            )

        ret, info = await self.hass.async_add_executor_job(
            self._login_control.login_result,
            self._qr_code,
            TUYA_CLIENT_ID,
            self._user_code,
        )
        if not ret:
            return self.async_show_form(
                step_id="scan",
                errors={"base": "login_error"},
                data_schema=vol.Schema(
                    {
                        vol.Optional("QR"): selector.QrCodeSelector(
                            config=selector.QrCodeSelectorConfig(
                                data=f"tuyaSmart--qrLogin?token={self._qr_code}",
                                scale=5,
                                error_correction_level=(
                                    selector.QrErrorCorrectionLevel.QUARTILE
                                ),
                            )
                        )
                    }
                ),
            )

        self._token_data = {
            CONF_USER_CODE: self._user_code,
            CONF_TOKEN_INFO: {
                "t": info["t"],
                "uid": info["uid"],
                "expire_time": info["expire_time"],
                "access_token": info["access_token"],
                "refresh_token": info["refresh_token"],
            },
            CONF_TERMINAL_ID: info[CONF_TERMINAL_ID],
            CONF_ENDPOINT: info[CONF_ENDPOINT],
        }

        if self._reauth_entry is not None:
            return self.async_update_reload_and_abort(
                self._reauth_entry,
                data={**self._reauth_entry.data, **self._token_data},
            )

        return await self.async_step_select_device()

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """List the account's devices and let the user pick the fireplace."""
        errors: dict[str, str] = {}

        if not self._devices:
            entry_stub = _StubEntry(self._token_data)
            manager = build_manager(
                entry_stub, TokenListener(self.hass, None)  # type: ignore[arg-type]
            )
            try:
                await self.hass.async_add_executor_job(manager.update_device_cache)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Could not list Tuya devices: %s", err)
                return self.async_abort(reason="no_devices")
            self._devices = list(manager.device_map.values())

        if not self._devices:
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = next((d for d in self._devices if d.id == device_id), None)
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=getattr(device, "name", None) or "Scandia Fireplace",
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_MODEL: getattr(device, "product_name", ""),
                    **self._token_data,
                },
            )

        options = [
            SelectOptionDict(
                value=d.id,
                label=f"{getattr(d, 'name', 'Device')} ({getattr(d, 'category', '')})",
            )
            for d in self._devices
        ]
        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=options, mode=SelectSelectorMode.DROPDOWN
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Re-authenticate when the stored token can no longer be refreshed."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> ScandiaOptionsFlow:
        """Return the options flow handler."""
        return ScandiaOptionsFlow()


class _StubEntry:
    """Minimal stand-in exposing ``data`` for Manager construction pre-entry."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data


class ScandiaOptionsFlow(OptionsFlow):
    """Let the user remap function codes and tune temperature limits."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the code mapping and temperature options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_MIN_TEMP] >= user_input[CONF_MAX_TEMP]:
                errors["base"] = "temp_range"
            else:
                return self.async_create_entry(title="", data=user_input)

        options = {**self.config_entry.options, **(user_input or {})}

        def _code(key: str, fallback: str) -> str:
            return str(options.get(key, fallback))

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CODE_POWER, default=_code(CONF_CODE_POWER, DEFAULT_CODE_POWER)
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_HEAT, default=_code(CONF_CODE_HEAT, DEFAULT_CODE_HEAT)
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_TARGET_TEMP,
                    default=_code(CONF_CODE_TARGET_TEMP, DEFAULT_CODE_TARGET_TEMP),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_CURRENT_TEMP,
                    default=_code(CONF_CODE_CURRENT_TEMP, DEFAULT_CODE_CURRENT_TEMP),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_FLAME_BRIGHTNESS,
                    default=_code(
                        CONF_CODE_FLAME_BRIGHTNESS, DEFAULT_CODE_FLAME_BRIGHTNESS
                    ),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_FLAME_EFFECT,
                    default=_code(CONF_CODE_FLAME_EFFECT, DEFAULT_CODE_FLAME_EFFECT),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_FLAME_SPEED,
                    default=_code(CONF_CODE_FLAME_SPEED, DEFAULT_CODE_FLAME_SPEED),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_TIMER,
                    default=_code(CONF_CODE_TIMER, DEFAULT_CODE_TIMER),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_CHILD_LOCK,
                    default=_code(CONF_CODE_CHILD_LOCK, DEFAULT_CODE_CHILD_LOCK),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_PRESET,
                    default=_code(CONF_CODE_PRESET, DEFAULT_CODE_PRESET),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_POWER_W,
                    default=_code(CONF_CODE_POWER_W, DEFAULT_CODE_POWER_W),
                ): TextSelector(),
                vol.Optional(
                    CONF_CODE_ENERGY,
                    default=_code(CONF_CODE_ENERGY, DEFAULT_CODE_ENERGY),
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
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
