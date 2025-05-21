"""Binary sensor entities for Kronoterm integration."""

from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.kronoterm_integration.mqtt_subscription import (
    AbstractMqttSubscriptionObserver,
    AbstractMqttSubscriptionSubject,
    MqttSubscriptionSubject,
)

from .const import DOMAIN
from .sensor_list import KronotermSensorListEntity
from .sensor_manager import SensorManager


async def async_setup_entry(
    hass: HomeAssistant,
    _entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Enter setup for binary sensors."""
    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.binary_sensors

    entities = []

    for sensor in sensor_defs:
        entity: KronotermBinarySensor = sensor["entity"]
        topic: str = sensor["topic"]

        subscription_subject = MqttSubscriptionSubject.get_instance(hass)
        await subscription_subject.async_attach(topic, entity)

        entities.append(entity)

    add_entities(entities)


class KronotermBinarySensor(BinarySensorEntity, AbstractMqttSubscriptionObserver):
    """Representation of a binary sensor."""

    def __init__(self, name: str, sensor_id: str) -> None:
        self._attr_name = name
        self.sensor_id = sensor_id
        super().__init__()

    @property
    def extra_state_attributes(self):
        return {"kronoterm": True}

    @property
    def unique_id(self):
        return f"kronoterm_{self.sensor_id}"

    def _msg_received(self, payload: str) -> None:
        """Receives message."""
        if payload == "ON":
            self.is_on = True
        elif payload == "OFF":
            self.is_on = False

    def notify_observer(
        self, _subject: AbstractMqttSubscriptionSubject, msg: mqtt.ReceiveMessage
    ) -> None:
        """Update from subject."""
        self._msg_received(str(msg.payload))
