"""Config + options flow for Flowwave (UI setup, no YAML)."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CONSUMPTION,
    CONF_GAS,
    CONF_PRODUCTION,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR,
    CONF_TOKEN,
    CONF_VOLTAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INGEST_URL,
)

_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor")
)
_INTERVAL = selector.NumberSelector(
    selector.NumberSelectorConfig(min=5, max=300, step=5, unit_of_measurement="s", mode="box")
)


def _sensor_schema(defaults: dict[str, Any] | None = None) -> dict:
    """The entity + interval part, reused by config and options."""
    d = defaults or {}

    def default(key: str):
        return d.get(key, vol.UNDEFINED)

    return {
        vol.Required(CONF_CONSUMPTION, default=default(CONF_CONSUMPTION)): _SENSOR,
        vol.Optional(CONF_PRODUCTION, default=default(CONF_PRODUCTION)): _SENSOR,
        vol.Optional(CONF_SOLAR, default=default(CONF_SOLAR)): _SENSOR,
        vol.Optional(CONF_GAS, default=default(CONF_GAS)): _SENSOR,
        vol.Optional(CONF_VOLTAGE, default=default(CONF_VOLTAGE)): _SENSOR,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=d.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ): _INTERVAL,
    }


async def _validate_token(hass, token: str) -> str | None:
    """None when the token is accepted, else an error key.

    Posts an empty payload: a valid token yields 400 (no readings), a bad one
    yields 401 — so we can check the credential without inserting fake data.
    """
    session = async_get_clientsession(hass)
    try:
        async with session.post(
            INGEST_URL,
            json={},
            headers={"Authorization": f"Bearer {token.strip()}"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 401:
                return "invalid_token"
            return None
    except (aiohttp.ClientError, TimeoutError):
        return "cannot_connect"


class FlowwaveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup: token + which sensors to send."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = str(user_input[CONF_TOKEN]).strip()
            err = await _validate_token(self.hass, token)
            if err:
                errors["base"] = err
            else:
                await self.async_set_unique_id(token)
                self._abort_if_unique_id_configured()
                user_input[CONF_TOKEN] = token
                return self.async_create_entry(title="Flowwave", data=user_input)

        schema = vol.Schema(
            {vol.Required(CONF_TOKEN): str, **_sensor_schema()}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return FlowwaveOptionsFlow(config_entry)


class FlowwaveOptionsFlow(OptionsFlow):
    """Change which sensors are sent, without re-entering the token."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = {**self._entry.data, **self._entry.options}
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(_sensor_schema(current))
        )
