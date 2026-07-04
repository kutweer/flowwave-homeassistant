"""Push Home Assistant meter readings to Flowwave.

This integration reads the entities you pick and POSTs them to flowwave.nl on
an interval — no rest_command, no automations.yaml, no YAML at all. Power
sensors are auto-converted to watts from their own unit_of_measurement, so a
kW inverter sensor and a W meter sensor both just work.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_CONSUMPTION,
    CONF_GAS,
    CONF_PRODUCTION,
    CONF_SCAN_INTERVAL,
    CONF_SOLAR,
    CONF_TOKEN,
    CONF_VOLTAGE,
    DEFAULT_SCAN_INTERVAL,
    INGEST_URL,
)

_LOGGER = logging.getLogger(__name__)
_UNAVAILABLE = ("unknown", "unavailable", "none", "")


def _to_watts(state: State | None) -> int | None:
    """A power sensor's value in watts, converted from its own unit."""
    if state is None or state.state in _UNAVAILABLE:
        return None
    try:
        value = float(state.state)
    except (ValueError, TypeError):
        return None
    unit = str(state.attributes.get("unit_of_measurement", "")).strip().lower()
    if unit == "kw":
        value *= 1000
    elif unit == "mw":
        value *= 1_000_000
    return round(value)


def _to_float(state: State | None) -> float | None:
    """A plain numeric state (gas m³, voltage V)."""
    if state is None or state.state in _UNAVAILABLE:
        return None
    try:
        return float(state.state)
    except (ValueError, TypeError):
        return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start pushing readings for a configured Flowwave device."""
    data = {**entry.data, **entry.options}
    token = data[CONF_TOKEN]
    interval = max(5, int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))
    session = async_get_clientsession(hass)

    async def _push(_now=None) -> None:
        payload: dict[str, float] = {}

        if entity := data.get(CONF_CONSUMPTION):
            if (v := _to_watts(hass.states.get(entity))) is not None:
                payload["import_w"] = v
        if entity := data.get(CONF_PRODUCTION):
            if (v := _to_watts(hass.states.get(entity))) is not None:
                payload["export_w"] = v
        if entity := data.get(CONF_SOLAR):
            if (v := _to_watts(hass.states.get(entity))) is not None:
                payload["solar_w"] = v
        if entity := data.get(CONF_GAS):
            if (v := _to_float(hass.states.get(entity))) is not None:
                payload["gas_m3"] = v
        if entity := data.get(CONF_VOLTAGE):
            if (v := _to_float(hass.states.get(entity))) is not None:
                payload["voltage"] = v

        if not payload:
            return

        try:
            async with session.post(
                INGEST_URL,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    _LOGGER.error(
                        "Flowwave rejected the device token — reconfigure the integration"
                    )
                elif resp.status not in (200, 201):
                    _LOGGER.warning("Flowwave push returned HTTP %s", resp.status)
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.debug("Flowwave push failed: %s", err)

    # push once now, then on the interval; reload when options change
    await _push()
    entry.async_on_unload(
        async_track_time_interval(hass, _push, timedelta(seconds=interval))
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload — the interval + listener are cancelled via async_on_unload."""
    return True
