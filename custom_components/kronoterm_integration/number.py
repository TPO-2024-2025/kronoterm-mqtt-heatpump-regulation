"""Switch entities for Kronoterm integration."""

import logging

from homeassistant.components import mqtt
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    _entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Enter setup for numbers."""
    ksl = _hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.numbers

    entities = []

    for number in sensor_defs:
        entity: KronotermNumber = number["entity"]
        entity.hass = _hass
        _LOGGER.debug("Added number with topic %s", number["topic"])

        entities.append(entity)

    add_entities(entities)


class KronotermNumber(NumberEntity):
    """Representation of a number."""

    hass: HomeAssistant | None = None

    def __init__(
        self,
        name: str,
        topic: str,
        min_value: float = 0,
        max_value: float = 100.0,
        step: float = 0.5,
        native_unit_of_measurement: str = UnitOfTemperature.CELSIUS,
    ) -> None:
        """Create new switch with name and topic."""
        self._attr_native_value = min_value
        self._attr_name = name
        self._topic = topic

        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = native_unit_of_measurement

        super().__init__()

    @property
    def extra_state_attributes(self):
        return {"kronoterm": True}

    def set_native_value(self, value: float) -> None:
        """Set native value and publish on MQTT."""
        self._attr_native_value = value

        if self.hass is not None:
            mqtt.publish(self.hass, self._topic, str(self.native_value))

        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set native value and publish on MQTT."""
        self._attr_native_value = value

        if self.hass is not None:
            mqtt.publish(self.hass, self._topic, str(self.native_value))

        self.async_write_ha_state()
