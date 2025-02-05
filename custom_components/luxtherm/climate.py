"""Climate entity for LuxTherm device."""

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LuxThermConfigEntry
from .coordinator import LuxThermCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LuxThermConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up lux from a config entry."""

    coordinator = LuxThermCoordinator(hass, entry.runtime_data)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([LuxThermClimate(coordinator, entry)])

    return True


class LuxThermClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for LuxTherm device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LuxThermCoordinator, entry: LuxThermConfigEntry
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, context=entry)
        self._is_on = False

        self.api = entry.runtime_data

        self._attr_unique_id = entry.data.get("device_id")
        self._attr_name = entry.data.get("name")

        self._device_id = entry.data.get("device_id")
        self._device_name = entry.data.get("name")
        self._hvac_mode = 0
        self._target_temperature = 55
        self._current_temperature = 55

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._device_id = self.coordinator.data["id"]
        self._device_name = self.coordinator.data["name"]
        self._attr_name = self._device_name
        self._hvac_mode = self.coordinator.data["hvac_mode"]
        self._target_temperature = self.coordinator.data["target_temperature"]
        self._current_temperature = self.coordinator.data["current_temperature"]

        _LOGGER.info(
            "Coordinator update %s: mode %s target %s",
            self._device_id,
            self._hvac_mode,
            self._target_temperature,
        )

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Set the initial state."""

        _LOGGER.warning("Adding to hass")

        await super().async_added_to_hass()

        # FIXME refactor to be shared?
        d = await self.api.get_device_state(self._device_id)

        self._hvac_mode = d.get("systemmode")
        self._target_temperature = d.get("holdheat")
        self._current_temperature = d.get("currenttemp")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        s = await self.api.get_device_state(self._device_id)
        if hvac_mode == HVACMode.HEAT:
            hvm = 1
        else:
            hvm = 0

        s["systemmode"] = hvm

        res = await self.api.set_device_state(self._device_id, s)
        _LOGGER.info("Set mode %s: %s", hvm, res)

        self._hvac_mode = hvm
        self._target_temperature = res.get("holdheat")

        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)

        s = await self.api.get_device_state(self._device_id)

        s["holdheat"] = temp

        res = await self.api.set_device_state(self._device_id, s)
        _LOGGER.info("Set temperature %s: %s", temp, res)

        self._target_temperature = temp

        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        self.set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        self.set_hvac_mode(HVACMode.OFF)

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.FAHRENHEIT

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current hvac mode."""
        if self._hvac_mode == 1:
            return HVACMode.HEAT

        return HVACMode.OFF

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac modes."""
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self._target_temperature

    @property
    def target_temperature_step(self) -> float:
        """Return the target temperature step."""
        return 1.0

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current_temperature

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device_name

    @property
    def supported_features(self) -> int:
        """Return the supported features."""

        # reference https://developers.home-assistant.io/docs/core/entity/climate/#supported-features

        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
