"""Config and options flow for the Scandia Fireplace integration."""

from __future__ import annotations

import logging
from typing import Any

import tinytuya
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
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
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

_LOGGER = logging.getLogger(__name__)


def _test_connection(
    device_id: str, host: str, local_key: str, protocol_version: str
) -> dict[str, Any]:
    """Attempt a local status read. Runs in the executor.

    Returns the reported ``dps`` mapping, or raises to signal failure.
    """
    device = tinytuya.Device(device_id, host, local_key)
    device.set_version(float(protocol_version))
    device.set_socketTimeout(5)
    data = device.status()
    device.close()
    if not isinstance(data, dict) or "dps" not in data:
        raise CannotConnect(str(data))
    return data["dps"]


class CannotConnect(Exception):
    """Error to indicate we cannot reach the fireplace locally."""


class ScandiaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of a Scandia fireplace."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect connection details and verify the device is reachable."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            try:
                await self.hass.async_add_executor_job(
                    _test_connection,
                    device_id,
                    user_input[CONF_HOST].strip(),
                    user_input[CONF_LOCAL_KEY].strip(),
                    user_input[CONF_PROTOCOL_VERSION],
                )
            except Exception as err:  # noqa: BLE001 - map any failure to a form error
                _LOGGER.warning("Could not connect to fireplace: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_MODEL) or "Scandia Fireplace",
                    data={
                        CONF_MODEL: user_input.get(CONF_MODEL, ""),
                        CONF_DEVICE_ID: device_id,
                        CONF_HOST: user_input[CONF_HOST].strip(),
                        CONF_LOCAL_KEY: user_input[CONF_LOCAL_KEY].strip(),
                        CONF_PROTOCOL_VERSION: user_input[CONF_PROTOCOL_VERSION],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_MODEL, default="Scandia Aurora 74"): TextSelector(),
                vol.Required(CONF_HOST): TextSelector(),
                vol.Required(CONF_DEVICE_ID): TextSelector(),
                vol.Required(CONF_LOCAL_KEY): TextSelector(),
                vol.Required(
                    CONF_PROTOCOL_VERSION, default=DEFAULT_PROTOCOL_VERSION
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=PROTOCOL_VERSIONS, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
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
