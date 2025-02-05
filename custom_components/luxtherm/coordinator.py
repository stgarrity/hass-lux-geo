"""Coordinator for LuxTherm device."""

import asyncio
from datetime import timedelta
import logging

from luxgeo.api import LuxAPI

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LuxThermCoordinator(DataUpdateCoordinator):
    """Data update coordinator for LuxTherm."""

    def __init__(self, hass: HomeAssistant, api: LuxAPI) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            always_update=True,  # FIXME test
        )
        self._api = api
        self._device_id = ""

    async def _async_setup(self) -> None:
        """Set up the coordinator.

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """

        try:
            u = await self._api.get_user()
        except Exception as err:
            _LOGGER.error("Error getting user", extra={"error": err})
            raise ConfigEntryError("Error getting user") from err

        locations = u.get("location")
        if not locations:
            _LOGGER.error("No locations found in Lux Geo API: %s", u)
            raise ConfigEntryError("No locations found in Lux Geo API")

        devices = locations[0].get("devices")
        if not devices:
            _LOGGER.error("No devices found in Lux Geo API")
            raise ConfigEntryError("No devices found in Lux Geo API")

        did = devices[0].get("id")
        if not did:
            _LOGGER.error("No device ID found in Lux Geo API")
            raise ConfigEntryError("No device ID found in Lux Geo API")

        self._device_id = did

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        _LOGGER.info("Updating data")

        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(10):
                device_state = await self._api.get_device_state(self._device_id)

                # I see how they got here on API semantics but ugh.
                # dt = (
                #     device_state.get("desiredtemp")
                #     if device_state.get("desirredtemp") != -1
                #     else device_state.get("currenttemp")
                # )

                data = {
                    "id": self._device_id,
                    "name": device_state.get("name"),
                    "hvac_mode": device_state.get("systemmode"),
                    "target_temperature": device_state.get("holdheat"),
                    "current_temperature": device_state.get("currenttemp"),
                }

                _LOGGER.info("Got data: %s", data)

                return data

        except Exception as err:
            _LOGGER.error("Error communicating with API", extra={"error": err})
            raise UpdateFailed(f"Error communicating with API: {err}") from err
