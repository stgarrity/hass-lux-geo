"""The Lux Thermostat integration."""

from __future__ import annotations

import logging

from luxgeo.api import LuxAPI
from luxgeo.auth import login

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

_PLATFORMS: list[Platform] = [Platform.CLIMATE]

type LuxThermConfigEntry = ConfigEntry[LuxAPI]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: LuxThermConfigEntry) -> bool:
    """Set up lux from a config entry."""

    # lazy login if we just did it and already have tokens
    tokens = entry.data["tokens"]
    api = LuxAPI(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], tokens)

    entry.runtime_data = api

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: LuxThermConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
