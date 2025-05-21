"""Switch entities for Kronoterm integration."""

import logging

from homeassistant.components import mqtt
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    _entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Enter setup for switches."""
    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.switches

    entities = []

    for sensor in sensor_defs:
        entity: KronotermSwitch = sensor["entity"]
        entity.hass = hass
        _LOGGER.debug("Added switch with topic %s", sensor["topic"])

        entities.append(entity)

    add_entities(entities)


class KronotermSwitch(SwitchEntity):
    """Representation of a switch."""

    hass: HomeAssistant | None = None

    def __init__(self, name: str, topic: str) -> None:
        """Create new switch with name and topic."""
        self._attr_name = name
        self._topic = topic

        super().__init__()

    def _get_payload(self) -> str:
        """Construct payload string."""
        payload = ""

        if self.state is not None:
            payload = self.state.upper()
        else:
            _LOGGER.error("Unexpected state")

        return payload

    def _publish_state(self) -> None:
        """Publish state on MQTT."""
        payload = self._get_payload()

        if self.hass is not None:
            mqtt.publish(self.hass, self._topic, payload)

        self.async_write_ha_state()

    async def _async_publish_state(self) -> None:
        """Publish state on MQTT."""
        payload = self._get_payload()

        if self.hass is not None:
            await mqtt.async_publish(self.hass, self._topic, payload)

        self.async_write_ha_state()

    def turn_on(self) -> None:
        """Turn the switch on."""
        self._attr_is_on = True
        self._publish_state()

    async def async_turn_on(self) -> None:
        """Turn the switch on."""
        self._attr_is_on = True
        await self._async_publish_state()

    def turn_off(self) -> None:
        """Turn the switch off."""
        self._attr_is_on = False
        self._publish_state()

    async def async_turn_off(self) -> None:
        """Turn the switch off."""
        self._attr_is_on = False
        await self._async_publish_state()
