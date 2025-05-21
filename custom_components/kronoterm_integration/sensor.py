"""Platform-specific sensor entities."""

from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.kronoterm_integration.mqtt_subscription import (
    AbstractMqttSubscriptionObserver,
    AbstractMqttSubscriptionSubject,
    MqttSubscriptionSubject,
)

from .const import DOMAIN
from .sensor_list import KronotermSensorListEntity
from .sensor_manager import SensorManager
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, _entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    """Enter setup for number and enum sensors sensors."""

    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.enum_sensors + ksl.number_sensors

    list_entity = hass.data[DOMAIN]["kronoterm_list_entity"]

    entities = []

    for sensor in sensor_defs:
        entity: KronotermEnumSensor | KronotermNumberSensor = sensor["entity"]
        topic: str = sensor["topic"]

        subscription_subject = MqttSubscriptionSubject.get_instance(hass)
        await subscription_subject.async_attach(topic, entity)

        entities.append(entity)

    entities.append(list_entity)

    add_entities(entities)


class KronotermEnumSensor(SensorEntity, AbstractMqttSubscriptionObserver):
    """Entity for sensors which have a limited set of possible values."""

    def __init__(self, name: str, options: list[str], sensor_id: str) -> None:
        """Create entity with name and valid states."""
        self._attr_name = name
        self._sensor_type = "enum"
        self.sensor_id = sensor_id
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = options
        self._attr_native_value = None
        super().__init__()

    @property
    def extra_state_attributes(self):
        return {"sensor_type": self._sensor_type, "kronoterm": True}

    @property
    def unique_id(self):
        return f"kronoterm_{self.sensor_id}"

    def _msg_received(self, payload: str) -> None:
        """Receives message."""
        if payload in self._attr_options:
            self._attr_native_value = payload
            self.async_write_ha_state()
            if "Error register" in self._attr_name and payload not in "No error":
                _LOGGER.critical("ERROR: %s with error %s", self._attr_name, payload)

    def notify_observer(
        self, _subject: AbstractMqttSubscriptionSubject, msg: mqtt.ReceiveMessage
    ) -> None:
        """Update from subject."""
        self._msg_received(str(msg.payload))


class KronotermNumberSensor(SensorEntity, AbstractMqttSubscriptionObserver):
    """Entity for sensors which have a numerical value."""

    def __init__(
        self, name: str, min_value: float, max_value: float, unit: str, sensor_id: str
    ) -> None:
        """Create entity with name, minimum name and maximum value."""
        self._attr_name = name
        self._sensor_type = "number"
        self.sensor_id = (sensor_id,)
        self._attr_native_value = 0.0
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 0.1
        self._unit = unit
        super().__init__()

    @property
    def extra_state_attributes(self):
        return {
            "sensor_type": self._sensor_type,
            "unit_of_measurement": self._unit,
            "kronoterm": True,
        }

    @property
    def unique_id(self):
        return f"kronoterm_{self.sensor_id}"

    def _msg_received(self, payload: str) -> None:
        """Receives message."""
        try:
            value = float(payload)
            if self._attr_native_min_value <= value <= self._attr_native_max_value:
                self._attr_native_value = value
                self.async_write_ha_state()
        except ValueError:
            pass

    def notify_observer(
        self, _subject: AbstractMqttSubscriptionSubject, msg: mqtt.ReceiveMessage
    ) -> None:
        """Update from subject."""
        self._msg_received(str(msg.payload))
