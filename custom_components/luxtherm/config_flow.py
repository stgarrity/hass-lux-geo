"""Config flow for the Lux Thermostat integration."""

from __future__ import annotations

import logging
from typing import Any

from luxgeo.api import LuxAPI
from luxgeo.auth import login
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    tokens = await login(data[CONF_USERNAME], data[CONF_PASSWORD])
    if not tokens:
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect

    api = LuxAPI(data[CONF_USERNAME], data[CONF_PASSWORD], tokens)

    # FIXME refactor
    try:
        u = await api.get_user()
    except Exception as err:
        _LOGGER.error("Error getting user", extra={"error": err})
        raise CannotConnect("Error getting user") from err

    _LOGGER.info("Got user: %s", u)

    did = "luxtherm_0"
    n = "Unnamed Lux Geo"
    locations = u.get("location")
    if locations:
        devices = locations[0].get("devices")
        if devices:
            did = devices[0].get("id")
            n = devices[0].get("name")

    # Return info that you want to store in the config entry.
    return {
        "title": n,
        "device_id": did,
        CONF_USERNAME: data[CONF_USERNAME],
        CONF_PASSWORD: data[CONF_PASSWORD],
        "tokens": tokens,  # we include this here to save a re-auth on setup, but it's optional
    }


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for lux."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
