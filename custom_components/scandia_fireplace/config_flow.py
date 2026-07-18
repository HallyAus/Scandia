"""Config and options flow for the Scandia Fireplace integration.

Login always uses the Smart Life "user code" + QR scan (no developer project).
The same sign-in yields the device's cloud token *and* its local key + IP, so
the user can then choose cloud control or fast local (LAN) control.
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
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CLOUD_DEFAULTS,
    CONF_DEVICE_ID,
    CONF_ENDPOINT,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_MODE,
    CONF_MODEL,
    CONF_PROTOCOL_VERSION,
    CONF_TERMINAL_ID,
    CONF_TOKEN_INFO,
    CONF_USER_CODE,
    DEFAULT_PROTOCOL_VERSION,
    DOMAIN,
    FN_POWER,
    FUNCTIONS,
    LOCAL_DEFAULTS,
    MODE_CLOUD,
    MODE_LOCAL,
    OPTION_KEY,
    PROTOCOL_VERSIONS,
    TUYA_CLIENT_ID,
    TUYA_RESPONSE_QR_CODE,
    TUYA_RESPONSE_RESULT,
    TUYA_RESPONSE_SUCCESS,
    TUYA_SCHEMA,
)
from .coordinator import TokenListener, build_manager, test_local_connection
from .discovery import scan_lan

_LOGGER = logging.getLogger(__name__)


def _normalise_version(raw: Any) -> str:
    """Coerce a protocol version to a supported string, defaulting to 3.3."""
    version = str(raw).strip() if raw is not None else ""
    return version if version in PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION


def _qr_schema(token: str) -> vol.Schema:
    """Schema that renders the login QR code."""
    return vol.Schema(
        {
            vol.Optional("QR"): selector.QrCodeSelector(
                config=selector.QrCodeSelectorConfig(
                    data=f"tuyaSmart--qrLogin?token={token}",
                    scale=5,
                    error_correction_level=selector.QrErrorCorrectionLevel.QUARTILE,
                )
            )
        }
    )


class _StubEntry:
    """Minimal stand-in exposing ``data`` for Manager construction pre-entry."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data


class ScandiaConfigFlow(ConfigFlow, domain=DOMAIN):
    """QR-code (user-code) login, then a choice of cloud or local control."""

    VERSION = 1

    def __init__(self) -> None:
        """Hold state across the login and mode steps."""
        self._login_control = LoginControl()
        self._user_code = ""
        self._qr_code = ""
        self._token_data: dict[str, Any] = {}
        self._devices: list[Any] = []
        self._reauth_entry: ConfigEntry | None = None
        self._device: dict[str, str] = {}
        self._discovered: dict[str, dict[str, str]] = {}
        self._scanned = False

    # -- login --------------------------------------------------------------
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
                step_id="scan", data_schema=_qr_schema(self._qr_code)
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
                data_schema=_qr_schema(self._qr_code),
                errors={"base": "login_error"},
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

    # -- device + mode ------------------------------------------------------
    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """List the account's devices and let the user pick the fireplace."""
        if not self._devices:
            manager = build_manager(
                _StubEntry(self._token_data),  # type: ignore[arg-type]
                TokenListener(self.hass, None),
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
            device = next(
                (d for d in self._devices if d.id == user_input[CONF_DEVICE_ID]), None
            )
            self._device = {
                "id": device.id,
                "name": getattr(device, "name", "") or "Scandia Fireplace",
                "model": getattr(device, "product_name", "") or "",
                "local_key": getattr(device, "local_key", "") or "",
                "ip": getattr(device, "ip", "") or "",
            }
            await self.async_set_unique_id(device.id)
            self._abort_if_unique_id_configured()
            return await self.async_step_mode()

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
        )

    async def async_step_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose cloud or local control."""
        return self.async_show_menu(
            step_id="mode", menu_options=["cloud", "local"]
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish setup in cloud mode."""
        return self._create_entry(MODE_CLOUD, {})

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish setup in local mode, verifying the LAN connection."""
        if not self._device.get("local_key"):
            return self.async_abort(reason="no_local_key")

        errors: dict[str, str] = {}
        if not self._scanned:
            self._discovered = await self.hass.async_add_executor_job(scan_lan)
            self._scanned = True
        discovered = self._discovered.get(self._device["id"], {})

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            version = user_input[CONF_PROTOCOL_VERSION]
            try:
                await self.hass.async_add_executor_job(
                    test_local_connection,
                    self._device["id"],
                    host,
                    self._device["local_key"],
                    version,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Could not connect locally: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self._create_entry(
                    MODE_LOCAL,
                    {
                        CONF_HOST: host,
                        CONF_LOCAL_KEY: self._device["local_key"],
                        CONF_PROTOCOL_VERSION: version,
                    },
                )

        default_host = (
            (user_input or {}).get(CONF_HOST)
            or self._device.get("ip")
            or discovered.get("ip", "")
        )
        default_version = _normalise_version(
            (user_input or {}).get(CONF_PROTOCOL_VERSION) or discovered.get("version")
        )
        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=default_host): TextSelector(),
                    vol.Required(
                        CONF_PROTOCOL_VERSION, default=default_version
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=PROTOCOL_VERSIONS, mode=SelectSelectorMode.DROPDOWN
                        )
                    ),
                }
            ),
            errors=errors,
        )

    def _create_entry(
        self, mode: str, extra: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create the config entry for the chosen mode."""
        return self.async_create_entry(
            title=self._device["name"],
            data={
                CONF_MODE: mode,
                CONF_DEVICE_ID: self._device["id"],
                CONF_MODEL: self._device["model"],
                **self._token_data,
                **extra,
            },
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


class ScandiaOptionsFlow(OptionsFlow):
    """Let the user remap each function to a Tuya code (cloud) or DP (local)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the address mapping."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        defaults = (
            CLOUD_DEFAULTS
            if self.config_entry.data.get(CONF_MODE) == MODE_CLOUD
            else LOCAL_DEFAULTS
        )

        schema_dict: dict[Any, Any] = {}
        for fn in FUNCTIONS:
            option_key = OPTION_KEY[fn]
            current = str(options.get(option_key, defaults[fn]))
            marker = vol.Required if fn == FN_POWER else vol.Optional
            schema_dict[marker(option_key, default=current)] = TextSelector()

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema_dict)
        )
